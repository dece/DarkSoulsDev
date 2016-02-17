from sieglib.log import LOG


class Bdt(object):
    """ Describe a BDT file. Do not load the whole file in memory as they can
    weight several GB, just open the file in whatever mode you need. """

    MAGIC      = 0x33464442  # BDF3
    FULL_MAGIC = b"\x42\x44\x46\x33\x30\x37\x44\x37\x52\x36" + b"\x00"*6

    def __init__(self):
        self.bdt_file = None
        self.opened = False

    def __del__(self):
        if self.opened:
            self.close()

    def open(self, file_path, mode = "rb"):
        try:
            self.bdt_file = open(file_path, mode)
        except OSError as exc:
            LOG.error("Error opening {}: {}".format(file_path, exc))
            return
        self.opened = True

    def close(self):
        self.bdt_file.close()
        self.opened = False

    def read_entry(self, position, size):
        assert self.opened
        self.bdt_file.seek(position)
        content = self.bdt_file.read(size)
        return content

    def make_header(self):
        assert self.opened
        self.bdt_file.seek(0)
        self.bdt_file.write(Bdt.FULL_MAGIC)

    def import_file(self, file_path):
        position = self.bdt_file.tell()
        try:
            with open(file_path, "rb") as input_file:
                file_content = input_file.read()
            num_written = self.bdt_file.write(file_content)

            # Pad the BDT file to 16-byte if needed.
            end_position = position + num_written
            if end_position % 16 != 0:
                pad_size = 16 - (end_position % 16)
                self.bdt_file.write(b"\x00" * pad_size)
        except OSError as exc:
            LOG.error("Error importing {}: {}".format(
                file_path, exc
            ))
            return position, -1
        else:
            return position, num_written
