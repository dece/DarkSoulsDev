import os

from PyQt5.QtWidgets import *

from param_editor.param_model import ParamModel
from param_editor.param_table import ParamTable


class MainWindow(QMainWindow):

    WIDTH  = 800
    HEIGHT = 600
    TITLE  = "SolaireLib ParamEditor"

    def __init__(self, parent = None):
        super().__init__(parent)
        self.param_model = ParamModel(self)
        self.param_table = ParamTable(self)
        self.param_table.setModel(self.param_model)

        self.central_widget = None
        self._create_central_widget()

        self.resize(self.WIDTH, self.HEIGHT)
        self.setWindowTitle(self.TITLE)
        self.setCentralWidget(self.central_widget)

    def _create_central_widget(self):
        self.central_widget = QWidget()

        central_layout = QVBoxLayout()
        central_layout.addWidget(self.param_table)

        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout()
        load_file_button = QPushButton("Load file")
        load_file_button.pressed.connect(self.load_file)
        buttons_layout.addWidget(load_file_button)
        buttons_widget.setLayout(buttons_layout)
        central_layout.addWidget(buttons_widget)

        self.central_widget.setLayout(central_layout)

    def _open_file(self, title, ext_filter):
        return QFileDialog.getOpenFileName(self, title, "", ext_filter)[0]

    def load_file(self):
        paramdef_path = self._open_file( "Open param definition file"
                                       , "Param defs (*.paramdef)" )
        if not paramdef_path:
            return

        param_path = os.path.splitext(paramdef_path)[0] + ".param"
        if not os.path.isfile(param_path):
            param_path = self._open_file("Open param file", "Param (*.param)")
            if not param_path:
                return

        self._load_param_model(paramdef_path, param_path)

    def _load_param_model(self, paramdef_path, param_path):
        self.param_model.load(paramdef_path, param_path)
        self.param_table.resizeColumnsToContents()
