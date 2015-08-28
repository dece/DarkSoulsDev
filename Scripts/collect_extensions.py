import os


output_dir = r"F:\Dev\Projets\DarkSoulsDev\Output"

extensions = set()

for root, dirs, files in os.walk(output_dir):
    for file_name in files:
        ext = os.path.splitext(file_name)[1]
        ext = ext.lstrip(".")
        extensions.add(ext)

for ext in sorted(extensions):
    print(ext)
