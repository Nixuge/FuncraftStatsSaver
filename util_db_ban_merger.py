from db.VARS import DbVars

DbVars.Queue.start()

with open("ban_pre1M.txt", "r") as file:
    print()
    for row in file.read().splitlines():
        if "#" in row or row == "":
            continue
        user_id, ban_status = row.split(" ||| ")
        user_id = int(user_id)
        query = f"UPDATE funcraft_stats SET ban = '{ban_status}' WHERE id=={user_id};"
        DbVars.Queue.add_instuction(query, None)
        

DbVars.Queue.should_stop = True
