import json


def load_filelist(hashmap_path):
    """ Load a JSON filelist hashmap and transform all string keys to ints. """
    with open(hashmap_path, "r") as hashmap_file:
        hashmap = json.load(hashmap_file)
    hashmap = { int(k, 16): hashmap[k] for k in hashmap.keys() }
    return hashmap
