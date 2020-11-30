from . import _shared
from .control import *
from sgui.lib.translate import _
from sgui.mkqt import *


class pydaw_lfo_widget:
    def __init__(
        self,
        a_size,
        a_rel_callback,
        a_val_callback,
        a_port_dict,
        a_freq_port,
        a_type_port,
        a_type_list,
        a_label=_("LFO"),
        a_preset_mgr=None,
        a_phase_port=None,
    ):
        self.groupbox = QGroupBox(str(a_label))
        self.groupbox.setObjectName("plugin_groupbox")
        self.layout = QGridLayout(self.groupbox)
        self.layout.setContentsMargins(3, 3, 3, 3)
        self.freq_knob = pydaw_knob_control(
            a_size,
            _("Freq"),
            a_freq_port,
            a_rel_callback,
            a_val_callback,
            10,
            2100,
            200,
            _shared.KC_HZ_DECIMAL,
            a_port_dict,
            a_preset_mgr,
        )
        self.freq_knob.add_to_grid_layout(self.layout, 0)
        self.type_combobox = pydaw_combobox_control(
            120, _("Type"), a_type_port, a_rel_callback, a_val_callback,
            a_type_list, a_port_dict, 0, a_preset_mgr=a_preset_mgr)
        self.layout.addWidget(self.type_combobox.name_label, 0, 1)
        self.layout.addWidget(self.type_combobox.control, 1, 1)
        if a_phase_port:
            self.phase_knob = pydaw_knob_control(
                a_size, _("Phase"), a_phase_port,
                a_rel_callback, a_val_callback,
                0, 100, 0, _shared.KC_DECIMAL, a_port_dict, a_preset_mgr)
            self.phase_knob.add_to_grid_layout(self.layout, 2)

