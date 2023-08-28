import asyncio
import random
from threading import Thread
import httpx
from PROXIES import PROXIES

from asynclimiter import AsyncLimiter
from db.instance import DbInstance
from funcraftparser import parse_ban

BASE_URL = "https://www.funcraft.net/fr/joueur/"

def get_deja_part_filename(filename: str):
    liste = []
    with open(filename, "r") as file:
        lignesraw = file.read().splitlines()
    for ligne in lignesraw:
        if ligne == "" or "#" in ligne:
            continue
        ligne = ligne.replace(" ||| à vie / très longtemps", "")
        ligne = ligne.replace(" ||| temporairement", "")
        liste.append(int(ligne))
    return liste

def get_deja_parse():
    full = get_deja_part_filename("ban.txt")
    prev = get_deja_part_filename("ban_pre1M.txt")
    return full + prev


deja_parse = get_deja_parse()

print(deja_parse)



class BanDler(AsyncLimiter):
    def __init__(self) -> None:
        super().__init__(self.dl_profile, max_task_count=250, polling_sleep=.08)

    async def dl_profile(self, url: str):
        id = int(url.split("/")[0])
        if id in deja_parse:
            self.skipped_tasks += 1
            return True
        
        await self.parse_profile(url)

    async def parse_profile(self, url: str):
        thread = SaveThread(self, url)
        thread.start()
        
        while thread.is_alive():
            await asyncio.sleep(.1)
        
        return


class SaveThread(Thread):
    def __init__(self, clazz, url: str):
        Thread.__init__(self)
        self.clazz = clazz
        self.url = url
 
    def run(self):
        client = httpx.Client(proxies=random.choice(PROXIES))
        try:
            r_page = client.get(BASE_URL + self.url)

            ban = parse_ban(r_page.text)
            if ban:
                self.clazz.ban(self.url.split("/")[0], ban, "ban_pre1M.txt")

            # with open(filepath_html, "w") as file:
            #     file.write(r_page.text)

            # with open(filepath_html, "a") as file:
            #     file.write("\n\n\n||FRIENDS PART, TO PARSE LATER||\n\n" + r_friends.text)

            # with open(filepath_image, "wb") as file:
            #     file.write(r_image.content)

        except Exception as e:
            self.clazz.wait_global()
            return self.clazz.fail_retry(self.url, f"Failed exception: {e} for {self.url}")

        # await asyncio.sleep(1)
        self.clazz.done_tasks += 1
        return True


async def RUN_THIS():
    dler = BanDler()
    instance = DbInstance("funcraft_database (copy).db")
    rows = instance.cursor.execute("SELECT * FROM funcraft_stats WHERE id > 5000").fetchall()
    urls = []
    for row in rows:
        url = f"{row[0]}/{row[1]}/"
        urls.append(url)
        # print(url)
        # input()
    print("done parsing from db")
    # print(rows[0][1])
    # print(len(rows))
    dler.remaining_elements = urls
    await dler.grab_all()


asyncio.run(RUN_THIS())