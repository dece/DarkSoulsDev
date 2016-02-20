from enum import Enum
from struct import Struct

from pyshgck.bin import read_struct, pad_data
from pyshgck.format import hexlify


class FsbFlags(Enum):
    """ Flags used in FSB header or samples. See fsb.h for more infos. """

    LOOP_OFF      = 0x00000001
    LOOP_NORMAL   = 0x00000002
    LOOP_BIDI     = 0x00000004
    EIGHT_BITS    = 0x00000008
    SIXTEEN_BITS  = 0x00000010
    MONO          = 0x00000020
    STEREO        = 0x00000040
    UNSIGNED      = 0x00000080
    SIGNED        = 0x00000100
    DELTA         = 0x00000200
    IT214         = 0x00000400
    IT215         = 0x00000800
    HW3D          = 0x00001000
    TWO_DIM       = 0x00002000
    STREAMABLE    = 0x00004000
    LOADMEMORY    = 0x00008000
    LOADRAW       = 0x00010000
    MPEGACCURATE  = 0x00020000
    FORCEMONO     = 0x00040000
    HW2D          = 0x00080000
    ENABLEFX      = 0x00100000
    MPEGHALFRATE  = 0x00200000
    IMAADPCM      = 0x00400000
    VAG           = 0x00800000
    NONBLOCKING   = 0x01000000
    XMA           = 0x01000000
    GCADPCM       = 0x02000000
    MULTICHANNEL  = 0x04000000
    USECORE0      = 0x08000000
    USECORE1      = 0x10000000
    LOADMEMORYIOP = 0x20000000
    IGNORETAGS    = 0x40000000
    STREAM_NET    = 0x80000000


class Fsb4(object):

    MAGIC = b"FSB4"

    # char        magic[4]     'FSB4'
    # int32_t     num_samples  number of samples in the file
    # int32_t     shdr_size    size in bytes of all of the sample headers + ext.
    # int32_t     data_size    size in bytes of compressed sample data
    # uint32_t    version      extended fsb version
    # uint32_t    mode         flags that apply to all samples in the fsb
    # char        unk[8]       ???
    # uint8_t     hash[16]     hash???
    BIN = Struct("<4siiiII8s16s")

    def __init__(self):
        self.magic = self.MAGIC
        self.num_samples = 0
        self.shdr_size = 0
        self.data_size = 0
        self.version = 0
        self.mode = 0
        self.unk = b"\x00" * 8
        self.hash = b"\x00" * 16

        self.headers = []
        self.data_offset = 0

    def __str__(self):
        fmt = ( "Soundbank with {:08} samples"
                " -- headers {:08X} bytes, data {:08X} bytes"
                " -- version {:08X}, mode {:08X}"
                " -- unk {} -- hash {}" )
        return fmt.format(
            self.num_samples, self.shdr_size, self.data_size,
            self.version, self.mode, hexlify(self.unk), hexlify(self.hash)
        )

    def load(self, fsb_file):
        unpacked = read_struct(fsb_file, self.BIN)
        self.magic       = unpacked[0]
        self.num_samples = unpacked[1]
        self.shdr_size   = unpacked[2]
        self.data_size   = unpacked[3]
        self.version     = unpacked[4]
        self.mode        = unpacked[5]
        self.unk         = unpacked[6]
        self.hash        = unpacked[7]
        assert self.magic == self.MAGIC

        self._load_headers(fsb_file)
        self.data_offset = fsb_file.tell()

    def _load_headers(self, fsb_file):
        self.headers = [None] * self.num_samples
        for index in range(self.num_samples):
            sample_header = Fsb4SampleHeader()
            sample_header.load(fsb_file)
            self.headers[index] = sample_header

    def extract(self, output_dir):
        offset = self.data_offset
        for header in self.headers:
            base_path = os.path.join(output_dir, header.name_as_str)
            self._extract_sample(header, offset, base_path)

    def _extract_sample(self, header, base_path):
        try:
            header_path = base_path + ".header"
            with open(header_path, "wb") as header_file:
                header.save(header_file)
        except OSError as exc:
            LOG.error("Error writing sample header: {}".format(exc))
            return

        try:
            with open(base_path, "wb") as header_file:
                pass
        except OSError as exc:
            LOG.error("Error writing sample data: {}".format(exc))
            return

        


class Fsb4SampleHeader(object):

    # uint16_t    size
    # char        name[FSOUND_FSB_NAMELEN]  // 30
    #
    # uint32_t    samples_len
    # uint32_t    compressed_len
    # uint32_t    loop_start
    # uint32_t    loop_end
    #
    # uint32_t    mode
    # int32_t     def_freq
    # uint16_t    def_vol
    # int16_t     def_pan
    # uint16_t    def_pri
    # uint16_t    num_channels
    #
    # float       min_distance
    # float       max_distance
    # int32_t     var_freq
    # uint16_t    var_vol
    # int16_t     var_pan
    BIN = Struct("<H30s IIII IiHhHH ffiHh")

    def __init__(self):
        self.size = 0
        self.name = b""
        self.samples_len = 0
        self.compressed_len = 0
        self.loop_start = 0
        self.loop_end = 0
        self.mode = 0
        self.def_freq = 0
        self.def_vol = 0
        self.def_pan = 0
        self.def_pri = 0
        self.num_channels = 0
        self.min_distance = 0.0
        self.max_distance = 0.0
        self.var_freq = 0
        self.var_vol = 0
        self.var_pan = 0

    @property
    def name_as_str(self):
        name = self.name.rstrip(b"\x00")
        return name.decode("utf8", errors = "replace")
    @name_as_str.setter
    def name_as_str(self, str_value):
        bytes_value = str_value.encode("utf8", errors = "replace")
        self.name = pad_data(bytes_value, 30)

    def __str__(self):
        fmt = ( "Sample '{}' ({} bytes)"
                " -- size {} bytes ({} compressed)"
                " -- mode {:08X} -- {} channel(s)" )
        return fmt.format(
            self.name_as_str, self.size,
            self.samples_len, self.compressed_len,
            self.mode, self.num_channels
        )

    def load(self, fsb_file):
        unpacked = read_struct(fsb_file, self.BIN)
        self.size           = unpacked[0]
        self.name           = unpacked[1]
        self.samples_len    = unpacked[2]
        self.compressed_len = unpacked[3]
        self.loop_start     = unpacked[4]
        self.loop_end       = unpacked[5]
        self.mode           = unpacked[6]
        self.def_freq       = unpacked[7]
        self.def_vol        = unpacked[8]
        self.def_pan        = unpacked[9]
        self.def_pri        = unpacked[10]
        self.num_channels   = unpacked[11]
        self.min_distance   = unpacked[12]
        self.max_distance   = unpacked[13]
        self.var_freq       = unpacked[14]
        self.var_vol        = unpacked[15]
        self.var_pan        = unpacked[16]
