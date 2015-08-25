from struct import Struct
import zlib


DCX_MAGIC = 0x44435800
DCS_MAGIC = 0x44435300
DCP_MAGIC = 0x44435000
DCA_MAGIC = 0x44434100

HEADER_BIN = Struct(">6I")
SIZES_BIN = Struct(">3I")
PARAMETERS_BIN = Struct(">8I")  # that's one pissed off struct!
ZLIB_CONTAINER_BIN = Struct(">2I")


class CompressedPackage(object):
    """ BDT compressed entry parser. Contain infos of the DCX chunk. """

    def __init__(self):
        self.magic = 0
        # self.unk1 = 0
        self.dcs_offset = 0
        self.dcp_offset = 0
        # self.unk2 = 0
        # self.unk3 = 0
        self.sizes = None
        self.parameters = None
        self.zlib_container = None
        self.zlib_data = None

    def load_file(self, compressed_file_path):
        with open(compressed_file_path, "rb") as data_file:
            self._load_header(data_file)
            self._load_sizes(data_file)
            self._load_parameters(data_file)
            self._load_zlib_container(data_file)
            self._load_zlib_data(data_file)

    def _load_header(self, data_file):
        data_file.seek(0)
        data = data_file.read(HEADER_BIN.size)
        unpacked = HEADER_BIN.unpack(data)
        self.magic = unpacked[0]
        # self.unk1 = unpacked[1]
        self.dcs_offset = unpacked[2]
        self.dcp_offset = unpacked[3]
        # self.unk2 = unpacked[4]
        # self.unk3 = unpacked[5]
        assert self.magic == DCX_MAGIC

    def _load_sizes(self, data_file):
        sizes = CompressedPackageSizes()
        sizes.load_sizes(data_file, self.dcs_offset)
        self.sizes = sizes

    def _load_parameters(self, data_file):
        parameters = CompressedPackageParameters()
        parameters.load_parameters(data_file, self.dcp_offset)
        self.parameters = parameters

    def _load_zlib_container(self, data_file):
        dca_offset = self.dcp_offset + self.parameters.dca_offset
        zlib_container = CompressedPackageZlibContainer()
        zlib_container.load_infos(data_file, dca_offset)
        self.zlib_container = zlib_container

    def _load_zlib_data(self, data_file):
        zlib_offset = self._get_zlib_offset()
        data_file.seek(zlib_offset)
        zlib_data = data_file.read(self.sizes.compressed_size)
        self.zlib_data = zlib_data

    def uncompress(self, output_file_path):
        uncompressed = zlib.decompress(self.zlib_data)
        print("Decompressing file at", output_file_path)
        with open(output_file_path, "wb") as output_file:
            output_file.write(uncompressed)

    def _get_zlib_offset(self):
        dca_offset = self.dcp_offset + self.parameters.dca_offset
        zlib_offset = dca_offset + self.zlib_container.data_offset
        return zlib_offset


class CompressedPackageSizes(object):
    """ DCS chunk. """

    def __init__(self):
        self.magic = 0
        self.uncompressed_size = 0
        self.compressed_size = 0

    def load_sizes(self, data_file, dcs_offset):
        data_file.seek(dcs_offset)
        data = data_file.read(SIZES_BIN.size)
        unpacked = SIZES_BIN.unpack(data)
        self.magic = unpacked[0]
        self.uncompressed_size = unpacked[1]
        self.compressed_size = unpacked[2]
        assert self.magic == DCS_MAGIC


class CompressedPackageParameters(object):
    """ DCP chunk. """

    def __init__(self):
        self.magic = 0
        self.method = 0
        self.dca_offset = 0
        # self.unk1 = 0
        # self.unk2 = 0
        # self.unk3 = 0
        # self.unk4 = 0
        # self.unk5 = 0

    def load_parameters(self, data_file, dcp_offset):
        data_file.seek(dcp_offset)
        data = data_file.read(PARAMETERS_BIN.size)
        unpacked = PARAMETERS_BIN.unpack(data)
        self.magic = unpacked[0]
        self.method = unpacked[1]
        self.dca_offset = unpacked[2]
        # self.unk1 = unpacked[3]
        # self.unk2 = unpacked[4]
        # self.unk3 = unpacked[5]
        # self.unk4 = unpacked[6]
        # self.unk5 = unpacked[7]
        assert self.magic == DCP_MAGIC


class CompressedPackageZlibContainer(object):
    """ DCA chunk. """

    def __init__(self):
        self.magic = 0
        self.data_offset = 0

    def load_infos(self, data_file, dca_offset):
        data_file.seek(dca_offset)
        data = data_file.read(ZLIB_CONTAINER_BIN.size)
        unpacked = ZLIB_CONTAINER_BIN.unpack(data)
        self.magic = unpacked[0]
        self.data_offset = unpacked[1]
        assert self.magic == DCA_MAGIC
