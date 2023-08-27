import asyncio
import random
import re
import httpx

from asynclimiter import AsyncLimiter

BASE_URL = "https://www.funcraft.net/fr/joueur/"

# If anyone comes here, yes, those are exposed proxies.
# I'll remove them once I'm done w saving as much as possible.
PROXIES = [
    {"https://": "http://esmbmiqf:ex5zd8godsmp@2.56.119.93:5074"},
    {"https://": "http://esmbmiqf:ex5zd8godsmp@185.199.229.156:7492"},
    {"https://": "http://esmbmiqf:ex5zd8godsmp@185.199.228.220:7300"},
    {"https://": "http://esmbmiqf:ex5zd8godsmp@185.199.231.45:8382"},
    {"https://": "http://esmbmiqf:ex5zd8godsmp@188.74.210.207:6286"},
    {"https://": "http://esmbmiqf:ex5zd8godsmp@188.74.183.10:8279"},
    {"https://": "http://esmbmiqf:ex5zd8godsmp@188.74.210.21:6100"},
    {"https://": "http://esmbmiqf:ex5zd8godsmp@45.155.68.129:8133"},
    {"https://": "http://esmbmiqf:ex5zd8godsmp@154.95.36.199:6893"},
    {"https://": "http://esmbmiqf:ex5zd8godsmp@45.94.47.66:8110"},
]

class ProfileDler(AsyncLimiter):
    def __init__(self) -> None:
        super().__init__(self.dl_profile, max_task_count=15, polling_sleep=.001)

    def contains(self, index):
        with open("done.txt", "r") as file:
            if str(index) in file.read().splitlines():
                return True
        return False

    async def dl_profile(self, index: int):
        if self.contains(index):
            self.skipped_tasks += 1
            return True
        
        while self.global_lock:
            await asyncio.sleep(.5)

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

            failed_nonfatal = r_image.status_code != 200

            if failed_nonfatal:
                await self.wait_global()
                await self.fail_nonfatal(image_url)

            filepath_html = f"pages/{index} ({username}).html"
            filepath_image = f"images/{image_id}.png"

            with open(filepath_html, "w") as file:
                file.write(r_page.text)

            with open(filepath_html, "a") as file:
                file.write("\n\n\n||FRIENDS PART, TO PARSE LATER||\n\n" + r_friends.text)

            if not failed_nonfatal:
                with open(filepath_image, "wb") as file:
                    file.write(r_image.content)

        except Exception as e:
            await self.wait_global()
            return await self.fail_retry(index)

        await self.done(index)
        await asyncio.sleep(1)
        return True