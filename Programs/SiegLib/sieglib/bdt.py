
class Bdt(object):
    """ Describe a BDT file. Do not load the whole file in memory as they can
    weight several GB, load a  """

    MAGIC      = 0x33464442  # BDF3
    FULL_MAGIC = b"\x42\x44\x46\x33\x30\x37\x44\x37\x52\x36" + b"\x00"*6

    def __init__(self):
        self.bdt_file = None
        self.opened = False

    def __del__(self):
        if self.opened:
            self.close()

    def open(self, file_path):
        self.bdt_file = open(file_path, "rb")
        self.opened = True

    def read_entry(self, position, size):
        assert self.opened
        self.bdt_file.seek(position)
        content = self.bdt_file.read(size)
        return content

    def close(self):
        self.bdt_file.close()
        self.opened = False
