import os


output_dir = r"F:\Dev\Projets\DarkSoulsDev\ExtractedSounds"

extensions = {}


for root, dirs, files in os.walk(output_dir):
    for file_name in files:
        ext = os.path.splitext(file_name)[1]
        ext = ext.lstrip(".")
        if ext in extensions:
            extensions[ext] += 1
        else:
            extensions[ext] = 0

for ext in sorted(list(extensions.keys())):
    print(ext, ":", extensions[ext])
