# StoryChat

Interactive character-based storytelling using Ollama Context Engine

## Overview

StoryChat is an interactive storytelling application that allows you to create immersive narrative experiences with dynamic characters. Built on the Ollama Context Engine, it combines Retrieval-Augmented Generation (RAG) and Context-Augmented Generation (CAG) to create responsive, contextually-aware character interactions.

## Features

- Create rich story backgrounds that inform character knowledge
- Define characters with unique personalities, speaking styles, and backstories
- Switch between characters during your storytelling session
- Add new context as your story progresses
- Automatic state saving and session resumption

## Special Commands

- `/createbackground <description>` - Create the story world background
- `/createcharacter name="Name" role="Role" ...` - Create a new character
- `/talkto <character>` - Switch to talking with a specific character
- `/addcontext <description>` - Add new information to the story context
- `/characters` - List all available characters
- `/save [filename]` - Save the current session state to a JSON file (defaults to storychat_state.json)
- `/load [filename]` - Load a previously saved session state (defaults to storychat_state.json)
- `/groupchat <character1> <character2> ...` - Start a conversation between multiple characters
- `/help` - Show help information
- `/exit` - Exit StoryChat (saves state automatically)

## Installation

1. Ensure [Ollama](https://ollama.ai/) is installed and running on your system
2. Clone this repository
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install the required Ollama models:

```bash
ollama pull nomic-embed-text:latest
ollama pull llama3.2:latest
```

## Usage

### Basic Usage

```bash
python run_storychat.py
```

### Demo Mode

To try StoryChat with pre-populated content:

```bash
python run_storychat.py --demo
```

## Creating Characters

Use the `/createcharacter` command with the following parameters:

```
/createcharacter name="Character Name" role="Character Role" appearance="Physical description" personality="Character traits" speech_style="How they talk" background="Character history" goals="What they want" secrets="What they hide"
```

Required parameters:
- `name`
- `role`
- `personality`
- `speech_style`

Optional parameters (defaults provided if omitted):
- `appearance`
- `background`
- `goals`
- `secrets`

## Example Session

```
> /createbackground The kingdom of Azoria is a land of high magic where technology and spells coexist.

> /createcharacter name="Elara" role="Court Mage" personality="Brilliant but eccentric" speech_style="Technical and precise"

> /talkto Elara

Elara> Tell me about the magical defenses of the castle

Elara> What do you know about the recent magical anomalies?
```

## Requirements

- Python 3.8+
- Ollama
- Required Python packages (see requirements.txt)

## Advanced Configuration

You can specify a custom database path:

```bash
python run_storychat.py --db custom_db_path
```

## Project Structure

- `storychat.py` - Main StoryChat implementation
- `run_storychat.py` - Command-line interface and demo content
- `storychat_state.json` - Saved session state (auto-generated)
- `storychat_db/` - Vector database for story context (auto-generated)

## License

MIT