from struct import Struct

from pyshgck.bin import read_cstring, read_struct
from solairelib.log import LOG


class ParamDef(object):

    CONST_ROWS_POSITION = 0x30
    CONST_ROW_SIZE      = 0xB0

    # uint32    file_size
    # uint16    rows_position (0x30)
    # uint16    unk1
    # uint16    num_fields
    # uint16    row_size (0xB0)
    # char[32]  name (padded with 0x20)
    # uint16    unk2 (0)
    # uint16    unk3 (0x68)
    HEADER_BIN = Struct("< IHHHH 32s HH")

    def __init__(self):
        self.name = ""
        self.num_fields = 0
        self.unk1 = 0
        self.unk2 = 0
        self.unk3 = 0
        self.fields = []

    def __str__(self):
        return "Table {} with {} fields".format(self.name, self.num_fields)

    def load(self, file_path):
        """ Load the paramdef file, return True on success. """
        try:
            with open(file_path, "rb") as paramdef_file:
                self._load_header(paramdef_file)
                self._load_fields(paramdef_file)
        except OSError as exc:
            LOG.error("Error reading '{}': {}".format(file_path, exc))
            return False
        return True

    def _load_header(self, paramdef_file):
        unpacked = read_struct(paramdef_file, self.HEADER_BIN)
        self.unk1       = unpacked[2]
        self.num_fields = unpacked[3]
        self.name       = unpacked[5].decode("utf8").rstrip("\x00\x20")
        self.unk2       = unpacked[6]
        self.unk3       = unpacked[7]
        assert ParamDef.CONST_ROWS_POSITION == unpacked[1]
        assert ParamDef.CONST_ROW_SIZE == unpacked[4]

    def _load_fields(self, paramdef_file):
        self.fields = [None] * self.num_fields
        for index in range(self.num_fields):
            field = ParamDefField()
            field.load(paramdef_file)
            self.fields[index] = field


class ParamDefField(object):

    # char[64]  name
    # char[8]   type1
    # char[8]   print_format
    # float     default_value
    # float     min_value
    # float     max_value
    # float     step
    # uint32    unk (1)
    # uint32    data_size
    # uint32    desc_position
    # char[32]  type2 (padded with 0x20)
    # char[32]  english_name (padded with 0x20)
    # uint32    ident
    BIN = Struct("< 64s 8s8s ffff III 32s32s I")

    TYPE_MAP = {
        "dummy8": Struct("<8s"),
        "f32":    Struct("<f"),
        "s8":     Struct("<b"),
        "s16":    Struct("<h"),
        "s32":    Struct("<i"),
        "u8":     Struct("<B"),
        "u16":    Struct("<H"),
        "u32":    Struct("<I")
    }

    def __init__(self):
        self.name = ""
        self.type1 = ""
        self.print_format = ""

        self.default_value = 0.0
        self.min_value = 0.0
        self.max_value = 0.0
        self.step = 0.0

        self.unk = 0
        self.data_size = 0

        self.desc_position = 0
        self.type2 = ""
        self.english_name = ""
        self.ident = 0

        self.description = ""
        self.bin = None

    def __str__(self):
        return "<{}> {} {}".format(
            self.type1, self.english_name, self.description
        )

    def load(self, paramdef_file):
        unpacked = read_struct(paramdef_file, self.BIN)
        self.name = unpacked[0].decode("shift_jis").rstrip("\x00")
        self.type1 = unpacked[1].decode("utf8").rstrip("\x00\x20")
        self.print_format = unpacked[2].decode("utf8").rstrip("\x00\x20")
        self.default_value = unpacked[3]
        self.min_value = unpacked[4]
        self.max_value = unpacked[5]
        self.step = unpacked[6]
        self.unk = unpacked[7]
        self.data_size = unpacked[8]
        self.desc_position = unpacked[9]
        self.type2 = unpacked[10].decode("utf8").rstrip("\x00\x20")
        self.english_name = unpacked[11].decode("utf8").rstrip("\x00\x20")
        self.ident = unpacked[12]
        self._load_description(paramdef_file)
        self._load_struct()

    def _load_description(self, paramdef_file):
        current_position = paramdef_file.tell()
        paramdef_file.seek(self.desc_position)
        self.description = read_cstring(paramdef_file).decode("shift_jis")
        paramdef_file.seek(current_position)

    def _load_struct(self):
        self.bin = self.TYPE_MAP.get(self.type1)
        if self.bin is None:
            LOG.error("Unknown type '{}', fallback to {} bytes".format(
                self.type1, self.data_size
            ))
            self.bin = Struct("<{}s".format(self.data_size))
