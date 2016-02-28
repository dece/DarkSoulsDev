from struct import Struct

from pyshgck.bin import read_cstring, read_struct
from solairelib.log import LOG


class Param(object):

    # uint32    strings_position
    # uint32    rows_position
    # uint16    unk1
    # uint16    num_rows
    # char[32]  name (padded with 0x20)
    # uint32    unk2
    HEADER_BIN = Struct("< IIHH 32s I")

    def __init__(self):
        self.name = ""
        self.strings_position = 0
        self.rows_position = 0
        self.unk1 = 0
        self.num_rows = 0
        self.unk2 = 0

        self.rows = []

    def load(self, file_path, paramdef):
        """ Load the param file, return True on success. """
        try:
            with open(file_path, "rb") as param_file:
                self._load_header(param_file)
                self._load_rows(param_file, paramdef)
        except OSError as exc:
            LOG.error("Error reading '{}': {}".format(file_path, exc))
            return False
        return True

    def _load_header(self, param_file):
        unpacked = read_struct(param_file, self.HEADER_BIN)
        self.strings_position = unpacked[0]
        self.rows_position    = unpacked[1]
        self.unk1             = unpacked[2]
        self.num_rows         = unpacked[3]
        self.name             = unpacked[4].decode("utf8").rstrip("\x00\x20")
        self.unk2             = unpacked[5]

    def _load_rows(self, param_file, paramdef):
        self.rows = [None] * self.num_rows
        for index in range(self.num_rows):
            row = ParamRow()
            row.load(param_file, paramdef)
            self.rows[index] = row


class ParamRow(object):

    # uint32    id
    # uint32    data_position
    # uint32    string_position
    BIN = Struct("<3I")

    def __init__(self):
        self.ident = 0
        self.data_position = 0
        self.text_position = 0

        self.data = []
        self.text = ""

    def __str__(self):
        data =  "".join(["{:<20}".format(str(d)) for d in self.data])
        return data + " -- " + self.text

    def load(self, param_file, paramdef):
        unpacked = read_struct(param_file, self.BIN)
        self.ident           = unpacked[0]
        self.data_position   = unpacked[1]
        self.text_position = unpacked[2]
        self._load_data(param_file, paramdef)
        self._load_text(param_file)

    def _load_data(self, param_file, paramdef):
        current_position = param_file.tell()
        param_file.seek(self.data_position)

        self.data = [None] * paramdef.num_fields
        for index in range(paramdef.num_fields):
            field = paramdef.fields[index]
            self.data[index] = read_struct(param_file, field.bin)[0]

        param_file.seek(current_position)

    def _load_text(self, param_file):
        current_position = param_file.tell()
        param_file.seek(self.text_position)
        self.text = read_cstring(param_file).decode("shift_jis")
        param_file.seek(current_position)
