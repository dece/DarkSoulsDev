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


def pad_data(data, padding, start_at = 0):
    while (start_at + len(data)) % padding != 0:
        data += b"\x00"
    return data
