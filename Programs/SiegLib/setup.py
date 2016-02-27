from cx_Freeze import setup, Executable

BUILD_EXE_OPTIONS = {
    "packages": ["sieglib"],
    "include_files": ["resources"]
}


setup(
    name         = "SiegLib",
    version      = "0.3",
    description  = "Small standalone utilities to use SiegLib functions",
    author       = "Shgck",
    author_email = "shgck@pistache.land",
    url          = "https://gitlab.com/Shgck/dark-souls-dev",
    options      = { "build_exe": BUILD_EXE_OPTIONS },
    executables  = [ Executable("sieglib/main.py", targetName = "sieglib.exe") ]
)
