import os


def do_it(path: str):
    for filename in os.listdir(path):
        if "nodupes" in filename: continue
        with open(f"{path}/{filename}", "r") as file:
            lines = file.read().splitlines()
            lines = set([x + "\n" for x in lines])
        
        if not os.path.isdir(f"{path}/nodupes"):
            os.makedirs(f"{path}/nodupes")
        
        with open(f"{path}/nodupes/{filename}", "w") as file:
            file.writelines(lines)

do_it("images")
do_it("users")