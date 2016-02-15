import json
import os
import re

from sieglib.bdt import Bdt
from sieglib.bhd import Bhd, BhdHeader, BhdRecord, BhdDataEntry
from sieglib.dcx import Dcx
from sieglib.filelist import load_filelist
from sieglib.log import LOG
from pyshgck.time import time_it


class ExternalArchive(object):
    """ Combination of BHD and BDT. Contains methods to export files to the
    filesystem and to generate archives from a directory tree.

    An ExternalArchive object is unusable when instantiated; use the function
    'reset' to create an empty one, or the functions 'load' or 'import_files' to
    populate it.

    Attributes:
    - bhd: Bhd object
    - bdt: Bdt object
    - filelist: dict which maps hashes to the original string
    - records_map: dict which maps record indices to the file names they contain
    - decompressed_list: list of files that have been decompressed during the
        archive export; it's the decompressed name, i.e. w/o the .dcx extension
    """

    # Do not handle these files when crafting an archive.
    SPECIAL_FILE_TYPES     = (".json",)
    RECORDS_MAP_NAME       = "records.json"
    DECOMPRESSED_LIST_NAME = "decompressed.json"

    # Files without a known name are named by their uppercase hex hash.
    UNNAMED_FILE_RE = re.compile(r"[0-9A-F]{8}")

    def __init__(self):
        self.bhd = None
        self.bdt = None
        self.filelist = None
        self.records_map = None
        self.decompressed_list = None

    def reset(self):
        self.bhd = Bhd()
        self.bdt = Bdt()
        self.filelist = {}
        self.records_map = {}
        self.decompressed_list = []

    def load(self, bhd_name):
        self.reset()
        self.bhd.load(bhd_name)
        bdt_name = os.path.splitext(bhd_name)[0] + ".bdt"
        self.bdt.open(bdt_name)

    def load_filelist(self, hashmap_path):
        self.filelist = load_filelist(hashmap_path)

    def load_records_map(self, input_dir):
        """ Load the archive's records map that will be used to generate an
        archive with original record-to-entries map, return True on success. """
        map_path = os.path.join(input_dir, self.RECORDS_MAP_NAME)
        if not os.path.isfile(map_path):
            LOG.error("Records map file can't be found.")
            return False
        else:
            with open(map_path, "r") as records_map_file:
                self.records_map = json.load(records_map_file)
            return True

    def load_decompressed_list(self, input_dir):
        """ Load the list of files in that input dir that should be compressed
        before being imported in the archive. """
        list_path = os.path.join(input_dir, self.DECOMPRESSED_LIST_NAME)
        if not os.path.isfile(list_path):
            LOG.info("No decompressed file list found in the input dir.")
            return False
        else:
            with open(list_path, "r") as list_file:
                self.decompressed_list = json.load(list_file)
            LOG.info("Loaded decompressed file list.")
            return True

    def save_records_map(self, output_dir):
        """ Write the JSON map of records to their entries. """
        records_map_path = os.path.join(output_dir, self.RECORDS_MAP_NAME)
        with open(records_map_path, "w") as records_map_file:
            json.dump(self.records_map, records_map_file)

    def save_decompressed_list(self, output_dir):
        """ Write the JSON list of files (relative path) decompressed. """
        list_path = os.path.join(output_dir, self.DECOMPRESSED_LIST_NAME)
        with open(list_path, "w") as list_file:
            json.dump(self.decompressed_list, list_file)

    #------------------------------
    # Extraction
    #------------------------------

    @time_it(LOG)
    def export_all_files(self, output_dir, decompress = True):
        """ Export all files from the archive to a directory tree in output_dir
        and decompress (if decompress is True, which is default) DCX files. """
        self.records_map = {}
        self.decompressed_list = []
        for index_and_record in enumerate(self.bhd.records):
            self._export_record(index_and_record, output_dir, decompress)
        self.save_records_map(output_dir)
        self.save_decompressed_list(output_dir)

    def _export_record(self, index_and_record, output_dir, decompress):
        """ Export data entries of that record. """
        record_files = []

        index, record = index_and_record
        for entry in record.entries:
            rel_path = self.export_file(entry, output_dir)
            if not rel_path:
                continue
            record_files.append(rel_path)

            if decompress:
                base_rel_path, extension = os.path.splitext(rel_path)
                if extension == ".dcx":
                    joinable_rel_path = os.path.normpath(rel_path.lstrip("/"))
                    file_path = os.path.join(output_dir, joinable_rel_path)
                    success = ExternalArchive._decompress(file_path)
                    if success:
                        self.decompressed_list.append(base_rel_path)

        self.records_map[index] = record_files

    def export_file(self, entry, output_dir):
        """ Export the file corresponding to that BHD data entry, return the
        relative file path on success, None on failure """
        if not self.is_entry_valid(entry):
            LOG.error("Tried to extract a file not from this archive.")
            return None

        rel_path = self.filelist.get(entry.hash) or "{:08X}".format(entry.hash)
        LOG.info("Extracting {}".format(rel_path))

        file_content = self.bdt.read_entry(entry.offset, entry.size)
        content_len = len(file_content)
        if content_len != entry.size:
            LOG.error( "Tried to read {} bytes but only {} were available "
                       "(file '{}').".format(
                entry.size, content_len, rel_path
            ))
            return None

        output_path = os.path.join(output_dir, rel_path.lstrip("/"))
        if not os.path.isdir(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        with open(output_path, "wb") as output_file:
            output_file.write(file_content)
        return rel_path

    def is_entry_valid(self, entry):
        """ Return True if that BhdDataEntry is part of this archive. """
        for record in self.bhd.records:
            if entry in record.entries:
                return True
        return False

    @staticmethod
    def _decompress(file_path, remove_dcx = True):
        """ Decompress that file and remove the compressed original (DCX) if
        remove_dcx is True. Return True on success. """
        dcx = Dcx()
        import_success = dcx.load(file_path)
        if not import_success:
            return False

        decompressed_path = os.path.splitext(file_path)[0]  # remove the .dcx
        export_success = dcx.save_decompressed(decompressed_path)
        if not export_success:
            return False

        if remove_dcx:
            os.remove(file_path)
        return True

    #------------------------------
    # Import
    #------------------------------

    @time_it(LOG)
    def import_files(self, data_dir, bhd_path):
        """ Create an external archive from the data in data_dir, return True on
        success. """
        self.reset()
        self._prepare_import(data_dir, bhd_path)

        for root, _, files in os.walk(data_dir):
            for file_name in files:
                ext = os.path.splitext(file_name)[1]
                if ext in self.SPECIAL_FILE_TYPES:
                    continue
                self.import_file(data_dir, root, file_name)

        self._update_header()
        self._save_files(bhd_path)
        return True

    def _prepare_import(self, data_dir, bhd_path):
        """ Prepare and load some files used in the import process, return True
        if everything is ready or False if the import should be aborted. """
        # Open the BDR file in write mode and write basic data
        bdt_path = os.path.splitext(bhd_path)[0] + ".bdt"
        self.bdt.open(bdt_path, "wb")
        self.bdt.make_header()

        # Load the records to entries map and prepare the BHD record list.
        records_map_is_loaded = self.load_records_map(data_dir)
        if not records_map_is_loaded:
            return False
        num_records = len(self.records_map.keys())
        self.bhd.records = [BhdRecord() for _ in range(num_records)]

        # Load the list of files to compress
        self.load_decompressed_list(data_dir)

    def import_file(self, data_dir, file_dir, file_name):
        """ Try to import the file file_name in file_dir, with data_dir as the
        archive root; create a data entry in the appropriate record, and write
        the file data in the BDT file. Return True on success. """
        file_path = os.path.join(file_dir, file_name)

        # Find rel_path: either a hashable name like "/chr/c5352.anibnd.dcx"
        # or directly a hash name like "192E66A4".
        # Create a data entry hash with an appropriate value at the same time.
        is_unnamed = self.UNNAMED_FILE_RE.match(file_name) is not None
        if is_unnamed:
            rel_path = file_name
            entry_hash = int(file_name, 16)
        else:
            rel_path = ExternalArchive._get_rel_path(data_dir, file_path)
            rel_path = "/" + rel_path
            entry_hash = BhdDataEntry.hash_name(rel_path)
        LOG.info("Importing {}".format(rel_path))

        # If the file is in the decompressed list, it doesn't exist on the disk
        # yet and we have to create the DCX file first.
        if rel_path in self.decompressed_list:
            joinable_rel_path = os.path.normpath(rel_path.lstrip("/"))
            decompressed_path = os.path.join(data_dir, joinable_rel_path)
            success = ExternalArchive._compress(decompressed_path)
            if not success:
                return False
            rel_path = rel_path + ".dcx"
            file_path = file_path + ".dcx"

        import_results = self.bdt.import_file(file_path)
        if import_results[1] == -1:  # written bytes
            return False

        data_entry = BhdDataEntry()
        data_entry.hash = entry_hash
        data_entry.offset, data_entry.size = import_results

        record_is_updated = self._update_record(rel_path, data_entry)
        return record_is_updated

    @staticmethod
    def _get_rel_path(data_dir, file_path):
        """ Return the sanitized relative path of file_path. """
        relative_path = os.path.relpath(file_path, data_dir)
        # Invert backslashes on Windows.
        relative_path = relative_path.replace(os.path.sep, "/")
        return relative_path

    @staticmethod
    def _compress(file_path, remove_original = True):
        dcx = Dcx()
        import_success = dcx.load_decompressed(file_path)
        if not import_success:
            return False

        dcx_path = file_path + ".dcx"
        export_success = dcx.save(dcx_path)

        if remove_original:
            os.remove(file_path)
        return export_success

    def _update_record(self, rel_path, data_entry):
        """ Add the data entry to the record associated with that relative path,
        return True on success. """
        try:
            index = next(( int(index)
                           for index, files in self.records_map.items()
                           if rel_path in files ))
        except StopIteration:
            LOG.error("File {} not in any record.".format(rel_path))
            return False
        record = self.bhd.records[index]
        record.entries.append(data_entry)
        return True

    def _update_header(self):
        """ Update the BHD header with values corresponding to the amount of
        records and entries stored; the header is then ready to write. """
        self.bhd.header = BhdHeader()

        num_records = len(self.bhd.records)
        num_data_entries = sum( ( len(record.entries)
                                  for record in self.bhd.records ) )
        file_size = (
            BhdHeader.HEADER_BIN.size +
            BhdRecord.RECORD_BIN.size * num_records +
            BhdDataEntry.DATA_ENTRY_BIN.size * num_data_entries
        )

        self.bhd.header.file_size = file_size
        self.bhd.header.num_records = num_records

    def _save_files(self, bhd_path):
        """ Write both BHD and BDT files to disk. """
        LOG.info("Saving files to disk...")
        self.bhd.save(bhd_path)
        self.bdt.close()
