from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QStandardItem, QStandardItemModel

from solairelib.param.param import Param
from solairelib.param.paramdef import ParamDef


class ParamModel(QStandardItemModel):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.paramdef = None
        self.param = None

    def load(self, paramdef_path, param_path):
        self._load_paramdef(paramdef_path)
        self._load_param(param_path)

    def _load_paramdef(self, paramdef_path):
        self.paramdef = ParamDef()
        load_success = self.paramdef.load(paramdef_path)
        if not load_success:
            return

        self.setColumnCount(self.paramdef.num_fields)
        field_names = [field.english_name for field in self.paramdef.fields]
        self.setHorizontalHeaderLabels(field_names)

    def _load_param(self, param_path):
        self.param = Param()
        load_success = self.param.load(param_path, self.paramdef)
        if not load_success:
            return

        for row in self.param.rows:
            row_content = []
            for value, field in zip(row.data, self.paramdef.fields):
                item = QStandardItem()
                item.setEditable(False)
                item.setData(QVariant(value))
                row_content.append(item)
            self.appendRow(row_content)
