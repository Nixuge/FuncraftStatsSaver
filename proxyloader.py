newfile = ""
with open("proxies", "r") as file:
    for line in file.read().splitlines():
        ip, port, user, passw = line.split(":")
        url = f"http://{user}:{passw}@{ip}:{port}"
        line = '{"https://": "' + url + '"},'
        newfile += line + "\n"

    
with open("proxiesformatted", "w") as file:
    file.write(newfile)