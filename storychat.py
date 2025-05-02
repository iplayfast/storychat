"""
StoryChat - Interactive character-based storytelling using Ollama Context Engine

This module implements a chat interface for interactive storytelling with
dynamic character switching and context management.
"""

from ollama_context import ContextEngine
from typing import Dict, List, Optional, Any, Set
import logging
import os
import json
import readline  # For command history in CLI
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import re
import random
from datetime import datetime

class CharacterResponse(BaseModel):
    """Structured output for character responses."""
    dialogue: str
    emotion: str
    thoughts: str

class GroupChatResponse(BaseModel):
    """Structured output for group chat responses."""
    character: str
    dialogue: str
    emotion: str
    reaction_to: str
    
class StoryChat:
    """Main class for managing the storytelling chat experience."""
    
    def __init__(self, db_path: str = "storychat_db"):
        """Initialize the StoryChat system."""
        # Set up the Context Engine
        self.engine = ContextEngine(
            mode="combined",
            log_level=logging.INFO,
            database=db_path
        )
        
        self.console = Console()
        self.active_character = None
        self.characters = {}
        self.background_created = False
        
        # Ensure database directory exists
        os.makedirs(db_path, exist_ok=True)
        
        # Try to load previous state
        self._load_state()
        
        self.console.print(Panel.fit(
            "Welcome to StoryChat! Type /help for available commands.", 
            title="StoryChat"
        ))
    
    def _load_state(self, filename: str = "storychat_state.json"):
        """Load previous session state if it exists."""
        try:
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    state = json.load(f)
                
                # Clear existing characters
                self.characters = {}
                
                # Load characters
                for char_name, char_data in state.get("characters", {}).items():
                    self.engine.register_context(
                        char_name,
                        char_data["template"],
                        char_data["variables"]
                    )
                    self.characters[char_name] = char_data
                
                # Set active character
                self.active_character = state.get("active_character")
                self.background_created = state.get("background_created", False)
                
                if self.active_character:
                    self.console.print(f"Resumed session with active character: [bold]{self.active_character}[/bold]")
                
                self.console.print(f"[green]Session state loaded from {filename}[/green]")
                return True
            else:
                self.console.print(f"[yellow]State file {filename} not found[/yellow]")
                return False
        except Exception as e:
            self.console.print(f"[bold red]Error loading state from {filename}:[/bold red] {str(e)}")
            return False
    
    def _save_state(self, filename: str = "storychat_state.json"):
        """Save current session state."""
        state = {
            "characters": self.characters,
            "active_character": self.active_character,
            "background_created": self.background_created
        }
        
        with open(filename, "w") as f:
            json.dump(state, f, indent=2)
        
        self.console.print(f"[green]Session state saved to {filename}[/green]")
    
    def create_background(self, background_description: str):
        """Create the story world background."""
        # Save background to file
        with open("story_background.txt", "w") as f:
            f.write(background_description)
        
        # Index background for retrieval
        self.engine.load_and_index_documents(
            "story_background.txt",
            metadatas=[{"type": "background"}]
        )
        
        self.background_created = True
        self._save_state()
        
        self.console.print(Panel(
            Markdown("*Background created and indexed for retrieval*"),
            title="Story Background Created",
            border_style="green"
        ))
    
    def create_character(self, character_data: Dict[str, Any]):
        """Create a new character."""
        name = character_data.get("name")
        if not name:
            self.console.print("[bold red]Error:[/bold red] Character must have a name")
            return
        
        # Create character template
        character_template = """
        Character Name: {name}
        Role: {role}
        Appearance: {appearance}
        Personality: {personality}
        Speech Style: {speech_style}
        Background: {background}
        Goals: {goals}
        Secrets: {secrets}
        """
        
        # Register the character context
        try:
            self.engine.register_context(name, character_template, character_data)
            self.characters[name] = {
                "template": character_template,
                "variables": character_data
            }
            
            # Switch to the new character if none active
            if not self.active_character:
                self.active_character = name
            
            self._save_state()
            
            self.console.print(Panel(
                f"Created character: [bold]{name}[/bold]\n"
                f"Role: {character_data.get('role', 'Unknown')}\n"
                f"Personality: {character_data.get('personality', 'Unknown')}",
                title="Character Created",
                border_style="green"
            ))
        except Exception as e:
            self.console.print(f"[bold red]Error creating character:[/bold red] {str(e)}")
    
    def talk_to(self, character_name: str):
        """Switch the active character."""
        if character_name not in self.characters:
            self.console.print(f"[bold red]Error:[/bold red] Character '{character_name}' not found")
            return
        
        self.active_character = character_name
        self._save_state()
        
        self.console.print(Panel(
            f"Now talking to [bold]{character_name}[/bold]",
            border_style="blue"
        ))
    
    def add_context(self, context_text: str):
        """Add new context to the story."""
        # Save context to file with timestamp
        context_filename = f"context_{len(os.listdir()) + 1}.txt"
        with open(context_filename, "w") as f:
            f.write(context_text)
        
        # Index context for retrieval
        self.engine.load_and_index_documents(
            context_filename,
            metadatas=[{"type": "context"}]
        )
        
        self._save_state()
        
        self.console.print(Panel(
            Markdown("*New context added and indexed for retrieval*"),
            title="Context Added",
            border_style="green"
        ))
    
    def chat(self, message: str):
        """Process chat messages and commands."""
        # Handle commands
        if message.startswith('/'):
            self._handle_command(message)
            return
        
        # Regular chat - talk to active character
        if not self.active_character:
            self.console.print("[bold yellow]Warning:[/bold yellow] No active character. Use /talkto {character} to select one.")
            return
        
        try:
            # Check if we have background context indexed
            has_background = False
            try:
                db_status = self.engine.check_database_status()
                has_background = db_status.get('status') == 'populated' and db_status.get('num_documents', 0) > 0
            except Exception:
                pass
            
            # If we have background context, use combined mode, otherwise just use context mode
            mode = "combined" if has_background else "context"
            where_clause = {"type": {"$in": ["background", "context"]}} if has_background else None
            
            # Get structured response from character
            response = self.engine.query_structured(
                prompt=message,
                response_model=CharacterResponse,
                context_name=self.active_character,
                where=where_clause,
                system_prompt=f"You are {self.active_character}. Respond in character with dialogue, emotion, and inner thoughts.",
                mode=mode
            )
            
            # Display character response
            char_name = self.active_character
            self.console.print(Panel(
                f"{response.dialogue}\n\n"
                f"[italic dim]{response.emotion} (thinking: {response.thoughts})[/italic dim]",
                title=f"{char_name}",
                border_style="cyan"
            ))
            
        except Exception as e:
            self.console.print(f"[bold red]Error generating response:[/bold red] {str(e)}")
            # Try simpler query without structured output as fallback
            try:
                simple_response = self.engine.query(
                    prompt=message,
                    context_name=self.active_character,
                    system_prompt=f"You are {self.active_character}. Respond in character.",
                    mode="context"  # Force context-only mode for fallback
                )
                
                dialogue = simple_response.get('result', '')
                if dialogue:
                    self.console.print(Panel(
                        f"{dialogue}",
                        title=f"{self.active_character}",
                        border_style="yellow"
                    ))
            except Exception as inner_e:
                self.console.print(f"[bold red]Fallback also failed:[/bold red] {str(inner_e)}")
    
    def _handle_command(self, command: str):
        """Process special commands."""
        # Extract command and arguments
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == '/help':
            self._show_help()
        
        elif cmd == '/createbackground':
            if not args:
                self.console.print("[bold yellow]Usage:[/bold yellow] /createbackground <description>")
                return
            self.create_background(args)
        
        elif cmd == '/createcharacter':
            try:
                # Parse character data from command
                char_data = self._parse_character_input(args)
                self.create_character(char_data)
            except Exception as e:
                self.console.print(f"[bold red]Error:[/bold red] {str(e)}")
                self.console.print("[bold yellow]Usage:[/bold yellow] /createcharacter name=Name role=Role personality=Personality ...")
        
        elif cmd == '/talkto':
            if not args:
                self.console.print("[bold yellow]Usage:[/bold yellow] /talkto <character>")
                return
            self.talk_to(args)
        
        elif cmd == '/addcontext':
            if not args:
                self.console.print("[bold yellow]Usage:[/bold yellow] /addcontext <description>")
                return
            self.add_context(args)
        
        elif cmd == '/characters':
            self._list_characters()
            
        elif cmd == '/save':
            # Use default name if none provided
            filename = args if args else "storychat_state.json"
            # Add .json extension if not present
            if not filename.endswith('.json'):
                filename += '.json'
            self._save_state(filename)
            
        elif cmd == '/load':
            # Use default name if none provided
            filename = args if args else "storychat_state.json"
            # Add .json extension if not present
            if not filename.endswith('.json'):
                filename += '.json'
            self._load_state(filename)
            
        elif cmd == '/groupchat':
            if not args:
                self.console.print("[bold yellow]Usage:[/bold yellow] /groupchat <character1> <character2> ...")
                return
            character_names = args.split()
            self._start_group_chat(character_names)
        
        elif cmd == '/exit':
            self._save_state()
            self.console.print("Goodbye! Session state saved.")
            exit(0)
        
        else:
            self.console.print(f"[bold red]Unknown command:[/bold red] {cmd}")
            self._show_help()
    
    def _parse_character_input(self, input_str: str) -> Dict[str, str]:
        """Parse character creation input into a dictionary."""
        # For simplicity, we'll use a basic key=value parsing
        char_data = {}
        
        # Simple parser for key=value pairs
        pattern = r'(\w+)=(?:"([^"]+)"|([^ ]+))'
        matches = re.findall(pattern, input_str)
        
        for match in matches:
            key = match[0]
            # Use the quoted value if present, otherwise use the unquoted value
            value = match[1] if match[1] else match[2]
            char_data[key] = value
        
        # Validate required fields
        required_fields = ["name", "role", "personality", "speech_style"]
        missing_fields = [field for field in required_fields if field not in char_data]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Add default values for optional fields
        if "appearance" not in char_data:
            char_data["appearance"] = "Not specified"
        if "background" not in char_data:
            char_data["background"] = "Not specified"
        if "goals" not in char_data:
            char_data["goals"] = "Not specified"
        if "secrets" not in char_data:
            char_data["secrets"] = "Not specified"
        
        return char_data
    
    def _list_characters(self):
        """List all created characters."""
        if not self.characters:
            self.console.print("No characters created yet.")
            return
        
        self.console.print(Panel(
            "\n".join([
                f"{'➤ ' if name == self.active_character else '  '}"
                f"[bold]{name}[/bold] - {char['variables'].get('role', 'Unknown')}"
                for name, char in self.characters.items()
            ]),
            title="Characters",
            border_style="blue"
        ))
    
    def _show_help(self):
        """Show help information."""
        help_text = """
        ## Available Commands
        
        * `/createbackground <description>` - Create story world background
        * `/createcharacter name="Name" role="Role" ...` - Create a new character
        * `/talkto <character>` - Switch active character
        * `/addcontext <description>` - Add new story context
        * `/characters` - List all characters
        * `/save [filename]` - Save session state (defaults to storychat_state.json)
        * `/load [filename]` - Load session state (defaults to storychat_state.json)
        * `/groupchat <character1> <character2> ...` - Start a conversation between characters
        * `/help` - Show this help message
        * `/exit` - Exit StoryChat
        
        Type regular messages to talk to the active character.
        """
        
        self.console.print(Panel(
            Markdown(help_text),
            title="StoryChat Help",
            border_style="green"
        ))

    def _start_group_chat(self, character_names: List[str]):
        """Start a conversation between multiple characters."""
        # Validate characters exist
        invalid_chars = [name for name in character_names if name not in self.characters]
        if invalid_chars:
            self.console.print(f"[bold red]Error:[/bold red] Unknown characters: {', '.join(invalid_chars)}")
            return
            
        if len(character_names) < 2:
            self.console.print("[bold yellow]Group chat requires at least 2 characters[/bold yellow]")
            return
            
        # Start group chat
        self.console.print(Panel(
            f"Starting group chat with characters: [bold]{', '.join(character_names)}[/bold]\n"
            f"Enter a topic or question to discuss, or type '/end' to end the group chat",
            title="Group Chat",
            border_style="magenta"
        ))
        
        # Get topic from user
        topic = input("Topic> ")
        if not topic or topic.strip() == "/end":
            return
            
        self.console.print(Panel(
            f"[italic]Characters discussing: {topic}[/italic]",
            border_style="blue"
        ))
        
        # Check if we have background context indexed
        has_background = False
        try:
            db_status = self.engine.check_database_status()
            has_background = db_status.get('status') == 'populated' and db_status.get('num_documents', 0) > 0
        except Exception:
            pass
        
        # Track which characters have spoken
        remaining_speakers = set(character_names)
        already_spoken = set()
        previous_speaker = None
        previous_dialogue = ""
        
        # Run the conversation for a few turns
        for _ in range(len(character_names) * 2):
            # If everyone has spoken once, reset
            if not remaining_speakers:
                remaining_speakers = set(character_names) - {previous_speaker}
                already_spoken = {previous_speaker}
            
            # Choose next speaker (not the previous one)
            if previous_speaker in remaining_speakers:
                remaining_speakers.remove(previous_speaker)
            
            # If somehow we run out of speakers, reset
            if not remaining_speakers:
                remaining_speakers = set(character_names) - {previous_speaker}
            
            next_speaker = random.choice(list(remaining_speakers))
            remaining_speakers.remove(next_speaker)
            already_spoken.add(next_speaker)
            
            # Generate response
            try:
                system_prompt = (
                    f"You are {next_speaker}. You are speaking in a group conversation "
                    f"about '{topic}'. " +
                    (f"{previous_speaker} just said: '{previous_dialogue}'. " if previous_speaker else "") +
                    f"Respond in character with dialogue, emotion, and who you're responding to."
                )
                
                # If we have background context, use combined mode, otherwise just use context mode
                mode = "combined" if has_background else "context"
                where_clause = {"type": {"$in": ["background", "context"]}} if has_background else None
                
                response = self.engine.query_structured(
                    prompt=topic if not previous_speaker else f"Respond to {previous_speaker}'s comment",
                    response_model=GroupChatResponse,
                    context_name=next_speaker,
                    where=where_clause,
                    system_prompt=system_prompt,
                    mode=mode
                )
                
                # Display character response
                self.console.print(Panel(
                    f"{response.dialogue}\n\n"
                    f"[italic dim]{response.emotion}[/italic dim]",
                    title=f"{next_speaker}" + (f" (responding to {response.reaction_to})" if response.reaction_to else ""),
                    border_style="cyan"
                ))
                
                # Update for next iteration
                previous_speaker = next_speaker
                previous_dialogue = response.dialogue
                
            except Exception as e:
                self.console.print(f"[bold red]Error generating response for {next_speaker}:[/bold red] {str(e)}")
                # Try simpler query without structured output as fallback
                try:
                    simple_response = self.engine.query(
                        prompt=topic if not previous_speaker else f"Respond to {previous_speaker}'s comment about {topic}",
                        context_name=next_speaker,
                        system_prompt=system_prompt,
                        mode="context"  # Force context-only mode for fallback
                    )
                    
                    dialogue = simple_response.get('result', '')
                    if dialogue:
                        self.console.print(Panel(
                            f"{dialogue}",
                            title=f"{next_speaker}" + (f" (responding to {previous_speaker})" if previous_speaker else ""),
                            border_style="yellow"
                        ))
                        
                        # Update for next iteration
                        previous_speaker = next_speaker
                        previous_dialogue = dialogue
                except Exception as inner_e:
                    self.console.print(f"[bold red]Fallback also failed:[/bold red] {str(inner_e)}")
        
        self.console.print(Panel(
            "[italic]Group discussion ended[/italic]",
            border_style="blue"
        ))
        
    def run_demo_groupchat(self):
        """Run a demonstration group chat with available characters."""
        available_chars = list(self.characters.keys())
        if len(available_chars) < 2:
            self.console.print("[yellow]Not enough characters for a group chat demo[/yellow]")
            return
            
        # Take up to 3 characters
        chat_chars = available_chars[:min(3, len(available_chars))]
        
        # Start a demo group chat
        self.console.print(Panel(
            f"Starting demo group chat with characters: [bold]{', '.join(chat_chars)}[/bold]",
            title="Demo Group Chat",
            border_style="magenta"
        ))
        
        demo_topic = "the recent magical disturbances and what they might mean for the kingdom"
        
        self.console.print(Panel(
            f"[italic]Characters discussing: {demo_topic}[/italic]",
            border_style="blue"
        ))
        
        # Check if we have background context indexed
        has_background = False
        try:
            db_status = self.engine.check_database_status()
            has_background = db_status.get('status') == 'populated' and db_status.get('num_documents', 0) > 0
        except Exception:
            pass
        
        # Track which characters have spoken
        remaining_speakers = set(chat_chars)
        already_spoken = set()
        previous_speaker = None
        previous_dialogue = ""
        
        # Run the conversation for a few turns
        for _ in range(len(chat_chars) * 2):
            # If everyone has spoken once, reset
            if not remaining_speakers:
                remaining_speakers = set(chat_chars) - {previous_speaker}
                already_spoken = {previous_speaker}
            
            # Choose next speaker (not the previous one)
            if previous_speaker in remaining_speakers:
                remaining_speakers.remove(previous_speaker)
            
            # If somehow we run out of speakers, reset
            if not remaining_speakers:
                remaining_speakers = set(chat_chars) - {previous_speaker}
            
            next_speaker = random.choice(list(remaining_speakers))
            remaining_speakers.remove(next_speaker)
            already_spoken.add(next_speaker)
            
            # Generate response
            try:
                system_prompt = (
                    f"You are {next_speaker}. You are speaking in a group conversation "
                    f"about '{demo_topic}'. " +
                    (f"{previous_speaker} just said: '{previous_dialogue}'. " if previous_speaker else "") +
                    f"Respond in character with dialogue, emotion, and who you're responding to."
                )
                
                # If we have background context, use combined mode, otherwise just use context mode
                mode = "combined" if has_background else "context"
                where_clause = {"type": {"$in": ["background", "context"]}} if has_background else None
                
                response = self.engine.query_structured(
                    prompt=demo_topic if not previous_speaker else f"Respond to {previous_speaker}'s comment",
                    response_model=GroupChatResponse,
                    context_name=next_speaker,
                    where=where_clause,
                    system_prompt=system_prompt,
                    mode=mode
                )
                
                # Display character response
                self.console.print(Panel(
                    f"{response.dialogue}\n\n"
                    f"[italic dim]{response.emotion}[/italic dim]",
                    title=f"{next_speaker}" + (f" (responding to {response.reaction_to})" if response.reaction_to else ""),
                    border_style="cyan"
                ))
                
                # Update for next iteration
                previous_speaker = next_speaker
                previous_dialogue = response.dialogue
                
            except Exception as e:
                self.console.print(f"[bold red]Error generating response for {next_speaker}:[/bold red] {str(e)}")
                # Try simpler query without structured output as fallback
                try:
                    simple_response = self.engine.query(
                        prompt=demo_topic if not previous_speaker else f"Respond to {previous_speaker}'s comment about {demo_topic}",
                        context_name=next_speaker,
                        system_prompt=system_prompt,
                        mode="context"  # Force context-only mode for fallback
                    )
                    
                    dialogue = simple_response.get('result', '')
                    if dialogue:
                        self.console.print(Panel(
                            f"{dialogue}",
                            title=f"{next_speaker}" + (f" (responding to {previous_speaker})" if previous_speaker else ""),
                            border_style="yellow"
                        ))
                        
                        # Update for next iteration
                        previous_speaker = next_speaker
                        previous_dialogue = dialogue
                except Exception as inner_e:
                    self.console.print(f"[bold red]Fallback also failed:[/bold red] {str(inner_e)}")
        
        self.console.print(Panel(
            "[italic]Group discussion ended[/italic]\n"
            "You can start your own group chats using the '/groupchat' command!",
            border_style="blue"
        ))
    
    def run(self):
        """Run the interactive chat loop."""
        try:
            while True:
                # Show prompt based on active character
                prompt = f"{self.active_character}> " if self.active_character else "> "
                message = input(prompt)
                
                if message.strip():
                    self.chat(message)
        except KeyboardInterrupt:
            self._save_state()
            self.console.print("\nGoodbye! Session state saved.")
        except Exception as e:
            self.console.print(f"[bold red]Error:[/bold red] {str(e)}")
            self._save_state()
            raise

if __name__ == "__main__":
    chat = StoryChat()
    chat.run()