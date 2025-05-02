#!/usr/bin/env python3
"""
Example usage of StoryChat - Interactive character-based storytelling
"""

from storychat import StoryChat
import sys
import argparse

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run StoryChat')
    parser.add_argument('--demo', action='store_true', help='Run with demo content')
    parser.add_argument('--db', default='storychat_db', help='Database path')
    return parser.parse_args()

def create_demo_content(chat):
    """Create demo content if requested."""
    # Create a fantasy background
    fantasy_background = """
    The land of Eldoria is a realm of magic and mystery, where towering mountains 
    meet enchanted forests. For centuries, the five kingdoms—Solaris, Lunaria, 
    Terravia, Aquamar, and Ignitia—have maintained a fragile peace.
    
    Recently, strange magical anomalies have begun appearing across the land. 
    Ancient artifacts are awakening, and creatures long thought to be myths 
    have been sighted near remote villages.
    
    The Council of Sages believes these events are connected to an ancient prophecy 
    about the return of the Shadow Lord, a powerful entity sealed away 1000 years ago.
    
    The capital city of Crystallis serves as a neutral meeting ground for representatives 
    of all kingdoms. Its grand library holds centuries of knowledge, and the magical 
    academy trains the most promising young spellcasters.
    """
    chat.create_background(fantasy_background)
    
    # Create demo characters
    
    # Wise Wizard
    chat.create_character({
        "name": "Thaddeus",
        "role": "Archmage of the Crystal Academy",
        "appearance": "Elderly man with flowing silver beard, wearing midnight blue robes embroidered with silver stars",
        "personality": "Wise, patient, but concerned about the growing magical disturbances",
        "speech_style": "Formal, scholarly, often uses arcane terminology",
        "background": "Studied magic for over 70 years, served three generations of rulers",
        "goals": "Discover the source of the magical anomalies",
        "secrets": "Encountered the Shadow Lord in his youth and barely survived"
    })
    
    # Knight Character
    chat.create_character({
        "name": "Lyra",
        "role": "Captain of the Royal Guard",
        "appearance": "Athletic woman with short auburn hair, wearing polished armor with gold trim",
        "personality": "Honorable, direct, disciplined, with a dry sense of humor",
        "speech_style": "Concise, uses military terms, speaks with authority",
        "background": "Daughter of a blacksmith, rose through the ranks through skill and determination",
        "goals": "Protect the kingdom from threats both magical and mundane",
        "secrets": "Can see magical auras, a rare ability she keeps hidden"
    })
    
    # Mysterious Merchant
    chat.create_character({
        "name": "Nyx",
        "role": "Traveling Merchant",
        "appearance": "Slender figure in colorful silks with a hooded cloak, face partially obscured",
        "personality": "Charismatic, enigmatic, knows more than they reveal",
        "speech_style": "Smooth, sometimes poetic, sprinkles in words from foreign languages",
        "background": "Claims to have traveled to lands beyond the maps",
        "goals": "Collect rare magical artifacts",
        "secrets": "Actually a spy for a secret organization studying the magical anomalies"
    })
    
    # Add additional context
    recent_event = """
    Three days ago, a meteor of pure crystal crashed into the western forest.
    Locals report strange lights and sounds emanating from the crash site.
    Animals have been behaving strangely, and several villagers claim to have seen
    shadowy figures moving through the trees at night.
    """
    chat.add_context(recent_event)
    
    # Set active character
    chat.talk_to("Thaddeus")
    
    print("\n[Demo content created. Try asking Thaddeus about the magical anomalies!]")

def main():
    """Main entry point for the application."""
    args = parse_arguments()
    
    # Create StoryChat instance
    chat = StoryChat(db_path=args.db)
    
    # Create demo content if requested
    if args.demo:
        create_demo_content(chat)
    
    # Run the chat interface
    chat.run()

if __name__ == "__main__":
    main()
