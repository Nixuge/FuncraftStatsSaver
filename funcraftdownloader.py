import asyncio
from concurrent.futures import ProcessPoolExecutor
import gzip
from io import BytesIO, StringIO
import json
import random
import re
from threading import Thread
import httpx

from db.VARS import DbVars
from asynclimiter import AsyncLimiter
from db.queries import Queries
from db.utils import DbUtils
from funcraftparser import parse_ban, parse_friend_html, parse_page_html

BASE_URL = "https://www.funcraft.net/fr/joueur/"

# If anyone comes here, yes, those are exposed proxies.
# I'll remove them once I'm done w saving as much as possible.
PROXIES = [


]

class ProfileDler(AsyncLimiter):
    def __init__(self) -> None:
        super().__init__(self.dl_profile, max_task_count=200, polling_sleep=.01)

    def contains(self, index):
        with open("done.txt", "r") as file:
            if str(index) in file.read().splitlines():
                return True
        return False

    async def dl_profile(self, index: int):
        if DbUtils.contains_id(index):
            self.skipped_tasks += 1
            return True
        
        await self.parse_profile(index)

    async def parse_profile(self, index: int):
        thread = SaveThread(self, index)
        thread.start()
        
        while thread.is_alive():
            await asyncio.sleep(.1)
        
        return

        client = httpx.AsyncClient(proxies=random.choice(PROXIES))
        try:
            r_redirect = await client.get(BASE_URL + str(index))
            if r_redirect.status_code == 404:
                return await self.nonexistent(index)
            if r_redirect.status_code != 302:
                await self.wait_global()
                return await self.fail_retry(index)

            username = re.findall(f"<title>Redirecting to https:\/\/www\.funcraft\.net\/fr\/joueur\/{index}\/(.*)<\/title>", r_redirect.text)[0]

            r_page = await client.get(BASE_URL + str(index) + "/" + username)
            r_friends = await client.get(BASE_URL + str(index) + "?sendFriends=1")

            if r_page.status_code != 200 or r_friends.status_code != 200:
                await self.wait_global()
                return await self.fail_retry(index)
            
            image_id = re.findall(f"\/_u\/avatar\/head\/{username}\/m2\/(.*?)\"", r_page.text)[0]
            image_url = f"https://d31zb6ev5hmn3f.cloudfront.net/_u/avatar/head/{username}/m2/" + str(image_id)
            r_image = await client.get(image_url)

            if r_image.status_code != 200:
                await self.wait_global()
                await self.fail_retry(image_url)

            # filepath_html = f"pages/{index} ({username}).html"
            # filepath_image = f"images/{image_id}.png"

            page_data = parse_page_html(r_page.text)
            friend_list = parse_friend_html(r_friends.text)
            
            _temp_stats = bytes(page_data.stats_dict_str, 'utf-8')
            gzipped_stats = gzip.compress(_temp_stats)
            
            _temp_fl = bytes(json.dumps(friend_list), 'utf-8')
            gzipped_friend_list = gzip.compress(_temp_fl)

            DbVars.Queue.add_instuction(
                Queries.get_insert_query(),
                (index, username, page_data.rank,
                 page_data.inscription, page_data.derniere_connexion,
                 page_data.gloire, page_data.parties_jouees,
                 gzipped_stats, gzipped_friend_list,
                 image_id, r_image.content
                 )
            )

            # with open(filepath_html, "w") as file:
            #     file.write(r_page.text)

            # with open(filepath_html, "a") as file:
            #     file.write("\n\n\n||FRIENDS PART, TO PARSE LATER||\n\n" + r_friends.text)

            # with open(filepath_image, "wb") as file:
            #     file.write(r_image.content)

        except Exception as e:
            await self.wait_global()
            return await self.fail_retry(index)

        # await asyncio.sleep(1)
        self.done_tasks += 1
        return True

class SaveThread(Thread):
    def __init__(self, clazz, index: int):
        Thread.__init__(self)
        self.clazz = clazz
        self.index = index
 
    def run(self):
        client = httpx.Client(proxies=random.choice(PROXIES))
        try:
            r_redirect = client.get(BASE_URL + str(self.index))
            if r_redirect.status_code == 404:
                return self.clazz.nonexistent(self.index)
            if r_redirect.status_code != 302:
                self.clazz.wait_global()
                return self.clazz.fail_retry(self.index, f"FAILED 302! {r_redirect.status_code} for {self.index} ({r_redirect.text})")

            username = re.findall(f"<title>Redirecting to https:\/\/www\.funcraft\.net\/fr\/joueur\/{self.index}\/(.*)<\/title>", r_redirect.text)[0]

            if "?" in username or "#" in username:
                DbVars.Queue.add_instuction(
                    Queries.get_insert_query(),
                    (self.index, username, None,
                    None, None,
                    None, None,
                    None, None,
                    None, None
                    )
                )
                self.clazz.done_tasks += 1
                return True



            r_page = client.get(BASE_URL + str(self.index) + "/" + username)
            r_friends = client.get(BASE_URL + str(self.index) + "?sendFriends=1")

            if r_page.status_code != 200 or r_friends.status_code != 200:
                self.clazz.wait_global()
                return self.clazz.fail_retry(self.index, f"FAILED r_page or r_friends for {self.index} (URL: {BASE_URL}{self.index}/{username}):\n{r_page.status_code} ({r_page.text})\n{r_friends.status_code} ({r_friends.text})")
            
            image_id = re.findall(f"\/_u\/avatar\/head\/{username}\/m2\/(.*?)\"", r_page.text)[0]
            image_url = f"https://d31zb6ev5hmn3f.cloudfront.net/_u/avatar/head/{username}/m2/" + str(image_id)
            r_image = client.get(image_url)

            if r_image.status_code != 200:
                self.clazz.wait_global()
                self.clazz.fail_retry(self.index, f"Image error (id: {self.index}, img_url: {image_url})")

            # filepath_html = f"pages/{index} ({username}).html"
            # filepath_image = f"images/{image_id}.png"

            page_data = parse_page_html(r_page.text)
            friend_list = parse_friend_html(r_friends.text)
            
            _temp_stats = bytes(page_data.stats_dict_str, 'utf-8')
            gzipped_stats = gzip.compress(_temp_stats)
            
            _temp_fl = bytes(json.dumps(friend_list), 'utf-8')
            gzipped_friend_list = gzip.compress(_temp_fl)

            ban = parse_ban(r_page.text)
            if ban:
                self.clazz.ban(self.index, ban)


            DbVars.Queue.add_instuction(
                Queries.get_insert_query(),
                (self.index, username, page_data.rank,
                 page_data.inscription, page_data.derniere_connexion,
                 page_data.gloire, page_data.parties_jouees,
                 gzipped_stats, gzipped_friend_list,
                 image_id, r_image.content
                 )
            )

            # with open(filepath_html, "w") as file:
            #     file.write(r_page.text)

            # with open(filepath_html, "a") as file:
            #     file.write("\n\n\n||FRIENDS PART, TO PARSE LATER||\n\n" + r_friends.text)

            # with open(filepath_image, "wb") as file:
            #     file.write(r_image.content)

        except Exception as e:
            self.clazz.wait_global()
            return self.clazz.fail_retry(self.index, f"Failed exception: {e} for {self.index}")

        # await asyncio.sleep(1)
        self.clazz.done_tasks += 1
        return True