from . import _shared
from .control import *
from .note_selector import pydaw_note_selector_widget
from mkpy.libpydaw.translate import _
from mkpy.mkqt import *


class pydaw_master_widget:
    def __init__(
        self,
        a_size,
        a_rel_callback,
        a_val_callback,
        a_vol_port,
        a_glide_port,
        a_pitchbend_port,
        a_port_dict,
        a_title=_("Master"),
        a_uni_voices_port=None,
        a_uni_spread_port=None,
        a_preset_mgr=None,
        a_poly_port=None,
        a_min_note_port=None,
        a_max_note_port=None,
        a_pitch_port=None,
        a_pb_min=1,
    ):
        self.group_box = QGroupBox()
        self.group_box.setObjectName("plugin_groupbox")
        self.group_box.setTitle(str(a_title))
        self.layout = QGridLayout(self.group_box)
        self.layout.setContentsMargins(3, 3, 3, 3)
        self.vol_knob = pydaw_knob_control(
            a_size, _("Vol"), a_vol_port, a_rel_callback, a_val_callback, -30,
            12, -6, _shared.KC_INTEGER, a_port_dict, a_preset_mgr)
        self.vol_knob.add_to_grid_layout(self.layout, 0)
        if a_uni_voices_port is not None and a_uni_spread_port is not None:
            self.uni_voices_knob = pydaw_knob_control(
                a_size, _("Unison"), a_uni_voices_port,
                a_rel_callback, a_val_callback, 1, 7, 1, _shared.KC_INTEGER,
                a_port_dict, a_preset_mgr)
            self.uni_voices_knob.add_to_grid_layout(self.layout, 1)
            self.uni_spread_knob = pydaw_knob_control(
                a_size, _("Spread"), a_uni_spread_port,
                a_rel_callback, a_val_callback,
                10, 100, 50, _shared.KC_DECIMAL, a_port_dict, a_preset_mgr)
            self.uni_spread_knob.add_to_grid_layout(self.layout, 2)
        if a_pitch_port is not None:
            self.pitch_knob = pydaw_knob_control(
                a_size, _("Pitch"), a_pitch_port,
                a_rel_callback, a_val_callback,
                -36, 36, 0, _shared.KC_INTEGER, a_port_dict, a_preset_mgr)
            self.pitch_knob.add_to_grid_layout(self.layout, 4)
        self.glide_knob = pydaw_knob_control(
            a_size, _("Glide"), a_glide_port,
            a_rel_callback, a_val_callback,
            0, 200, 0, _shared.KC_TIME_DECIMAL, a_port_dict, a_preset_mgr)
        self.glide_knob.add_to_grid_layout(self.layout, 5)
        self.pb_knob = pydaw_knob_control(
            a_size, _("Pitchbend"), a_pitchbend_port,
            a_rel_callback, a_val_callback, a_pb_min, 36, 18,
            _shared.KC_INTEGER, a_port_dict, a_preset_mgr)
        self.pb_knob.add_to_grid_layout(self.layout, 6)
        if a_poly_port is not None:
            self.mono_combobox = pydaw_combobox_control(
                90, "Poly Mode", a_poly_port, a_rel_callback, a_val_callback,
                ["Retrig.", "Free", "Mono", "Mono2"],
                a_port_dict, 0, a_preset_mgr)
            self.mono_combobox.add_to_grid_layout(self.layout, 7)
        if a_min_note_port or a_max_note_port:
            assert(a_min_note_port and a_max_note_port)
            self.min_note = pydaw_note_selector_widget(
                a_min_note_port, a_rel_callback, a_val_callback, a_port_dict,
                0, a_preset_mgr)
            self.max_note = pydaw_note_selector_widget(
                a_max_note_port, a_rel_callback, a_val_callback, a_port_dict,
                120, a_preset_mgr)
            self.layout.addWidget(
                QLabel(_("Range")), 0, 9,
                alignment=QtCore.Qt.AlignHCenter)
            self.layout.addWidget(self.min_note.widget, 1, 9)
            self.layout.addWidget(self.max_note.widget, 2, 9)


