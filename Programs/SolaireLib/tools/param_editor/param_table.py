from PyQt5.QtWidgets import QTableView


class ParamTable(QTableView):

    def __init__(self, parent = None):
        super().__init__(parent)
