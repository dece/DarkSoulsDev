import unittest

from sieglib.bhd import bhd_hash


EXAMPLE_NAME = "/chr/c0000.anibnd.dcx"
EXAMPLE_HASH = 0xF8630FB1


class BhdTests(unittest.TestCase):

    def test_bhd_hash(self):
        self.assertEquals(bhd_hash(EXAMPLE_NAME), EXAMPLE_HASH)


if __name__ == "__main__":
    unittest.main()
