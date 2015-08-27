import os

d = r"F:\Dev\Projets\DarkSoulsDev\Output\2"

os.chdir(d)

magics = []
for f in os.listdir():
    with open(f, "rb") as fi:
        magic = fi.read(4)
    magics.append(magic)

for magic in magics:
    print(magic)
