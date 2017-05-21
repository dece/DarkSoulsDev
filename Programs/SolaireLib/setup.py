from distutils.core import setup


setup(
    name         = "SolaireLib",
    version      = "0.1",
    description  = "Format parsing library for Dark Souls",
    author       = "Shgck",
    author_email = "shgck@pistache.land",
    url          = "https://gitlab.com/Shgck/dark-souls-dev",
    packages     = [
        "solairelib",
        "solairelib.param"
    ]
)
