from pprint import pprint
import re
import sqlite3


with open("lines.txt", "r") as file:
    content = file.read().splitlines()

urls = []

for line in content:
    urls.append(line.split(" ")[2])

ids = []

for url in urls:
    if "?q=" in url: continue
    match = re.search("www.funcraft.net/fr/joueur/(\d*?)/", url)
    if not match: continue
    ids.append(match.groups()[0])

ids = list(set(ids))

connection = sqlite3.connect("../ORIGINAL_W_BANS_GZIPNULL.db")
cursor = connection.cursor()
QUERY = "SELECT * FROM funcraft_stats WHERE id == (?);"
for id in ids:
    result = cursor.execute(QUERY, (int(id), )).fetchone()
    if result[1] == None:
        print("MATCH!", id)