import gzip
import sqlite3


connection = sqlite3.connect("funcraft_database.db", isolation_level='DEFERRED')

all = connection.cursor().execute("SELECT * FROM funcraft_stats;").fetchall()

QUERY = ""
print("done querying")
count = 0

bad_ids = []

for thing in all:
    user_id = int(thing[0])
    byte_friend_data = thing[8]
    if byte_friend_data == None:
        continue
    byte_friend_data = bytes.decode(gzip.decompress(thing[8]))
    
    if byte_friend_data == "null":
        bad_ids.append((user_id, ))

print(bad_ids)

query = f"UPDATE funcraft_stats SET gzipped_friends = NULL WHERE id==(?);"
cursor = connection.cursor()
cursor.executemany(query, bad_ids)
cursor.close()


connection.commit()

print("done !")
