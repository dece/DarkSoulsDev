import unittest

from sieglib.bhd import BhdDataEntry


EXAMPLE_NAME = "/chr/c0000.anibnd.dcx"
EXAMPLE_HASH = 0xF8630FB1


class BhdTests(unittest.TestCase):

    def test_hash_name(self):
        self.assertEquals(BhdDataEntry.hash_name(EXAMPLE_NAME), EXAMPLE_HASH)


if __name__ == "__main__":
    unittest.main()
