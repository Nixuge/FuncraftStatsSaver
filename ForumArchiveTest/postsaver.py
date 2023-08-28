import gzip
import json
import math
import os
import random
import re
from threading import Thread
import time
from bs4 import BeautifulSoup, Tag

import httpx
from PROXIES import PROXIES
from asynclimiter import ThreadLimiter
from db.VARS import DbVars
from db.queries import QueriesPosts, QueriesThreads
from db.utils import DbUtils
from threads_pages import THREADS_PAGES


class ForumPostSaver(ThreadLimiter):
    def __init__(self) -> None:
        super().__init__(self.dl_page, max_task_count=40, polling_sleep=.1)
        self.lock_img = False
        self.lock_user = False
        self.lock_done = False
        self.done_lines = {}
       
    def gen_done_lines(self, category: str):
        self.lock_done = True
        path = f"done/{category}.txt"
        if not os.path.isfile(path):
            self.lock_done = False
            self.done_lines[category] = []
            return
        
        with open(path, "r") as file:
            self.done_lines[category] = file.read().splitlines()

            
        self.lock_done = False

    
    def add_img(self, img_url: str, category: str):
        while self.lock_img:
            time.sleep(self.polling_sleep)
        
        self.lock_img = True
        with open(f"images/{category}.txt", "a") as file:
            file.write(f"{img_url}\n")
        self.lock_img = False

    def add_user(self, user: str, category: str):
        while self.lock_user:
            time.sleep(self.polling_sleep)
        
        self.lock_user = True
        with open(f"users/{category}.txt", "a") as file:
            file.write(f"{user}\n")
        self.lock_user = False

    def done(self, id: int, category: str):
        while self.lock_done:
            time.sleep(self.polling_sleep)
        
        self.lock_done = True
        with open(f"done/{category}.txt", "a") as file:
            file.write(f"{id}\n")
        self.lock_done = False

    def get_done(self, val: str, category: str):
        while self.lock_done:
            time.sleep(self.polling_sleep)
        
        lines = self.done_lines.get(category)
        if not lines:
            self.gen_done_lines(category)
            lines = self.done_lines.get(category)

        if str(val) in lines:
            return True

        return False


    def dl_page(self, data: tuple[str, str, int]):
        thread = ThreadSaver(self, data)
        self.tasks.append(thread)
        thread.start()

LINK_REGEX = re.compile("\"https:\/\/d3lkwj5yf9cdhp\.cloudfront\.net\/(.*?)\"")

class ThreadSaver(Thread):
    def __init__(self, clazz: ForumPostSaver, data: tuple[str, str, int]):
        Thread.__init__(self)
        self.data = data
        self.category = data[0]
        self.url = data[1]
        self.url_short = self.url.replace("https://community.funcraft.net/", "")
        self.parent_thread_id = data[2]
        self.clazz = clazz
        self.soup = None
 
    def run(self):
        if self.clazz.get_done(self.url_short, self.category):
            self.clazz.skipped_tasks += 1
            return

        try:
        # if True:
            prox = random.choice(PROXIES)
            req = httpx.get(self.url, proxies=prox)
            if req.status_code != 200:
                return self.clazz.fail_retry(self.data, f"Non 200 code for req for {self.url}: {req.status_code}")
            
            self.soup = BeautifulSoup(req.text, "html.parser")

            instrs: list[tuple] = []

            posts = self.get_all_post_divs()
            for post in posts:
                self.parse_images(post)
                post_author_id, post_author_name = self.parse_user_links_get_id(post)
                post_content = self.get_post_content_gzipped(post)
                post_number, date_dernier_edit, date_post = self.get_bottom_bar_data(post)
                post_id = self.get_post_id(post)
                likes = self.parse_likes(post, post_id)
                if likes:
                    likes = gzip.compress(bytes(json.dumps(likes), encoding="utf-8"))
                sondage = self.parse_sondage(self.soup)
                if sondage:
                    sondage = gzip.compress(bytes(json.dumps(sondage), encoding="utf-8"))


                instrs.append((
                    post_id, self.parent_thread_id,
                    post_number, post_author_id, post_author_name,
                    date_dernier_edit, date_post,
                    likes, post_content, sondage
                ))

            # print(QueriesPosts.get_insert_query(self.category))
            # print(len(instrs[0]))
            # input()

            for instr in instrs:
                DbVars.QueuePosts.add_instuction(
                    QueriesPosts.get_insert_query(self.category),
                    instr
                )
            


        except Exception as e:
            return self.clazz.fail_retry(self.data, f"Failed exception: {e} for {self.url}")

        self.clazz.done_tasks += 1
        self.clazz.done(self.url_short, self.category)


    def get_all_post_divs(self) -> list[Tag]:
        normal = self.soup.find("ol", {"id": "messageList"})
        return normal.find_all("li", {"class": "message"}, recursive=False)

    def parse_images(self, post_tag: Tag) -> None:
        images = re.findall(LINK_REGEX, str(post_tag))
        for image in images:
            self.clazz.add_img(image, self.category)

    def parse_user_links_get_id(self, post_tag: Tag) -> int:
        userinfo = post_tag.find("div", {"class": "messageUserInfo"})
        username_id_wrap = userinfo.find("a", {"class": "username", "itemprop": "name"})
        if username_id_wrap.get("href"):
            username_id = username_id_wrap["href"]
            username_id = username_id.replace("members/", "").replace("/", "")
            self.clazz.add_user(username_id, self.category)
            splitted = username_id.split(".")
            return int(splitted[-1]), username_id_wrap.text
        else:
            return -1, username_id_wrap.text
    
    def get_post_id(self, post_tag: Tag) -> int:
        return int(post_tag["id"].replace("post-", ""))

    def get_post_content_gzipped(self, post_tag: Tag) -> bytes:
        data_str = str(post_tag.find("div", {"class": "messageContent"}))
        return gzip.compress(bytes(data_str, encoding="utf-8"))

    def get_bottom_bar_data(self, post_tag: Tag) -> tuple:
        bottombar = post_tag.find("div", {"class": "messageDetails"})
        postnum_w = bottombar.find("a", {"class": "postNumber"})
        post_number = int(postnum_w.text.replace("#", "").replace(" ", ""))

        date_dernier_edit = bottombar.find("div", {"class": "editDate"})
        if date_dernier_edit:
            date_dernier_edit = date_dernier_edit.find("span", {"class": "DateTime"})["title"]

        date_post = bottombar.find("a", {"class": "datePermalink"})
        date_post = date_post.find("span", {"class": "DateTime"})["title"]

        return (post_number, date_dernier_edit, date_post)

    def parse_likes(self, post_tag: Tag, post_id: int) -> list[tuple] | None:
        likes = post_tag.find("span", {"class": "LikeText"})
        if not likes:
            return None
        
        all_shown = likes.find_all("a", {"class": "username"})

        likes_base_url = f"https://community.funcraft.net/posts/{post_id}/likes"

        additional = likes.find("a", {"class": "OverlayTrigger"})
        if additional:
            count = int(additional.text.replace("autres personnes", "").replace("autre personne", "")) + len(all_shown)
        else:
            count = 1

        likes: list[tuple[int, str]] = [] #id, date 
        
        page_max = math.ceil(count / 100)
        for i in range(1, page_max + 1):
            # print(f"making request: ?page={i}")
            result = httpx.get(f"{likes_base_url}?page={i}", proxies=random.choice(PROXIES))
            while result.status_code != 200:
                # print(f"failed req, retrying {result.status_code} + {likes_base_url}?page={i}")
                time.sleep(1)
                result = httpx.get(f"{likes_base_url}?page={i}", proxies=random.choice(PROXIES))
            
            newsoup = BeautifulSoup(result.text, "html.parser")
            # print(f"{likes_base_url}?page={i}")
            likes_current_page = newsoup.find("ol", {"class": "overlayScroll"})

            # If player has a hidden profile, it won't show
            if not likes_current_page:
                return None
            
            likes_current_page: list[Tag] = likes_current_page.find_all("li", {"class": "memberListItem"})
            for like in likes_current_page:
                date = like.find("div", {"class": "extra"}).find("span", {"class": "DateTime"})["title"]
                id = like.find("h3", {"class": "username"}).find("a", {"class": "username"})
                id = int(id["href"].replace("members/", "").replace("/", "").split(".")[-1])
                likes.append((id, date))

        return likes

    def parse_sondage(self, page_tag: Tag) -> dict | None:
        poll = page_tag.find("div", {"class": "pollContent"})
        if not poll:
            return None
    
        data = {}
        data["question"] = poll.find("h2", {"class": "questionText"}).text
        data["reponses"] = str(poll.find("div", {"class": "pollResultsOverlay"}))
        return data
        
