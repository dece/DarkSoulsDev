import json
import os

from dks_extractor.bdt_extractor import ComposedArchiveExtractor
from dks_extractor.bnd import StandaloneArchive
from dks_extractor.dcx import CompressedPackage


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

    def _load_hash_maps(self, resource_dir):
        for ident in ArchiveManager.EXTERNAL_ARCHIVES_IDENT:
            hash_map_file_name = "dvdbnd{}.hashmap.json".format(ident)
            hash_map_file_path = os.path.join(resource_dir, hash_map_file_name)
            self._load_hash_map(ident, hash_map_file_path)

    def _load_hash_map(self, ident, hash_map_file_path):
        with open(hash_map_file_path, "r") as hash_map_file:
            self.hash_maps[ident] = json.load(hash_map_file)

    def full_extraction(self, data_dir, output_dir):
        """ Perform the most complete extraction/inflating of data possible. """
        # self.extract_external_archives(data_dir, output_dir)

        # self.inflate_files(output_dir)
        self.extract_internal_archives(output_dir)


    def extract_external_archives(self, data_dir, output_dir):
        """ Extract all files from external composed archive (dvdbnd). """
        bdt_extractor = ComposedArchiveExtractor()
        for ident in ArchiveManager.EXTERNAL_ARCHIVES_IDENT:
            bhd_file_path, bdt_file_path = \
                    ArchiveManager.get_archive_file_paths(data_dir, ident)
            bdt_extractor.hash_map = self.hash_maps[ident]
            bdt_extractor.output_dir = os.path.join(output_dir, str(ident))
            os.makedirs(bdt_extractor.output_dir, exist_ok = True)
            bdt_extractor.extract_archive(bhd_file_path, bdt_file_path)

    @staticmethod
    def get_archive_file_paths(data_dir, ident):
        bhd_file_name = "dvdbnd{}.bhd5".format(ident)
        bhd_file_path = os.path.join(data_dir, bhd_file_name)
        bdt_file_name = "dvdbnd{}.bdt".format(ident)
        bdt_file_path = os.path.join(data_dir, bdt_file_name)
        return bhd_file_path, bdt_file_path

    def inflate_files(self, work_dir, remove_dcx = False):
        """ Inflate (= decompress) all DCX files in work_dir. """
        for root, dirs, files in os.walk(work_dir):
            for file_name in files:
                extension = os.path.splitext(file_name)[1]
                if extension == ".dcx":
                    full_path = os.path.join(root, file_name)
                    self._inflate_file(full_path)
                    if remove_dcx:
                        os.remove(full_path)

    def _inflate_file(self, dcx_file_path):
        dcx = CompressedPackage()
        dcx.load_file(dcx_file_path)
        inflated_file_path = os.path.splitext(dcx_file_path)[0]
        dcx.uncompress(inflated_file_path)

    def extract_internal_archives(self, work_dir, remove_bnd = False):
        for root, dirs, files in os.walk(work_dir):
            for file_name in files:
                if file_name.endswith("bnd"):
                    full_path = os.path.join(root, file_name)
                    self._extract_internal_archive(full_path, work_dir)
                    if remove_bnd:
                        os.remove(full_path)

    def _extract_internal_archive(self, bnd_file_path, output_dir):
        bnd = StandaloneArchive()
        bnd.load_file(bnd_file_path)
        bnd.extract_all_files(output_dir)
