import gzip

data = bytes.fromhex("hex from sqlite db viewer here")
print(gzip.decompress(data))