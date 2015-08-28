import os

import dks_archives.file_types as file_types


RENAME_TEMPLATE = ".old_{}"
RENAME_MSG = ( "This file already exists. "
               "The older version has been renamed with a .old extension." )

def rename_older_versions(path):
    """ Rename possibly existing versions to ensure that at the end,
    there is no file at path. """
    version_counter = 0
    while os.path.isfile(path + RENAME_TEMPLATE.format(version_counter)):
        version_counter += 1
    os.rename(path, path + RENAME_TEMPLATE.format(version_counter))
    print(RENAME_MSG)


def rename_with_fitting_extension(path):
    with open(path, "rb") as file_to_rename:
        magic = file_to_rename.read(4)
    extension = file_types.get_dummy_extension_from_data(magic)
    new_name = os.path.splitext(path)[0] + "." + extension
    os.rename(path, new_name)
