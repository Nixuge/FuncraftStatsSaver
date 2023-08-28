import random
from threading import Thread
import time
from bs4 import BeautifulSoup, Tag

import httpx
from PROXIES import PROXIES
from asynclimiter import ThreadLimiter
from db.VARS import DbVars
from db.queries import QueriesThreads
from db.utils import DbUtils
from threads_pages import THREADS_PAGES


class ForumThreadMetaSaver(ThreadLimiter):
    def __init__(self) -> None:
        super().__init__(self.dl_page, max_task_count=30, polling_sleep=.1)
    
    def dl_page(self, data: tuple[str, str]):
        thread = ThreadSaver(self, data)
        self.tasks.append(thread)
        thread.start()

class ThreadSaver(Thread):
    def __init__(self, clazz: ForumThreadMetaSaver, data: tuple[str, str]):
        Thread.__init__(self)
        self.data = data
        self.category = data[0]
        self.url = data[1]
        self.clazz = clazz
        self.soup = None
 
    def run(self):
        DbVars.Queue.add_important_instruction(QueriesThreads.get_create_repo_table_query(self.category))
        time.sleep(1)
        try:
            req = httpx.get(self.url, proxies=random.choice(PROXIES))
            if req.status_code != 200:
                return self.clazz.fail_retry(self.data, f"Non 200 code for req for {self.url}")
            
            self.soup = BeautifulSoup(req.text, "html.parser")

            instrs = []

            normal = self.get_all_normal()
            
            if normal:
                for post in normal:
                    instrs.append(self.parse_post(post, False))

            sticky = self.get_all_sticky()
            if sticky:
                for post in sticky:
                    instrs.append(self.parse_post(post, True))

            for instr in instrs:
                DbVars.Queue.add_instuction(
                    QueriesThreads.get_insert_query(self.category),
                    instr
                )   


        except Exception as e:
            return self.clazz.fail_retry(self.data, f"Failed exception: {e} for {self.url}")

        self.clazz.done_tasks += 1

    def get_all_sticky(self) -> list[Tag] | None:
        sticky = self.soup.find("div", {"class": "uix_stickyThreads"})
        if not sticky:
            return
        return sticky.find_all("li")

    def get_all_normal(self) -> list[Tag] | None:
        normal = self.soup.find("ol", {"class": "discussionListItems"})
        if not normal:
            return
        return normal.find_all("li", {"class": "discussionListItem"}, recursive=False)

    def parse_post(self, posts_tag: Tag, sticky: bool) -> tuple:
        thread_id = int(posts_tag["id"].replace("thread-", ""))
        prefixe = posts_tag.find("span", {"class": "prefix"})
        if prefixe:
            prefixe = prefixe.text
        else:
            prefixe = None
        
        # last page
        pageNav = posts_tag.find("span", {"class": "itemPageNav"})
        if pageNav:
            pages = int(pageNav.find_all("a")[-1].text)
        else:
            pages = 1
        
        
        usernameA = posts_tag.find("a", {"class": "username"})


        date_creation_wrap = posts_tag.find("a", {"class": "faint"})
        date_creation = date_creation_wrap.find("span", {"class": "DateTime"}).text

        try:
            autheur_nom, autheur_id = usernameA["href"].replace("members/", "").replace("/", "").split(".")
            autheur_id = int(autheur_id)
        except:
            autheur_nom = usernameA.text
            autheur_id = -1

        title_url_wrapper = posts_tag.find("h3", {"class": "title"})
        title_url = title_url_wrapper.find("a", {"class": "PreviewTooltip"})
        if title_url:
            title = title_url.text
            thread_url = title_url["href"]
        else:
            title_url = title_url_wrapper.find("a")
            title = title_url.text
            thread_url = title_url["href"]

        try:
            reponses_wrapper = posts_tag.find("dl", {"class": "major"})
            reponses = int(reponses_wrapper.find("dd").text.replace(" ", ""))

            affichages_wrapper = posts_tag.find("dl", {"class": "minor"})
            affichages = int(affichages_wrapper.find("dd").text.replace(" ", ""))
        except:
            reponses = -1
            affichages = -1
        
        # print(posts_tag)

        return (thread_id, pages,
             prefixe, title,
             reponses, affichages,
             autheur_nom, autheur_id,
             date_creation, sticky, thread_url
             )
        

def start_info_saver():
    DbVars.Queue.start()
    saver = ForumThreadMetaSaver()

    to_save: list[tuple[str, str]] = []

    for category, url_list in THREADS_PAGES.items():
        DbVars.Queue.add_important_instruction(QueriesThreads.get_create_repo_table_query(category))
        for url in url_list:
            to_save.append((category, url))

    saver.remaining_elements = to_save

    saver.grab_all()

    DbVars.Queue.should_stop = True