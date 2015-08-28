import os
import sys

d = sys.argv[1]
magics = []
for f in os.listdir(d):
    f = os.path.join(d, f)
    if not os.path.isfile(f):
        continue
    with open(f, "rb") as fi:
        magic = fi.read(4)
    magics.append(magic)

for magic in magics:
    print(magic)
