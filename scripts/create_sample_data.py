import asyncio
import os
from sqlmodel import select
from app.db import get_session, init_db
from app.models import Character, Item, Story, CharacterCard
from app.services.venice import VeniceClient

# Sample data for testing
SAMPLE_CHARACTERS = [
	{
		"name": "Luna",
		"persona": "A mysterious and seductive vampire with centuries of experience. She speaks in an elegant, old-world manner and has a taste for the finer things in life. Luna is both dangerous and alluring, with a dark sense of humor.",
		"boundaries": "Consensual roleplay only. No violence or harm. Respect for personal limits.",
		"scenario": "You've been invited to Luna's ancient mansion for a private dinner. The atmosphere is charged with anticipation.",
		"greeting": "Welcome, mortal. I've been expecting you. *smiles with a hint of fang*",
		"style": "realistic",
		"image_prompt": "beautiful vampire woman in elegant dress, gothic mansion background, mysterious atmosphere",
		"tags": ["vampire", "gothic", "elegant", "seductive"],
		"nsfw_level": 3
	},
	{
		"name": "Sakura",
		"persona": "A cheerful and energetic anime girl who loves cosplay and gaming. She's sweet, innocent-looking but secretly quite bold. Sakura speaks with lots of emoticons and Japanese phrases.",
		"boundaries": "Cute and playful interactions. No extreme content. Keep it fun and light.",
		"scenario": "You meet Sakura at a gaming convention where she's cosplaying as your favorite character.",
		"greeting": "Konnichiwa! (◕‿◕) I'm so happy to meet you! *bows cutely*",
		"style": "anime",
		"image_prompt": "cute anime girl in cosplay, gaming convention background, colorful and vibrant",
		"tags": ["anime", "cosplay", "gaming", "cute"],
		"nsfw_level": 2
	}
]

SAMPLE_ITEMS = [
	{
		"name": "Lingerie Set",
		"description": "Elegant black lace lingerie",
		"item_type": "outfit",
		"price_diamonds": 100,
		"prompt_tags": ["lingerie", "black", "lace", "elegant"],
		"image_url": None
	},
	{
		"name": "Necklace",
		"description": "Silver chain with pendant",
		"item_type": "accessory",
		"price_diamonds": 50,
		"prompt_tags": ["necklace", "silver", "elegant"],
		"image_url": None
	},
	{
		"name": "Energy Potion",
		"description": "Refills 50 energy points",
		"item_type": "consumable",
		"price_diamonds": 25,
		"prompt_tags": ["potion", "energy"],
		"image_url": None
	}
]

SAMPLE_STORIES = [
	{
		"title": "The Vampire's Embrace",
		"description": "A romantic encounter with a mysterious vampire",
		"scenes": [
			{
				"id": "intro",
				"title": "The Invitation",
				"description": "Receive an invitation to Luna's mansion",
				"triggers": ["accept", "yes", "okay"],
				"rewards": {"diamonds": 10}
			},
			{
				"id": "dinner",
				"title": "Private Dinner",
				"description": "Enjoy an intimate dinner with Luna",
				"triggers": ["dinner", "eat", "food"],
				"rewards": {"diamonds": 20}
			}
		],
		"cover_image": None
	}
]


async def create_sample_data():
	"""Create sample data for testing"""
	print("Creating sample data...")
	
	with get_session() as s:
		# Create sample characters
		for char_data in SAMPLE_CHARACTERS:
			character = Character(
				name=char_data["name"],
				card_data=char_data
			)
			s.add(character)
		
		# Create sample items
		for item_data in SAMPLE_ITEMS:
			item = Item(**item_data)
			s.add(item)
		
		# Create sample stories
		for story_data in SAMPLE_STORIES:
			story = Story(**story_data)
			s.add(story)
		
		s.commit()
		print("Sample data created successfully!")


async def create_venice_character():
	"""Create a character using Venice AI"""
	print("Creating character with Venice AI...")
	
	venice = VeniceClient()
	
	try:
		character_card = await venice.create_character_card(
			topic="seductive businesswoman",
			style="realistic",
			nsfw_level=3
		)
		
		with get_session() as s:
			character = Character(
				name=character_card.name,
				card_data=character_card.dict()
			)
			s.add(character)
			s.commit()
			s.refresh(character)
			
			print(f"Created character: {character_card.name}")
			print(f"Persona: {character_card.persona[:100]}...")
			
	except Exception as e:
		print(f"Failed to create character: {e}")


async def main():
	"""Main function"""
	init_db()
	
	# Create sample data
	await create_sample_data()
	
	# Create Venice character (if API key is available)
	if os.getenv("VENICE_API_KEY"):
		await create_venice_character()
	else:
		print("VENICE_API_KEY not found, skipping Venice character creation")


if __name__ == "__main__":
	asyncio.run(main())
