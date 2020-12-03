from sgui import glbl
from sgui.sgqt import *

class playback_widget:
    def __init__(self):
        self.play_button = QRadioButton()
        self.play_button.setObjectName("play_button")
        self.play_button.clicked.connect(glbl.TRANSPORT.on_play)
        self.stop_button = QRadioButton()
        self.stop_button.setChecked(True)
        self.stop_button.setObjectName("stop_button")
        self.stop_button.clicked.connect(glbl.TRANSPORT.on_stop)

