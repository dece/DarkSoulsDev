import json
import os

from dks_archives.bdt_extractor import BdtExtractor, BdtExtractorMode
from dks_archives.bnd import Bnd
from dks_archives.dcx import Dcx
import dks_archives.file_names as file_names


class ArchiveManager(object):
    """ High-level archive extraction interface.

    This is not a BDT/BND/whatever parser but an interface managing these
    parsers, giving them the correct file lists, etc. It tries to ensure that
    no level of packaging/compression is left behind. If it fails to do so, it's
    a bug.
    """

    def __init__(self, resource_dir):
        self.resource_dir = resource_dir
        self.external_bdt_manager = None
        self.internal_bdt_manager = None
        self.file_inflater = None
        self.bnd_manager = None

    def full_extraction(self, data_dir, output_dir):
        """ Perform the most complete extraction/inflating of data possible. """
        self._prepare_extraction(data_dir, output_dir)
        self.external_bdt_manager.extract_all()
        self.file_inflater.inflate_files()
        self.bnd_manager.extract_all()
        self.bnd_manager.extract_all()
        self.internal_bdt_manager.extract_all()
        self.file_inflater.inflate_files()

    def _prepare_extraction(self, data_dir, output_dir):
        self.external_bdt_manager = \
                ExternalBdtManager(data_dir, self.resource_dir, output_dir)
        self.internal_bdt_manager = InternalBdtManager(output_dir, True)
        self.file_inflater = FileInflater(output_dir, True)
        self.bnd_manager = BndManager(output_dir, True)


class ExternalBdtManager(object):

    EXTERNAL_ARCHIVES_IDENT = [0, 1, 2, 3]

    def __init__(self, data_dir, resource_dir, output_dir):
        self.data_dir = data_dir
        self.output_dir = os.path.join(output_dir, file_names.RELATIVE_ROOT)
        self.hash_maps = {}
        self._load_hash_maps(resource_dir)

    def _load_hash_maps(self, resource_dir):
        for ident in ExternalBdtManager.EXTERNAL_ARCHIVES_IDENT:
            hash_map_file_name = "dvdbnd{}.hashmap.json".format(ident)
            hash_map_file_path = os.path.join(resource_dir, hash_map_file_name)
            with open(hash_map_file_path, "r") as hash_map_file:
                self.hash_maps[ident] = json.load(hash_map_file)

    def extract_all(self):
        """ Extract all files from external composed archive (dvdbnd). """
        bdt_extractor = BdtExtractor(BdtExtractorMode.BHD5)
        bdt_extractor.output_dir = self.output_dir

        for ident in ExternalBdtManager.EXTERNAL_ARCHIVES_IDENT:
            bhd_file_path, bdt_file_path = \
                    ExternalBdtManager.get_bdt_bhd5_paths(self.data_dir, ident)
            bdt_extractor.hash_map = self.hash_maps[ident]
            bdt_extractor.extract_archive(bhd_file_path, bdt_file_path)

    @staticmethod
    def get_bdt_bhd5_paths(data_dir, ident):
        bhd_file_name = "dvdbnd{}.bhd5".format(ident)
        bhd_file_path = os.path.join(data_dir, bhd_file_name)
        bdt_file_name = "dvdbnd{}.bdt".format(ident)
        bdt_file_path = os.path.join(data_dir, bdt_file_name)
        return bhd_file_path, bdt_file_path


class InternalBdtManager(object):

    def __init__(self, work_dir, remove_archives = False):
        self.work_dir = work_dir
        self.remove_archives = remove_archives
        self.extractor = BdtExtractor(BdtExtractorMode.BHF)

    def extract_all(self):
        for root, _, files in os.walk(self.work_dir):
            for file_name in files:
                if InternalBdtManager.is_bdt(file_name):
                    bdt_file_path = os.path.join(root, file_name)
                    self.extract_bdt(bdt_file_path)

    @staticmethod
    def is_bdt(file_name):
        return file_name.endswith("bdt")

    def extract_bdt(self, bdt_file_path):
        bhf_file_path = InternalBdtManager.get_bhf_path(bdt_file_path)
        if not os.path.isfile(bhf_file_path):
            print("Can't find BHF for", bdt_file_path)
            return
        self.extractor.output_dir = os.path.dirname(bdt_file_path)
        self.extractor.extract_archive(bhf_file_path, bdt_file_path)
        if self.remove_archives:
            os.remove(bdt_file_path)
            os.remove(bhf_file_path)

    @staticmethod
    def get_bhf_path(bdt_file_path):
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


class FileInflater(object):
    """ Decompress all DCX in a directory tree. """

    def __init__(self, work_dir, remove_dcx = False):
        self.work_dir = work_dir
        self.remove_dcx = remove_dcx

    def inflate_files(self):
        for root, _, files in os.walk(self.work_dir):
            for file_name in files:
                if FileInflater.is_dcx(file_name):
                    full_path = os.path.join(root, file_name)
                    FileInflater.inflate_file(full_path)
                    if self.remove_dcx:
                        os.remove(full_path)

    @staticmethod
    def is_dcx(file_name):
        extension = os.path.splitext(file_name)[1]
        return extension == ".dcx"

    @staticmethod
    def inflate_file(dcx_file_path):
        """ Decompress the file contained in the DCX, and name it with a proper
        extension if possible. """
        dcx = Dcx()
        dcx.load_file(dcx_file_path)
        inflated_file_path = os.path.splitext(dcx_file_path)[0]
        dcx.uncompress(inflated_file_path)
        if not os.path.splitext(inflated_file_path)[1]:
            file_names.rename_with_fitting_extension(inflated_file_path)


class BndManager(object):

    def __init__(self, work_dir, remove_bnd = False):
        self.work_dir = work_dir
        self.remove_bnd = remove_bnd

    def extract_all(self):
        for root, _, files in os.walk(self.work_dir):
            for file_name in files:
                if BndManager.is_bnd(file_name):
                    full_path = os.path.join(root, file_name)
                    BndManager.extract_bnd(full_path, self.work_dir)
                    if self.remove_bnd:
                        os.remove(full_path)

    @staticmethod
    def is_bnd(file_name):
        return file_name.endswith("bnd")

    @staticmethod
    def extract_bnd(bnd_file_path, output_dir):
        bnd = Bnd()
        bnd.load_file(bnd_file_path)
        bnd.extract_all_files(output_dir)
