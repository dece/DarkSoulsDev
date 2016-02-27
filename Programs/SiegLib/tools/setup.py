import os.path
import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
sys.path.append(os.path.abspath(".."))
BUILD_EXE_OPTIONS = { "packages": ["sieglib"] }

# GUI applications require a different base on Windows.
# The default is for a console application.
BASE = "Win32GUI" if sys.platform == "win32" else None


setup(
    name         = "SiegLib tools",
    description  = "Small standalone utilities to use SiegLib functions",
    author       = "Shgck",
    author_email = "shgck@pistache.land",
    url          = "https://gitlab.com/Shgck/dark-souls-dev",
    options      = { "build_exe": BUILD_EXE_OPTIONS },
    executables  = [
        Executable("bnd_tool.py", base = BASE),
        Executable("dcx_tool.py", base = BASE)
    ]
)
