from fmodlib.fsb import Fsb4


def analyse_fsb(fsb_path):
    fsb = Fsb4()
    with open(fsb_path, "rb") as fsb_file:
        fsb.load(fsb_file)

    print(fsb)
    for sample_header in fsb.headers:
        print(sample_header)


FSB = r"F:\Dev\Projets\DarkSoulsDev\Workspace\sound\frpg_main.fsb"

analyse_fsb(FSB)
