from struct import Struct


BHD5_MAGIC = 0x35444842

HEADER_BIN = Struct("<6I")
ENTRY_RECORD_BIN = Struct("<2I")
DATA_ENTRY_BIN = Struct("<4I")


class CombinedInternalArchiveHeader(object):
    """ BHD5 parser. Some useless elements commented for performance. """

    def __init__(self):
        self.magic = 0
