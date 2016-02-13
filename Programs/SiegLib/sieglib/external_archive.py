import json
import os

from sieglib.bdt import Bdt
from sieglib.bhd import Bhd
from sieglib.filelist import load_filelist
from sieglib.log import LOG
from pyshgck.time import time_it


class ExternalArchive(object):
    """ Combination of BHD and BDT. """

    def __init__(self):
        self.bhd = None
        self.bdt = None
        self.filelist = {}

    def reset(self):
        self.bhd = Bhd()
        self.bdt = Bdt()
        self.filelist = {}

    def load(self, bhd_name):
        self.reset()
        self.bhd.load(bhd_name)
        bdt_name = os.path.splitext(bhd_name)[0] + ".bdt"
        self.bdt.open(bdt_name)

    def load_filelist(self, hashmap_path):
        self.filelist = load_filelist(hashmap_path)

    @time_it(LOG)
    def extract_all_files(self, output_dir):
        records_map = {}
        for index, record in enumerate(self.bhd.records):
            record_files = []
            for entry in record.entries:
                file_name = self.extract_file(entry, output_dir)
                if file_name:
                    record_files.append(file_name)
            records_map[index] = record_files
        ExternalArchive._save_records_map(records_map, output_dir)

    @staticmethod
    def _save_records_map(records_map, output_dir):
        """ Write the JSON map of records to their entries. """
        records_map_path = os.path.join(output_dir, "records.json")
        with open(records_map_path, "w") as records_map_file:
            json.dump(records_map, records_map_file)

    def extract_file(self, entry, output_dir):
        """ Extract the file corresponding to that BHD data entry, return the
        relative file path on success, None on failure """
        if not self.is_entry_valid(entry):
            LOG.error("Tried to extract a file not from this archive.")
            return None

        file_name = self.filelist.get(entry.hash) or "{:08X}".format(entry.hash)
        LOG.info("Extracting {}".format(file_name))

        file_content = self.bdt.read_entry(entry.offset, entry.size)
        content_len = len(file_content)
        if content_len != entry.size:
            LOG.error( "Tried to read {} bytes but only {} were available "
                       "(file '{}')".format(
                entry.size, content_len, file_name
            ))
            return None

        output_path = os.path.join(output_dir, file_name.lstrip("/"))
        if not os.path.isdir(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        with open(output_path, "wb") as output_file:
            output_file.write(file_content)
        return file_name

    def is_entry_valid(self, entry):
        """ Return True if that BhdDataEntry is part of this archive. """
        for record in self.bhd.records:
            if entry in record.entries:
                return True
        return False

    def import_data_dir(self, data_dir):
        pass
