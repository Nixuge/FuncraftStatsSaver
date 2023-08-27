import asyncio
import re
import httpx

from funcraftdownloader import ProfileDler

BASE_URL = "https://www.funcraft.net/fr/joueur/"

async def main():
    dler = ProfileDler()
    dler.remaining_elements = list(range(1, 2363980))
    await dler.grab_all()


asyncio.run(main())