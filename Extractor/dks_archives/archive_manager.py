import json
import os

from dks_archives.bdt_extractor import ( CombinedArchiveExtractor
                                       , CombinedArchiveExtractorMode )
from dks_archives.bnd import StandaloneArchive
from dks_archives.dcx import CompressedPackage
import dks_archives.file_names as file_names




class ArchiveManager(object):
    """ High-level archive extraction interface.

    This is not a BDT/BND/whatever parser but an interface managing these
    parsers, giving them the correct file lists, etc. It tries to ensure that
    no level of packaging/compression is left behind. If it fails to do so, it's
    a bug.
    """

    EXTERNAL_ARCHIVES_IDENT = [0, 1, 2, 3]
    RELATIVE_ROOT = "N\\FRPG\\data\\INTERROOT_win32"

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
        self.extract_all_external_bdts(data_dir, output_dir)
        self.inflate_files(output_dir, True)
        self.extract_all_bnds(output_dir, True)
        self.extract_all_bnds(output_dir, True)
        self.extract_all_internal_bdts(output_dir, True)
        self.inflate_files(output_dir, True)

    def extract_all_external_bdts(self, data_dir, output_dir):
        """ Extract all files from external composed archive (dvdbnd). """
        bhd5_mode = CombinedArchiveExtractorMode.BHD5
        bdt_extractor = CombinedArchiveExtractor(bhd5_mode)
        output_dir = os.path.join(output_dir, ArchiveManager.RELATIVE_ROOT)
        bdt_extractor.output_dir = output_dir
        for ident in ArchiveManager.EXTERNAL_ARCHIVES_IDENT:
            bhd_file_path, bdt_file_path = \
                    ArchiveManager._get_bdt_bhd5_paths(data_dir, ident)
            bdt_extractor.hash_map = self.hash_maps[ident]
            os.makedirs(bdt_extractor.output_dir, exist_ok = True)
            bdt_extractor.extract_archive(bhd_file_path, bdt_file_path)

    @staticmethod
    def _get_bdt_bhd5_paths(data_dir, ident):
        bhd_file_name = "dvdbnd{}.bhd5".format(ident)
        bhd_file_path = os.path.join(data_dir, bhd_file_name)
        bdt_file_name = "dvdbnd{}.bdt".format(ident)
        bdt_file_path = os.path.join(data_dir, bdt_file_name)
        return bhd_file_path, bdt_file_path

    def extract_all_internal_bdts(self, work_dir, remove_archives = False):
        bhf_mode = CombinedArchiveExtractorMode.BHF
        bdt_extractor = CombinedArchiveExtractor(bhf_mode)
        for root, _, files in os.walk(work_dir):
            for file_name in files:
                extension = os.path.splitext(file_name)[1]
                if extension.endswith("bdt"):
                    bdt_file_path = os.path.join(work_dir, root, file_name)
                    bhf_file_path = ArchiveManager._get_bhf_path(bdt_file_path)
                    if not os.path.isfile(bhf_file_path):
                        print("Can't find BHF for", bdt_file_path)
                        continue
                    bdt_extractor.output_dir = os.path.dirname(bdt_file_path)
                    bdt_extractor.extract_archive(bhf_file_path, bdt_file_path)
                    if remove_archives:
                        os.remove(bdt_file_path)
                        os.remove(bhf_file_path)

    @staticmethod
    def _get_bhf_path(bdt_file_path):
        """ Get the path of the BHF file corresponding to that BDT file.

        The general case is that it's in the same directory, but for CHRTPFBDT
        the BHF file is located in a subdir named as the BDT file without
        extension.
        """
        bdt_dirname = os.path.dirname(bdt_file_path)
        bdt_name, bdt_ext = os.path.splitext(os.path.basename(bdt_file_path))
        bhf_full_name = bdt_name + bdt_ext[:-3] + "bhd"
        if bdt_ext == ".chrtpfbdt":
            bhf_dirname = os.path.join(bdt_dirname, bdt_name)
            bhf_file_path = os.path.join(bhf_dirname, bhf_full_name)
        else:
            bhf_file_path = os.path.join(bdt_dirname, bhf_full_name)
        return bhf_file_path

    def inflate_files(self, work_dir, remove_dcx = False):
        """ Inflate (= decompress) all DCX files in work_dir. """
        for root, _, files in os.walk(work_dir):
            for file_name in files:
                extension = os.path.splitext(file_name)[1]
                if extension == ".dcx":
                    full_path = os.path.join(root, file_name)
                    ArchiveManager._inflate_file(full_path)
                    if remove_dcx:
                        os.remove(full_path)

    @staticmethod
    def _inflate_file(dcx_file_path):
        dcx = CompressedPackage()
        dcx.load_file(dcx_file_path)
        inflated_file_path = os.path.splitext(dcx_file_path)[0]
        dcx.uncompress(inflated_file_path)
        if not os.path.splitext(inflated_file_path)[1]:
            file_names.rename_with_fitting_extension(inflated_file_path)

    def extract_all_bnds(self, work_dir, remove_bnd = False):
        for root, _, files in os.walk(work_dir):
            for file_name in files:
                if file_name.endswith("bnd"):
                    full_path = os.path.join(root, file_name)
                    ArchiveManager._extract_bnd(full_path, work_dir)
                    if remove_bnd:
                        os.remove(full_path)

    @staticmethod
    def _extract_bnd(bnd_file_path, output_dir):
        bnd = StandaloneArchive()
        bnd.load_file(bnd_file_path)
        bnd.extract_all_files(output_dir)
