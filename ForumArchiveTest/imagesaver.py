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


class ImageSaver(ThreadLimiter):
    def __init__(self) -> None:
        super().__init__(self.dl_page, max_task_count=1000, polling_sleep=.01)
        self.lock_done = False
        self.gen_done_lines()

    def gen_done_lines(self):
        self.lock_done = True
        path = f"done_images.txt"
        if not os.path.isfile(path):
            self.lock_done = False
            self.done_lines = []
            return
        
        with open(path, "r") as file:
            self.done_lines = file.read().splitlines()

        self.lock_done = False

    def done(self, url: str):
        while self.lock_done:
            time.sleep(self.polling_sleep)
        
        self.lock_done = True
        with open(f"done_images.txt", "a") as file:
            file.write(f"{url}\n")
        self.lock_done = False

    def get_done(self, url: str):
        while self.lock_done:
            time.sleep(self.polling_sleep)

        if str(url) in self.done_lines:
            return True

        return False


    def dl_page(self, data: str):
        thread = ImageSaverThread(self, data)
        self.tasks.append(thread)
        thread.start()


class ImageSaverThread(Thread):
    def __init__(self, clazz: ImageSaver, url: str):
        Thread.__init__(self)
        self.path = url
        self.clazz = clazz
        self.soup = None
 
    def run(self):
        if self.clazz.get_done(self.path):
            self.clazz.skipped_tasks += 1
            return

        try:
        # if True:
            prox = random.choice(PROXIES)

            full_url = "https://d3lkwj5yf9cdhp.cloudfront.net/" + self.path
            subdir = "image_downloads/" + "/".join(self.path.split("/")[:-1])
            if not os.path.isdir(subdir):
                os.makedirs(subdir)
            
            req = httpx.get(full_url)
            if req.status_code != 200:
                return self.clazz.fail_retry(self.path, f"Non 200 code for req for {self.path}: {req.status_code}")

            with open("image_downloads/" + self.path, "wb") as file:
                file.write(req.content)
            
            self.clazz.done(self.path)

        except Exception as e:
            return self.clazz.fail_retry(self.path, f"Failed exception: {e} for {self.path}")

        self.clazz.done_tasks += 1
        self.clazz.done(self.path)


if __name__ == "__main__":
    links = []
    for filename in os.listdir("images/nodupes"):
        with open(f"images/nodupes/{filename}") as file:
            data = file.read().splitlines()
        links += data

    saver = ImageSaver()
    saver.remaining_elements = links
    saver.grab_all()