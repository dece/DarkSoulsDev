""" Utilities to guess data types from magics. """

from enum import Enum


class FileType(Enum):

    UNKNOWN = 0
    BDT = 1
    BHD5 = 2
    BHF = 3
    DCX = 4
    BND = 5
    FEV = 6
    FSB = 7
    BJBO = 8


MAGICS = {
    b"BDF3": FileType.BDT,
    b"BHD5": FileType.BHD5,
    b"BHF3": FileType.BHF,
    b"DCX\x00": FileType.DCX,
    b"BND3": FileType.BND,
    b"FEV1": FileType.FEV,
    b"FSB4": FileType.FSB,
    b"BJBO": FileType.BJBO
}


def file_type_from_magic(magic):
    if magic in MAGICS:
        return MAGICS[magic]
    else:
        return FileType.UNKNOWN


DUMMY_EXTENSIONS = {
    FileType.UNKNOWN: "xxx",
    FileType.BDT: "bdt",
    FileType.BHD5: "bhd5",
    FileType.BHF: "bhf",
    FileType.DCX: "dcx",
    FileType.BND: "bnd",
    FileType.FEV: "fev",
    FileType.FSB: "fsb",
    FileType.BJBO: "bjbo"
}


def get_dummy_extension_from_data(magic):
    file_type = file_type_from_magic(magic)
    assert file_type in DUMMY_EXTENSIONS
    return DUMMY_EXTENSIONS[file_type]
