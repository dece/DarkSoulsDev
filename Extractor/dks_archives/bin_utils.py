""" Utilities for parsing binary data. """


def read_string(data, offset):
    """ Read the 0-terminated string from data at position offset and return
    corresponding bytes object (terminator excluded). """
    string_bytes = b""
    while True:
        data.seek(offset)
        next_byte = data.read(1)
        if not next_byte or next_byte == b"\x00":
            break
        string_bytes += next_byte
        offset += 1
    return string_bytes


def pad_data(data, padding):
    missing_padding_size = padding - (len(data) % padding):
    data += missing_padding_size * b"\x00"
    return data
