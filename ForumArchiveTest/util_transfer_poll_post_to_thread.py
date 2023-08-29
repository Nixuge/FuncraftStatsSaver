import time
from db.VARS import DbVars
from db.queries import QueriesPosts
from threads_pages import THREADS_PAGES

DbVars.QueueThreads.start()

sondages_map = {}

for category in THREADS_PAGES.keys():
    # print(category)
    rows = DbVars.ReadInstancePosts.cursor.execute(f"SELECT * FROM {category} WHERE sondage IS NOT NULL").fetchall()
    if len(rows) == 0: continue
    sondages_map[category] = []
    for row in rows:
        parent_id = row[1]
        sondage_blob = row[9]
        sondages_map[category].append((sondage_blob, parent_id))

time.sleep(2)

for category, tuples in sondages_map.items():
    # DbVars.QueueThreads.cursor.execute(f"ALTER TABLE {category} ADD poll BLOB")
    # DbVars.QueueThreads.connection.commit()
    DbVars.QueuePosts.cursor.execute(f"ALTER TABLE {category} DROP COLUMN sondage")
    
    # query = f"UPDATE {category} SET poll = (?) WHERE thread_id==(?);"
    # DbVars.QueueThreads.cursor.executemany(query, tuples)
    # DbVars.QueueThreads.connection.commit()
    print(category)


DbVars.QueueThreads.should_stop = True
