import os
from struct import Struct
import zlib

import dks_archives.file_names as file_names


DCX_MAGIC = 0x44435800
DCX_CONST_UNK1 = 0x00010000

DCS_MAGIC = 0x44435300

DCP_MAGIC = 0x44435000
DCP_METHOD = b"DFLT"
DCP_CONST_UNK5 = 0x00010100

DCA_MAGIC = 0x44434100
DCA_CONST_OFFSET = 0x8

HEADER_BIN = Struct(">6I")
SIZES_BIN = Struct(">3I")
PARAMETERS_BIN = Struct(">8I")  # that's one pissed off struct!
ZLIB_CONTAINER_BIN = Struct(">2I")


class CompressedPackage(object):
    """ BDT compressed entry parser. Contain infos of the DCX chunk. """

    def __init__(self):
        self.magic = 0
        self.unk1 = 0
        self.dcs_offset = 0
        self.dcp_offset = 0
        self.unk2 = 0
        self.unk3 = 0

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
        self.unk1 = unpacked[1]
        self.dcs_offset = unpacked[2]
        self.dcp_offset = unpacked[3]
        self.unk2 = unpacked[4]
        self.unk3 = unpacked[5]
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

    def _get_zlib_offset(self):
        dca_offset = self.dcp_offset + self.parameters.dca_offset
        zlib_offset = dca_offset + self.zlib_container.data_offset
        return zlib_offset

    def uncompress(self, output_file_path):
        uncompressed = zlib.decompress(self.zlib_data)
        print("Decompressing file at", output_file_path)
        if os.path.isfile(output_file_path):
            file_names.rename_older_versions(output_file_path)
        with open(output_file_path, "wb") as output_file:
            output_file.write(uncompressed)

    def compress(self, file_to_compress_path, remove_original = False):
        with open(file_to_compress_path, "rb") as file_to_compress:
            data = file_to_compress.read()
        if remove_original:
            os.remove(file_to_compress_path)
        self.zlib_data = zlib.compress(data)

    def save_file(self, output_path):
        header_data = self.pack_header()
        sizes_data = self.sizes.pack_sizes()
        params_data = self.parameters.pack_parameters()
        container_data = self.zlib_container.pack_infos()
        dcx_data = header_data + sizes_data + params_data + container_data
        with open(output_path, "wb") as output_file:
            output_file.write(dcx_data)
            output_file.write(self.zlib_data)

    def pack_header(self):
        data = ( self.magic, self.unk1, self.dcs_offset
               , self.dcp_offset, self.unk2, self.unk3 )
        return HEADER_BIN.pack(*data)


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

    def pack_sizes(self):
        data = (self.magic, self.uncompressed_size, self.compressed_size)
        return SIZES_BIN.pack(*data)


class CompressedPackageParameters(object):
    """ DCP chunk. """

    def __init__(self):
        self.magic = 0
        self.method = 0
        self.dca_offset = 0
        self.unk1 = 0
        self.unk2 = 0
        self.unk3 = 0
        self.unk4 = 0
        self.unk5 = 0

    def load_parameters(self, data_file, dcp_offset):
        data_file.seek(dcp_offset)
        data = data_file.read(PARAMETERS_BIN.size)
        unpacked = PARAMETERS_BIN.unpack(data)
        self.magic = unpacked[0]
        self.method = unpacked[1]
        self.dca_offset = unpacked[2]
        self.unk1 = unpacked[3]
        self.unk2 = unpacked[4]
        self.unk3 = unpacked[5]
        self.unk4 = unpacked[6]
        self.unk5 = unpacked[7]
        assert self.magic == DCP_MAGIC
        assert self.method == DCP_METHOD

    def pack_parameters(self):
        data = ( self.magic, self.method, self.dca_offset
               , self.unk1, self.unk2, self.unk3, self.unk4, self.unk5 )
        return PARAMETERS_BIN.pack(*data)


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

    def pack_infos(self):
        data = (self.magic, self.data_offset)
        return ZLIB_CONTAINER_BIN.pack(*data)


class Compressor(object):

    def __init__(self):
        self.dcx = CompressedPackage()

    def compress_file(self, file_to_compress):
        self._prepare_dcx()
        self.dcx.compress(file_to_compress)
        self._create_chunks(file_to_compress)

        output_path = file_to_compress + ".dcx"
        self.dcx.save_file(output_path)

    def _prepare_dcx(self):
        self.dcx.magic = DCX_MAGIC
        self.dcx.unk1 = DCX_CONST_UNK1
        self.dcx.dcs_offset = HEADER_BIN.size
        self.dcx.dcp_offset = self.dcx.dcs_offset + SIZES_BIN.size
        self.dcx.unk2 = self.dcx.dcp_offset
        self.dcx.unk3 = self.dcx.dcp_offset + 0x8

    def _create_chunks(self, original_file):
        self._create_sizes(original_file)
        self._create_params()
        self._create_zlib_container()

    def _create_sizes(self, uncompressed_file):
        """ Create a valid DCS chunk. """
        dcx_sizes = CompressedPackageSizes()
        dcx_sizes.magic = DCS_MAGIC
        dcx_sizes.uncompressed_size = os.stat(uncompressed_file).st_size
        dcx_sizes.compressed_size = len(self.dcx.zlib_data)
        self.dcx.sizes = dcx_sizes

    def _create_params(self):
        dcx_params = CompressedPackageParameters()
        dcx_params.magic = DCP_MAGIC
        dcx_params.method = DCP_METHOD
        dcx_params.dca_offset = PARAMETERS_BIN.size
        dcx_params.unk5 = DCP_CONST_UNK5
        self.dcx.parameters = dcx_params

    def _create_zlib_container(self):
        dcx_zlib_container = CompressedPackageZlibContainer()
        dcx_zlib_container.magic = DCA_MAGIC
        dcx_zlib_container.data_offset = DCA_CONST_OFFSET
        self.dcx.zlib_container = dcx_zlib_container
