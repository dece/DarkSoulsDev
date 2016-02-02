import os
import shutil

from dks_archives.bnd import BndCreator
from dks_archives.bhd5 import Bhd5, Bhd5EntryRecord, Bhd5DataEntry
from dks_archives.dcx import Compressor
from dks_archives.hasher import hash_string


class FileInjector(object):

    def __init__(self, target_bdt):
        self.target_bdt = target_bdt
        self.bnd_creator = BndCreator()
        self.dcx_compressor = Compressor()

    def add_file_to_inject(self, file_to_inject, virtual_file_name):
        self.bnd_creator.add_file(file_to_inject, virtual_file_name)

    def inject(self):
        temp_bnd_path = self.target_bdt + ".injected.bnd"
        self.bnd_creator.create(temp_bnd_path)
        temp_dcx_path = temp_bnd_path + ".dcx"
        self.dcx_compressor.compress_file(temp_bnd_path, temp_dcx_path)

        dcx_offset, dcx_size = self._append_file_to_bdt(temp_dcx_path)
        self._update_archive_header(dcx_offset, dcx_size)

        # os.remove(temp_bnd_path)
        # os.remove(temp_dcx_path)
        self.bnd_creator.reset()

    def _append_file_to_bdt(self, new_file_path):
        with open(self.target_bdt, "ab") as bdt_file:
            bdt_file.seek(0, os.SEEK_END)
            FileInjector.pad_file(bdt_file, 16)
            new_file_offset = bdt_file.tell()

            with open(new_file_path, "rb") as file_to_append:
                shutil.copyfileobj(file_to_append, bdt_file)

            new_file_size = bdt_file.tell() - new_file_offset

        return new_file_offset, new_file_size

    def _update_archive_header(self, new_file_offset, new_file_size):
        bhd_path = os.path.splitext(self.target_bdt)[0] + ".bhd5"
        bhd = Bhd5()
        bhd.load_file(bhd_path)
        FileInjector._add_entry_and_record(new_file_offset, new_file_size, bhd)
        bhd.save_file(bhd_path)

    @staticmethod
    def _add_entry_and_record(file_offset, file_size, bhd):
        entry = FileInjector._create_bhd_entry("/dummy", file_offset, file_size)
        entry_offset = bhd.add_entry(entry)

        record = FileInjector._create_bhd_record(entry_offset)
        bhd.add_record(record)

    @staticmethod
    def _create_bhd_record(entries_offset):
        record = Bhd5EntryRecord()
        record.num_entries = 1
        record.entries_offset = entries_offset
        return record

    @staticmethod
    def _create_bhd_entry(name, size, offset):
        entry = Bhd5DataEntry()
        entry.hash = int(hash_string(name), 16)
        entry.size = size
        entry.offset = offset
        entry.unk = 0
        return entry

    @staticmethod
    def pad_file(file_object, padding):
        while file_object.tell() % padding != 0:
            file_object.write(b"\x00")





def main():
    file_injector = FileInjector("..\\Samples\\dvdbnd3.bdt")
    file_injector.add_file_to_inject(
        "..\\Samples\\face_m.bmp",
        "N:\\FRPG\\data\\FaceGen\\GameData\\face_m.bmp"
    )
    file_injector.inject()


if __name__ == '__main__':
    main()
