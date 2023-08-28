import os
from db.VARS import DbVars
from db.queries import QueriesPosts, QueriesThreads
from postsaver import ForumPostSaver

from threads_pages import THREADS_PAGES


DbVars.QueuePosts.start()
saver = ForumPostSaver()

to_save: list[tuple[str, str]] = []

BASE_URL = "https://community.funcraft.net/"

all_elements = []

# =====DONE=====
# "annonces_regles"
# "recrutement_staff",
# discussions
# "teams",

# =====REMAINING=====
# "presentation_de_teams",
# "recrutement_teams",
# "suggestions_idees",
# "ameliorations",
# "propositions_de_mini_jeux",
# "astuces_entraide",
# "demande_daide_questions",
# "signaler_un_bug",
# "bugs_traites",
# "hors_sujet",
# "les_jeux_forum",
# "presentez_vous",
# "presentation_du_staff",
# "vos_talents_creations",
# "demandes_de_creations",
# "discussions_minecraft",
# "maps_constructions_redstone",
# "resource_packs",
# "mods_plugins_outils"



# for category in THREADS_PAGES.keys():
for category in ["presentation_de_teams"]:
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

for pathes in ["users/", "images/", "done"]:
    if not os.path.isdir(pathes):
        os.makedirs(pathes)


# all_elements.append(("discussions", "https://community.funcraft.net/threads/rec-rush-elo-contenders-season-3.76816/page-6", 76816))

saver.remaining_elements = all_elements
saver.grab_all()

DbVars.QueuePosts.should_stop = True
DbVars.QueueThreads.should_stop = True