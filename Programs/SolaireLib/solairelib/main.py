import sys

from solairelib.tpf import Tpf


MUH_TPF = Tpf()
MUH_TPF.load(sys.argv[1])
MUH_TPF.extract_textures(sys.argv[2])

