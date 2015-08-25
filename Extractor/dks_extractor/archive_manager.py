import json
import os


class ArchiveManager(object):
    """ High-level archive extraction interface.

    This is not a BDT/BND/whatever parser but an interface managing these
    parsers, giving them the correct file lists, etc.
    """

    EXTERNAL_ARCHIVES_IDENT = [0, 1, 2, 3]

    def __init__(self, resource_dir = None):
        self.hash_maps = {}
        if resource_dir is not None:
            self.load_resources(resource_dir)

    def load_resources(self, resource_dir):
        self._load_hash_maps(resource_dir)

    def full_extraction(self, data_dir, output_dir):
        pass

    def _load_hash_maps(self, resource_dir):
        for ident in ArchiveManager.EXTERNAL_ARCHIVES_IDENT:
            hash_map_file_name = "dvdbnd{}.hashmap.json".format(ident)
            hash_map_file_path = os.path.join(resource_dir, hash_map_file_name)
            self._load_hash_map(ident, hash_map_file_path)

    def _load_hash_map(self, ident, hash_map_file_path):
        with open(hash_map_file_path, "r") as hash_map_file:
            self.hash_maps[ident] = json.load(hash_map_file)
