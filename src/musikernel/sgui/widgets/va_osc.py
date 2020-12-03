from . import _shared
from .control import *
from sgui.lib.translate import _
from sgui.sgqt import *


class osc_widget:
    def __init__(
        self,
        a_size,
        a_pitch_port,
        a_fine_port,
        a_vol_port,
        a_type_port,
        a_osc_types_list,
        a_rel_callback,
        a_val_callback,
        a_label,
        a_port_dict=None,
        a_preset_mgr=None,
        a_default_type=0,
        a_uni_voices_port=None,
        a_uni_spread_port=None,
        a_pb_port=None,
    ):
        self.grid_layout = QGridLayout()
        self.group_box = QGroupBox(str(a_label))
        self.group_box.setObjectName("plugin_groupbox")
        self.group_box.setLayout(self.grid_layout)

        self.pitch_knob = knob_control(
            a_size, _("Pitch"), a_pitch_port,
            a_rel_callback, a_val_callback, -36, 36,
            0, a_val_conversion=_shared.KC_INT_PITCH, a_port_dict=a_port_dict,
            a_preset_mgr=a_preset_mgr)
        self.fine_knob = knob_control(
            a_size, _("Fine"), a_fine_port, a_rel_callback,
            a_val_callback, -100, 100, 0, a_val_conversion=_shared.KC_DECIMAL,
            a_port_dict=a_port_dict, a_preset_mgr=a_preset_mgr)

        self.pitch_knob.ratio_callback = self.fine_knob.set_value

        self.vol_knob = knob_control(
            a_size, _("Vol"), a_vol_port, a_rel_callback,
            a_val_callback, -30, 0, -6, a_val_conversion=_shared.KC_INTEGER,
            a_port_dict=a_port_dict, a_preset_mgr=a_preset_mgr)
        self.osc_type_combobox = combobox_control(
            100, _("Type"), a_type_port, a_rel_callback, a_val_callback,
            a_osc_types_list, a_port_dict, a_preset_mgr=a_preset_mgr,
            a_default_index=a_default_type)
        if a_uni_voices_port is not None and a_uni_spread_port is not None:
            self.uni_voices_knob = knob_control(
                a_size, _("Unison"), a_uni_voices_port,
                a_rel_callback, a_val_callback, 1, 7, 1, _shared.KC_INTEGER,
                a_port_dict, a_preset_mgr)
            self.uni_voices_knob.add_to_grid_layout(self.grid_layout, 10)
            self.uni_spread_knob = knob_control(
                a_size, _("Spread"), a_uni_spread_port,
                a_rel_callback, a_val_callback,
                10, 100, 50, _shared.KC_DECIMAL, a_port_dict, a_preset_mgr)
            self.uni_spread_knob.add_to_grid_layout(self.grid_layout, 11)
        if a_pb_port is not None:
            self.pb_knob = knob_control(
                a_size, _("PitchBnd"), a_pb_port,
                a_rel_callback, a_val_callback, -36, 36, 0, _shared.KC_INTEGER,
                a_port_dict, a_preset_mgr)
            self.pb_knob.add_to_grid_layout(self.grid_layout, 15)
        self.pitch_knob.add_to_grid_layout(self.grid_layout, 0)
        self.fine_knob.add_to_grid_layout(self.grid_layout, 1)
        self.vol_knob.add_to_grid_layout(self.grid_layout, 2)
        self.grid_layout.addWidget(self.osc_type_combobox.name_label, 0, 3)
        self.grid_layout.addWidget(self.osc_type_combobox.control, 1, 3)


