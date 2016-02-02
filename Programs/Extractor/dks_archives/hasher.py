""" Generate hashes corresponding to the BHD5 data entry format. """

import json


def hash_string(characters):
    """ Get an 8 character BHD5 hash from this string. """
    hash_value = get_hash_value(characters)
    eight_chars_hash = format_hash(hash_value)
    return eight_chars_hash

def get_hash_value(characters):
    """ Get the full hash value for this string. """
    characters = characters.lower()
    hash_value = 0
    for character in characters:
        hash_value *= 37
        hash_value += ord(character)
    return hash_value

def format_hash(hash_value):
    """ Format a hash value to a 8 characters BHD5 hash. """
    string_hash = "{:08X}".format(hash_value)
    four_least_significant_bytes = string_hash[-8:]
    return four_least_significant_bytes





def load_filelist(filelist_file_path):
    """ Load a file containing a list of file name on each line. """
    file_names = []
    with open(filelist_file_path, "r") as filelist_file:
        for line in filelist_file:
            line = line.rstrip("\n")
            file_names.append(line)
    return file_names

def save_json_map(hash_map, json_file_path):
    """ Save the JSON-compatible object hash_map at json_file_path. """
    with open(json_file_path, "w") as json_file:
        json.dump(hash_map, json_file, indent = 2)
