from .modulex import pydaw_modulex_single
from .modulex_settings import pydaw_modulex_settings
from mkpy.libpydaw.translate import _
from mkpy.mkqt import *


class pydaw_per_audio_item_fx_widget:
    def __init__(
        self,
        a_rel_callback,
        a_val_callback,
    ):
        self.effects = []
        self.widget = QWidget()
        self.widget.setObjectName("plugin_ui")
        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)
        f_port = 0
        for f_i in range(8):
            f_effect = pydaw_modulex_single(
                _("FX{}").format(f_i),
                f_port,
                a_rel_callback,
                a_val_callback,
            )
            f_effect.disable_mousewheel()
            self.effects.append(f_effect)
            self.layout.addWidget(f_effect.group_box)
            f_port += 4
        self.widget.setGeometry(0, 0, 348, 1100)  #ensure minimum size
        self.scroll_area = QScrollArea()
        self.scroll_area.setGeometry(0, 0, 360, 1120)
        self.scroll_area.setWidget(self.widget)

    def set_from_list(self, a_list):
        """ a_class is a pydaw_modulex_settings instance """
        for f_i in range(len(a_list)):
            self.effects[f_i].set_from_class(a_list[f_i])

    def get_list(self):
        """ return a list of pydaw_modulex_settings instances """
        f_result = []
        for f_effect in self.effects:
            f_result.append(f_effect.get_class())
        return f_result

    def clear_effects(self):
        for f_effect in self.effects:
            f_effect.combobox.set_value(0)
            for f_knob in f_effect.knobs:
                f_knob.set_value(64)

