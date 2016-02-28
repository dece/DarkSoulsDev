import sys

from solairelib.param.param import Param
from solairelib.param.paramdef import ParamDef


MUH_DEF = ParamDef()
MUH_DEF.load(sys.argv[1])

MUH_DATA = Param()
MUH_DATA.load(sys.argv[2], MUH_DEF)

with open("solairelib.log", "w", encoding = "utf8") as log:
    log.write(str(MUH_DEF) + "\n")
    for field in MUH_DEF.fields:
        log.write("- " + str(field) + "\n")

    for row in MUH_DATA.rows:
        log.write("> " + str(row) + "\n")
