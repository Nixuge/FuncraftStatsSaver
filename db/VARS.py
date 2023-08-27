from db.instance import DbInstance
from db.queue import DbQueue

# Kinda dirty but that's how it is
class DbVars:
    # TO BE USED STRICTLY FOR READ TASKS !
    # USE THE QUEUE OTHERWISE !
    ReadInstance = DbInstance("funcraft_database.db")

    # TO BE USED STRICTLY FOR WRITE TASKS, WITH THE 
    # add_instuction() AND add_important_instruction() FUNCTIONS ! 
    # USE THE ReadInstance TO READ DATA INSTEAD !
    Queue = DbQueue("funcraft_database.db")
