import asyncio
from db.VARS import DbVars
from db.queries import Queries

from funcraftdownloader import ProfileDler

BASE_URL = "https://www.funcraft.net/fr/joueur/"

async def main():
    DbVars.Queue.start()
    DbVars.Queue.add_important_instruction(Queries.get_create_repo_table_query("funcraft_stats"))
    await asyncio.sleep(1)
        
    dler = ProfileDler()
    dler.remaining_elements = list(range(2150000, 2364000))
    await dler.grab_all()


asyncio.run(main())
DbVars.Queue.should_stop = True

#START INDEX FOR BAN PARSING: aprox 853 000