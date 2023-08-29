from db.VARS import DbVars

DbVars.Queue.start()

with open("ban.txt", "r") as file:
    count = 0
    print()
    for row in file.read().splitlines():
        count += 1
        if "#" in row or row == "":
            continue
        user_id, ban_status = row.split(" ||| ")
        user_id = int(user_id)
        # print(f"{user_id}: {ban_status}")
        query = f"UPDATE funcraft_stats SET ban = '{ban_status}' WHERE id=={user_id};"
        DbVars.Queue.add_instuction((query, ))
        

DbVars.Queue.should_stop = True
# query = f"UPDATE funcraft_stats SET ban = {ban} WHERE id=={user_id};"