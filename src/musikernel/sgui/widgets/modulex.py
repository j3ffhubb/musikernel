from . import _shared
from .control import *
from .modulex_settings import pydaw_modulex_settings
from sgui.lib.translate import _
from sgui.sgqt import *


MODULEX_CLIPBOARD = None
MODULEX_EFFECTS_LIST = [
    "Off",
    "LP2",
    "LP4",
    "HP2",
    "HP4",
    "BP2",
    "BP4",
    "Notch2",
    "Notch4",
    "EQ",
    "Distortion",
    "Comb Filter",
    "Amp/Pan",
    "Limiter",
    "Saturator",
    "Formant",
    "Chorus",
    "Glitch",
    "RingMod",
    "LoFi",
    "S/H",
    "LP-D/W",
    "HP-D/W",
    "Monofier",
    "LP<-->HP",
    "Growl Filter",
    "Screech LP",
    "Metal Comb",
    "Notch-D/W",
    "Foldback",
]

class pydaw_modulex_single:
    def __init__(
        self,
        a_title,
        a_port_k1,
        a_rel_callback,
        a_val_callback,
        a_port_dict=None,
        a_preset_mgr=None,
        a_knob_size=51,
    ):
        self.group_box = QGroupBox()
        self.group_box.contextMenuEvent = self.contextMenuEvent
        self.group_box.setObjectName("plugin_groupbox")
        if a_title is not None:
            self.group_box.setTitle(str(a_title))
        self.layout = QGridLayout()
        self.layout.setContentsMargins(3, 3, 3, 3)
        #self.layout.setAlignment(QtCore.Qt.AlignCenter)
        self.group_box.setLayout(self.layout)
        self.knobs = []
        for f_i in range(3):
            f_knob = pydaw_knob_control(
                a_knob_size,
                "",
                a_port_k1 + f_i,
                a_rel_callback,
                a_val_callback,
                0,
                127,
                64,
                a_port_dict=a_port_dict,
                a_preset_mgr=a_preset_mgr,
            )
            f_knob.add_to_grid_layout(self.layout, f_i)
            self.knobs.append(f_knob)
        self.combobox = pydaw_combobox_control(
            132,
            "Type",
            a_port_k1 + 3,
            a_rel_callback,
            a_val_callback,
            MODULEX_EFFECTS_LIST,
            a_port_dict=a_port_dict,
            a_preset_mgr=a_preset_mgr,
            a_default_index=0,
        )
        self.layout.addWidget(self.combobox.name_label, 0, 3)
        self.combobox.control.currentIndexChanged.connect(
            self.type_combobox_changed)
        self.layout.addWidget(self.combobox.control, 1, 3)

    def wheel_event(self, a_event=None):
        pass

    def disable_mousewheel(self):
        """ Mousewheel events cause problems with
            per-audio-item-fx because they rely on the mouse release event.
        """
        for knob in self.knobs:
            knob.control.wheelEvent = self.wheel_event
        self.combobox.control.wheelEvent = self.wheel_event

    def contextMenuEvent(self, a_event):
        f_menu = QMenu(self.group_box)
        f_copy_action = f_menu.addAction(_("Copy"))
        f_copy_action.triggered.connect(self.copy_settings)
        f_cut_action = f_menu.addAction(_("Cut"))
        f_cut_action.triggered.connect(self.cut_settings)
        f_paste_action = f_menu.addAction(_("Paste"))
        f_paste_action.triggered.connect(self.paste_settings)
        f_paste_and_copy_action = f_menu.addAction(_("Paste and Copy"))
        f_paste_and_copy_action.triggered.connect(self.paste_and_copy)
        f_menu.addAction(f_paste_and_copy_action)
        f_reset_action = f_menu.addAction(_("Reset"))
        f_reset_action.triggered.connect(self.reset_settings)
        f_menu.exec_(QCursor.pos())

    def copy_settings(self):
        global MODULEX_CLIPBOARD
        MODULEX_CLIPBOARD = self.get_class()

    def paste_and_copy(self):
        """ Copy the existing setting and then paste,
            for rearranging effects
        """
        self.paste_settings(True)

    def paste_settings(self, a_copy=False):
        global MODULEX_CLIPBOARD
        if MODULEX_CLIPBOARD is None:
            QMessageBox.warning(
                self.group_box,
                _("Error"),
                _("Nothing copied to clipboard"),
            )
        else:
            f_class = self.get_class()
            self.set_from_class(MODULEX_CLIPBOARD)
            self.update_all_values()
            if a_copy:
                MODULEX_CLIPBOARD = f_class

    def update_all_values(self):
        for f_knob in self.knobs:
            f_knob.control_value_changed(f_knob.get_value())
        self.combobox.control_value_changed(self.combobox.get_value())

    def cut_settings(self):
        self.copy_settings()
        self.reset_settings()

    def reset_settings(self):
        self.set_from_class(pydaw_modulex_settings(64, 64, 64, 0))
        self.update_all_values()

    def set_from_class(self, a_class):
        """ a_class is a pydaw_modulex_settings instance """
        self.knobs[0].set_value(a_class.knobs[0])
        self.knobs[1].set_value(a_class.knobs[1])
        self.knobs[2].set_value(a_class.knobs[2])
        self.combobox.set_value(a_class.fx_type)

    def get_class(self):
        """ return a pydaw_modulex_settings instance """
        return pydaw_modulex_settings(
            self.knobs[0].control.value(),
            self.knobs[1].control.value(),
            self.knobs[2].control.value(),
            self.combobox.control.currentIndex())

    def type_combobox_changed(self, a_val):
        if a_val == 0: #Off
            self.knobs[0].name_label.setText("")
            self.knobs[1].name_label.setText("")
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 1: #LP2
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 2: #LP4
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 3: #HP2
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 4: #HP4
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 5: #BP2
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 6: #BP4
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 7: #Notch2
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 8: #Notch4
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 9: #EQ
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("BW"))
            self.knobs[2].name_label.setText(_("Gain"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(1.0, 6.0)
            self.knobs[2].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[2].set_127_min_max(-24.0, 24.0)
            self.knobs[1].value_label.setText("")
        elif a_val == 10: #Distortion
            self.knobs[0].name_label.setText(_("Gain"))
            self.knobs[1].name_label.setText(_("D/W"))
            self.knobs[2].name_label.setText(_("Out"))
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_127_min_max(0.0, 48.0)
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[2].set_127_min_max(-30.0, 0.0)
        elif a_val == 11: #Comb Filter
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Amt"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 12: #Amp/Panner
            self.knobs[0].name_label.setText(_("Pan"))
            self.knobs[1].name_label.setText(_("Amp"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-40.0, 24.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 13: #Limiter
            self.knobs[0].name_label.setText(_("Thresh"))
            self.knobs[1].name_label.setText(_("Ceil"))
            self.knobs[2].name_label.setText(_("Rel"))
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_127_min_max(-30.0, 0.0)
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-12.0, -0.1)
            self.knobs[2].val_conversion = _shared.KC_127_ZERO_TO_X_INT
            self.knobs[2].set_127_min_max(50.0, 1500.0)
        elif a_val == 14: #Saturator
            self.knobs[0].name_label.setText(_("Gain"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText(_("Out"))
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_127_min_max(-12.0, 12.0)
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[2].set_127_min_max(-12.0, 12.0)
        elif a_val == 15: #Formant Filter
            self.knobs[0].name_label.setText(_("Vowel"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 16: #Chorus
            self.knobs[0].name_label.setText(_("Rate"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_127_min_max(0.3, 6.0)
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 17: #Glitch
            self.knobs[0].name_label.setText(_("Pitch"))
            self.knobs[1].name_label.setText(_("Glitch"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 18: #RingMod
            self.knobs[0].name_label.setText(_("Pitch"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 19: #LoFi
            self.knobs[0].name_label.setText(_("Bits"))
            self.knobs[1].name_label.setText("")
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_127_min_max(4.0, 16.0)
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 20: #Sample and Hold
            self.knobs[0].name_label.setText(_("Pitch"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 21: #LP2-Dry/Wet
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 22: #HP2-Dry/Wet
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 23: #Monofier
            self.knobs[0].name_label.setText(_("Pan"))
            self.knobs[1].name_label.setText(_("Amp"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 6.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 24: #LP<-->HP
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(("LP/HP"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 25: #Growl Filter
            self.knobs[0].name_label.setText(_("Vowel"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText(_("Type"))
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 26: #Screech LP
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 27: #Metal Comb
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Amt"))
            self.knobs[2].name_label.setText(_("Spread"))
            self.knobs[0].val_conversion = _shared.KC_NONE
            self.knobs[1].val_conversion = _shared.KC_NONE
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 28: #Notch4-Dry/Wet
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_127_PITCH
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 29: #Foldback Distortion
            self.knobs[0].name_label.setText(_("Thresh"))
            self.knobs[1].name_label.setText(_("Gain"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[0].set_127_min_max(-12.0, 0.0)
            self.knobs[1].val_conversion = _shared.KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(0.0, 12.0)
            self.knobs[2].val_conversion = _shared.KC_NONE
            self.knobs[2].value_label.setText("")

        self.knobs[0].set_value(self.knobs[0].control.value())
        self.knobs[1].set_value(self.knobs[1].control.value())
        self.knobs[2].set_value(self.knobs[2].control.value())


