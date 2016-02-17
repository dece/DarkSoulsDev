import os
from struct import Struct
import zlib

from pyshgck.bin import read_struct
from sieglib.log import LOG


class Dcx(object):
    """ DCX parser. """

    MAGIC      = 0x44435800
    CONST_UNK1 = 0x00010000

    HEADER_BIN = Struct(">6I")

    def __init__(self, file_path = None):
        self.magic = self.MAGIC
        self.unk1 = self.CONST_UNK1
        self.dcs_offset = self.HEADER_BIN.size
        self.dcp_offset = self.dcs_offset + DcxSizes.SIZES_BIN.size
        self.unk2 = self.dcp_offset
        self.unk3 = self.dcp_offset + 0x8

        self.sizes = DcxSizes()
        self.parameters = DcxParameters()
        self.zlib_container = DcxZlibContainer()
        self.zlib_data = None

        if file_path:
            self.load(file_path)

    def load(self, file_path):
        """ Load a DCX file, return True on success. """
        try:
            with open(file_path, "rb") as dcx_file:
                self._load_header(dcx_file)
                self._load_content(dcx_file)
        except OSError as exc:
            LOG.error("Error reading '{}': {}".format(file_path, exc))
            return False
        return True

    def _load_header(self, dcx_file):
        dcx_file.seek(0)
        unpacked = read_struct(dcx_file, self.HEADER_BIN)
        self.magic        = unpacked[0]
        self.unk1         = unpacked[1]
        self.dcs_offset   = unpacked[2]
        self.dcp_offset   = unpacked[3]
        self.unk2         = unpacked[4]
        self.unk3         = unpacked[5]
        assert self.magic == self.MAGIC
        assert self.unk1 == self.CONST_UNK1
        assert self.dcs_offset == self.HEADER_BIN.size
        assert self.dcp_offset == self.dcs_offset + DcxSizes.SIZES_BIN.size
        assert self.unk2 == self.dcp_offset
        assert self.unk3 == self.dcp_offset + 0x8

    def _load_content(self, dcx_file):
        self.sizes.load(dcx_file, self.dcs_offset)
        self.parameters.load(dcx_file, self.dcp_offset)
        dca_offset = self.dcp_offset + self.parameters.dca_offset
        self.zlib_container.load(dcx_file, dca_offset)
        self._load_zlib_data(dcx_file, dca_offset)

    def _load_zlib_data(self, dcx_file, dca_offset):
        zlib_offset = dca_offset + self.zlib_container.data_offset
        dcx_file.seek(zlib_offset)
        zlib_data = dcx_file.read(self.sizes.compressed_size)
        self.zlib_data = zlib_data

    def save(self, output_path):
        """ Save the DCX file at output_path, return True on success. """
        try:
            with open(output_path, "wb") as dcx_file:
                self._save_header(dcx_file)
                self._save_content(dcx_file)
        except OSError as exc:
            LOG.error("Error writing '{}': {}".format(output_path, exc))
            return False
        return True

    def _save_header(self, file_object):
        data = self.HEADER_BIN.pack(
            self.magic, self.unk1, self.dcs_offset, self.dcp_offset,
            self.unk2, self.unk3
        )
        file_object.write(data)

    def _save_content(self, file_object):
        self.sizes.save(file_object)
        self.parameters.save(file_object)
        self.zlib_container.save(file_object)
        file_object.write(self.zlib_data)

    def load_decompressed(self, file_path):
        """ Compress the file content, import its content and update the
        different sizes variables. Return True on success and False if an error
        occured with zlib or the import. """
        try:
            with open(file_path, "rb") as file_to_compress:
                data = file_to_compress.read()
        except OSError as exc:
            LOG.error("Error reading '{}': {}".format(file_path, exc))
            return False

        try:
            self.zlib_data = zlib.compress(data, 9)
        except zlib.error as exc:
            LOG.error("Zlib error: {}".format(exc))
            return False

        file_size = os.stat(file_path).st_size
        self.sizes.uncompressed_size = file_size
        self.sizes.compressed_size = len(self.zlib_data)
        return True

    def save_decompressed(self, output_path):
        """ Save the decompressed content at output_path, return True on
        success and False if an error occured with zlib or the export. """
        try:
            decompressed = zlib.decompress(self.zlib_data)
        except zlib.error as exc:
            LOG.error("Zlib error: {}".format(exc))
            return False

        try:
            with open(output_path, "wb") as output_file:
                output_file.write(decompressed)
        except OSError as exc:
            LOG.error("Error writing '{}': {}".format(output_path, exc))
            return False

        return True


class DcxSizes(object):
    """ DCS chunk. """

    MAGIC = 0x44435300

    SIZES_BIN = Struct(">3I")

    def __init__(self):
        self.magic = self.MAGIC
        self.uncompressed_size = 0
        self.compressed_size = 0

    def load(self, dcx_file, dcs_offset):
        dcx_file.seek(dcs_offset)
        unpacked = read_struct(dcx_file, self.SIZES_BIN)
        self.magic             = unpacked[0]
        self.uncompressed_size = unpacked[1]
        self.compressed_size   = unpacked[2]
        assert self.magic == self.MAGIC

    def save(self, file_object):
        data = self.SIZES_BIN.pack(
            self.magic, self.uncompressed_size, self.compressed_size
        )
        file_object.write(data)


class DcxParameters(object):
    """ DCP chunk. """

    MAGIC      = 0x44435000
    METHOD     = b"DFLT"
    CONST_UNK1 = 0x09000000  # Compression level?
    CONST_UNK5 = 0x00010100  # Zlib version?

    PARAMETERS_BIN = Struct(">I4s6I")

    def __init__(self):
        self.magic = self.MAGIC
        self.method = self.METHOD
        self.dca_offset = self.PARAMETERS_BIN.size
        self.unk1 = self.CONST_UNK1
        self.unk2 = 0
        self.unk3 = 0
        self.unk4 = 0
        self.unk5 = self.CONST_UNK5

    def load(self, dcx_file, dcp_offset):
        dcx_file.seek(dcp_offset)
        unpacked = read_struct(dcx_file, self.PARAMETERS_BIN)
        self.magic      = unpacked[0]
        self.method     = unpacked[1]
        self.dca_offset = unpacked[2]
        self.unk1       = unpacked[3]
        self.unk2       = unpacked[4]
        self.unk3       = unpacked[5]
        self.unk4       = unpacked[6]
        self.unk5       = unpacked[7]
        assert self.magic == self.MAGIC
        assert self.method == self.METHOD
        assert self.dca_offset == self.PARAMETERS_BIN.size
        assert self.unk1 == self.CONST_UNK1
        assert self.unk2 == 0
        assert self.unk3 == 0
        assert self.unk4 == 0
        assert self.unk5 == self.CONST_UNK5

    def save(self, file_object):
        data = self.PARAMETERS_BIN.pack(
            self.magic, self.method, self.dca_offset,
            self.unk1, self.unk2, self.unk3, self.unk4, self.unk5
        )
        file_object.write(data)


class DcxZlibContainer(object):
    """ DCA chunk. """

    MAGIC        = 0x44434100
    CONST_OFFSET = 0x8

    ZLIB_CONTAINER_BIN = Struct(">2I")

    def __init__(self):
        self.magic = self.MAGIC
        self.data_offset = self.CONST_OFFSET

    def load(self, dcx_file, dca_offset):
        dcx_file.seek(dca_offset)
        unpacked = read_struct(dcx_file, self.ZLIB_CONTAINER_BIN)
        self.magic       = unpacked[0]
        self.data_offset = unpacked[1]
        assert self.magic == self.MAGIC
        assert self.data_offset == self.CONST_OFFSET

    def save(self, file_object):
        data = self.ZLIB_CONTAINER_BIN.pack(self.magic, self.data_offset)
        file_object.write(data)
