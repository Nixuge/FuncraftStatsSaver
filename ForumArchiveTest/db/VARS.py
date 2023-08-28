from db.instance import DbInstance
from db.queue import DbQueue

# Kinda dirty but that's how it is
class DbVars:
    # TO BE USED STRICTLY FOR READ TASKS !
    # USE THE QUEUE OTHERWISE !
    ReadInstanceThreads = DbInstance("funcraft_forum.db")

    # TO BE USED STRICTLY FOR WRITE TASKS, WITH THE 
    # add_instuction() AND add_important_instruction() FUNCTIONS ! 
    # USE THE ReadInstance TO READ DATA INSTEAD !
    QueueThreads = DbQueue("funcraft_forum.db")

    # TO BE USED STRICTLY FOR READ TASKS !
    # USE THE QUEUE OTHERWISE !
    ReadInstancePosts = DbInstance("funcraft_forum_posts.db")

    # TO BE USED STRICTLY FOR WRITE TASKS, WITH THE 
    # add_instuction() AND add_important_instruction() FUNCTIONS ! 
    # USE THE ReadInstance TO READ DATA INSTEAD !
    QueuePosts = DbQueue("funcraft_forum_posts.db")
