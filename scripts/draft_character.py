import asyncio
import os
import json
from app.services.venice import VeniceClient


async def main() -> None:
	client = VeniceClient(api_key=os.environ.get("VENICE_API_KEY"))
	card = await client.draft_character_card(topic="Southern charm cowgirl neighbor")
	print(json.dumps(card, ensure_ascii=False, indent=2))


if __name__ == "__main__":
	asyncio.run(main())
