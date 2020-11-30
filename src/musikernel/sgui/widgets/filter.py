from . import _shared
from .control import *
from sgui.lib.translate import _
from sgui.mkqt import *

class pydaw_filter_widget:
    def __init__(
        self,
        a_size,
        a_rel_callback,
        a_val_callback,
        a_port_dict,
        a_cutoff_port,
        a_res_port,
        a_type_port=None,
        a_label=_("Filter"),
        a_preset_mgr=None,
    ):
        self.groupbox = QGroupBox(str(a_label))
        self.groupbox.setObjectName("plugin_groupbox")
        self.layout = QGridLayout(self.groupbox)
        self.layout.setContentsMargins(3, 3, 3, 3)
        self.cutoff_knob = pydaw_knob_control(
            a_size,
            _("Cutoff"),
            a_cutoff_port,
            a_rel_callback,
            a_val_callback,
            20,
            124,
            124,
            _shared.KC_PITCH,
            a_port_dict,
            a_preset_mgr,
        )
        self.cutoff_knob.add_to_grid_layout(self.layout, 0)
        self.res_knob = pydaw_knob_control(
            a_size,
            _("Res"),
            a_res_port,
            a_rel_callback,
            a_val_callback,
            -300,
            0,
            -120,
            _shared.KC_TENTH,
            a_port_dict,
            a_preset_mgr,
        )
        self.res_knob.add_to_grid_layout(self.layout, 1)
        if a_type_port is not None:
            self.type_combobox = pydaw_combobox_control(
                90,
                _("Type"),
                a_type_port,
                a_rel_callback,
                a_val_callback,
                [
                    "LP2",
                    "LP4",
                    "HP2",
                    "HP4",
                    "BP2",
                    "BP4",
                    "Notch2",
                    "Notch4",
                    _("Off"),
                ],
                a_port_dict,
                a_preset_mgr=a_preset_mgr,
            )
            self.layout.addWidget(self.type_combobox.name_label, 0, 2)
            self.layout.addWidget(self.type_combobox.control, 1, 2)


