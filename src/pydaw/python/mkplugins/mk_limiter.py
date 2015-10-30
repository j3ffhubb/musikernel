# -*- coding: utf-8 -*-
"""
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

"""

from libpydaw.pydaw_widgets import *
from libpydaw.translate import _


MK_LIM_THRESHOLD = 0
MK_LIM_CEILING = 1
MK_LIM_RELEASE = 2
MK_LIM_UI_MSG_ENABLED = 3


MK_LIM_PORT_MAP = {}


class mk_lim_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, a_val_callback, a_project,
                 a_folder, a_plugin_uid, a_track_name, a_stylesheet,
                 a_configure_callback, a_midi_learn_callback,
                 a_cc_map_callback):
        pydaw_abstract_plugin_ui.__init__(
            self, a_val_callback, a_project, a_plugin_uid, a_stylesheet,
            a_configure_callback, a_folder, a_midi_learn_callback,
            a_cc_map_callback)
        self._plugin_name = "MK Limiter"
        self.is_instrument = False

        self.preset_manager = None
        self.layout.setSizeConstraint(QLayout.SetFixedSize)

        self.misc_tab = QWidget()
        self.layout.addWidget(self.misc_tab)
        self.delay_vlayout = QVBoxLayout()
        self.misc_tab.setLayout(self.delay_vlayout)
        self.delay_hlayout = QHBoxLayout()
        self.delay_vlayout.addLayout(self.delay_hlayout)

        f_knob_size = DEFAULT_KNOB_SIZE

        self.reverb_groupbox = QGroupBox("MK Limiter")
        self.reverb_groupbox.setObjectName("plugin_groupbox")
        self.groupbox_gridlayout = QGridLayout(
            self.reverb_groupbox)
        self.reverb_hlayout = QHBoxLayout()
        self.delay_vlayout.addLayout(self.reverb_hlayout)
        self.reverb_hlayout.addWidget(self.reverb_groupbox)
        self.reverb_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding))

        self.thresh_knob = pydaw_knob_control(
            f_knob_size, _("Thresh"), MK_LIM_THRESHOLD,
            self.plugin_rel_callback, self.plugin_val_callback,
            -360, 0, 0, KC_TENTH, self.port_dict, self.preset_manager)
        self.thresh_knob.add_to_grid_layout(self.groupbox_gridlayout, 3)

        self.ceiling_knob = pydaw_knob_control(
            f_knob_size, _("Ceiling"), MK_LIM_CEILING,
            self.plugin_rel_callback, self.plugin_val_callback,
            -180, 0, 0, KC_TENTH, self.port_dict, self.preset_manager)
        self.ceiling_knob.add_to_grid_layout(self.groupbox_gridlayout, 7)

        self.release_knob = pydaw_knob_control(
            f_knob_size, _("Release"), MK_LIM_RELEASE,
            self.plugin_rel_callback, self.plugin_val_callback,
            50, 1500, 500, KC_INTEGER, self.port_dict, self.preset_manager)
        self.release_knob.add_to_grid_layout(self.groupbox_gridlayout, 22)

        self.peak_meter = peak_meter(16, False)
        self.reverb_hlayout.addWidget(self.peak_meter.widget)

        self.delay_spacer_layout = QVBoxLayout()
        self.delay_vlayout.addLayout(self.delay_spacer_layout)
        self.delay_spacer_layout.addItem(
            QSpacerItem(1, 1, vPolicy=QSizePolicy.Expanding))

        self.ui_msg_enabled = pydaw_null_control(
            MK_LIM_UI_MSG_ENABLED,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, self.port_dict)

        self.open_plugin_file()
        self.set_midi_learn(MK_LIM_PORT_MAP)
        self.enable_ui_msg(True)

    def widget_close_event(self, a_event):
        self.enable_ui_msg(False)
        pydaw_abstract_plugin_ui.widget_close_event(self, a_event)

    def raise_widget(self):
        pydaw_abstract_plugin_ui.raise_widget(self)
        self.enable_ui_msg(True)

    def enable_ui_msg(self, a_enabled):
        if a_enabled:
            print("Enabling UI messages")
            self.plugin_val_callback(
                MK_LIM_UI_MSG_ENABLED, 1.0)
        else:
            print("Disabling UI messages")
            self.plugin_val_callback(
                MK_LIM_UI_MSG_ENABLED, 0.0)

    def ui_message(self, a_name, a_value):
        if a_name == "gain":
            self.peak_meter.set_value([a_value] * 2)
        else:
            pydaw_abstract_plugin_ui.ui_message(a_name, a_value)

    def save_plugin_file(self):
        # Don't allow the peak meter to run at startup
        self.ui_msg_enabled.set_value(0)
        pydaw_abstract_plugin_ui.save_plugin_file(self)

