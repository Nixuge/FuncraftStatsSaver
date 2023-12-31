import gc
import gzip
import json
import sqlite3
import time

from queries import get_query_create

GAMES = [
    "blitz",
    "hikabrain",
    "infected",
    "landrush",
    "mma",
    "pvpsmash",
    "rush",
    "rushretro", # disabled by default
    "shootcraft",
    "skywars",
    "survival"
]

def build_per_game():
    connection = sqlite3.connect("ORIGINAL_W_BANS_GZIPNULL.db")
    cursor = connection.cursor()

    all_rows = cursor.execute("SELECT * FROM funcraft_stats;").fetchall()
    # all_rows = cursor.execute("SELECT * FROM funcraft_stats;").fetchmany(5000)

    print("starting")
    start_time_total = time.time_ns()

    final_dict: dict[str, dict[str, dict[list[tuple]]]] = {}
    for game in GAMES:
        final_dict[game] = {}

    for row in all_rows:
        if row[7] == None:
            continue
        content = json.loads(gzip.decompress(row[7]))
        if not content:
            continue
        
        for month in content.keys():
            for game in GAMES:
                if not month in final_dict[game]:
                    final_dict[game][month] = []
                
                currentStats = content[month].get(game)
                if not currentStats: continue

                currentStats = currentStats["stats"]
                for stat in currentStats:
                    if stat["name"] == "glory":
                        final_dict[game][month].append((row[0], float(stat["value"])))
                        break


    print(f"done in {(time.time_ns() - start_time_total) / 1000000000}s")
    start_time = time.time_ns()
    print("Starting list organization")

    newdb = sqlite3.connect("rankings.db")
    for game in GAMES:        
        for month in final_dict[game]:
            month_db = month.replace("month-", "").replace("-", "_")
            newdb.cursor().execute(get_query_create(game, month_db))
            final_dict[game][month].sort(key=take_second)
            final_dict[game][month].reverse()
        newdb.commit()

    for game in GAMES:
        for month in final_dict[game]:
            for index, player in enumerate(final_dict[game][month]):
                final_dict[game][month][index] = (player[0], index + 1)
    
    print(f"done in {(time.time_ns() - start_time) / 1000000000}s")
    start_time = time.time_ns()
    print("Starting final insert")

    _cursor = newdb.cursor()
    for game in GAMES:
        for month in final_dict[game]:
            month_db = month.replace("month-", "").replace("-", "_")
            query = f"INSERT INTO {game}__{month_db} VALUES (?, ?)"
            
            _cursor.executemany(query, final_dict[game][month])
            newdb.commit()
    newdb.commit()
    newdb.close()

    print(f"done in {(time.time_ns() - start_time) / 1000000000}s")
    start_time = time.time_ns()
    print("Starting building player specific dict")
    player_dict: dict[str, dict[str, dict[str, dict]]] = {}
    for game in final_dict:
        for month in final_dict[game]:
            for player in final_dict[game][month]:
                id = player[0]
                rank = player[1]
                if not id in player_dict.keys():
                    player_dict[id] = {}
                if not game in player_dict[id].keys():
                    player_dict[id][game] = {}
                player_dict[id][game][month] = rank
    print(f"done in {(time.time_ns() - start_time) / 1000000000}s")
    print(f"cleaned up {gc.collect()} elements")

    start_time = time.time_ns()
    print("Compressing player rankings dicts")
    insert_data = []
    for playerid, data in player_dict.items():
        insert_data.append((gzip.compress(bytes(json.dumps(data), 'utf-8')), playerid))
        # final_dict.pop(playerid) # cleanup memory
    print(f"done in {(time.time_ns() - start_time) / 1000000000}s")
    
    print(f"cleaned up {gc.collect()} elements")
    start_time = time.time_ns()
    print("Starting player specific dict insertion")

    query = f"UPDATE funcraft_stats SET gzipped_rankings = (?) WHERE id == (?)"
    newconnagain = sqlite3.connect("funcraft_database_website.db")
    newconnagain.cursor().executemany(query, insert_data)
    newconnagain.commit()
    print(f"done in {(time.time_ns() - start_time) / 1000000000}s")
    print(f"all done in {(time.time_ns() - start_time_total) / 1000000000}s")
    
    # with open("save.json", "w") as file:
        # json.dump(final_dict, file, indent=4)


def take_second(elem):
    return elem[1]


def remove_empty_tables():
    sql_query = """SELECT name FROM sqlite_master WHERE type='table';"""
    connection = sqlite3.connect("rankings.db")
    all_tables = connection.cursor().execute(sql_query).fetchall()
    for table in all_tables:
        query = f"""SELECT * FROM {table[0]};"""
        data = connection.cursor().execute(query).fetchone()
        if data:
            print("good " + table[0])
            pass
        else:
            print("bad " + table[0])
            del_query = f"DROP TABLE {table[0]}"
            connection.cursor().execute(del_query)

def build_indexes():
    sql_query = """SELECT name FROM sqlite_master WHERE type='table';"""
    connection = sqlite3.connect("rankings.db")
    all_tables = connection.cursor().execute(sql_query).fetchall()
    for table in all_tables:
        print("building for " + table[0])
        query1 = f"CREATE INDEX idx_{table[0]}_ranking on {table[0]}(ranking);"
        connection.cursor().execute(query1)
        connection.commit()

print("building")     
build_per_game()
print("removing empty tables")
remove_empty_tables()
print("building indexes")
build_indexes()