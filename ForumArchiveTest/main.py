from db.VARS import DbVars
from db.queries import QueriesPosts, QueriesThreads
from postsaver import ForumPostSaver

from threads_pages import THREADS_PAGES


DbVars.QueuePosts.start()
saver = ForumPostSaver()

to_save: list[tuple[str, str]] = []

BASE_URL = "https://community.funcraft.net/"

all_elements = []

for category in THREADS_PAGES.keys():
    DbVars.QueuePosts.add_important_instruction(QueriesPosts.get_create_repo_table_query(category))
    query = F"SELECT * FROM {category}"
    results = DbVars.ReadInstanceThreads.cursor.execute(query).fetchall()

    for result in results:
        pages = int(result[1])
        result_base_url = BASE_URL + result[10]
        for i in range(1, pages + 1):
            suffix = "" if int(i) == 1 else f"page-{i}"
            element = (category, result_base_url + suffix, result[0])
            all_elements.append(element)


saver.remaining_elements = all_elements
saver.grab_all()

DbVars.QueuePosts.should_stop = True
DbVars.QueueThreads.should_stop = True