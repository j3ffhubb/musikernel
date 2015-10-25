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


SREVERB_REVERB_TIME = 0
SREVERB_REVERB_WET = 1
SREVERB_REVERB_COLOR = 2
SREVERB_REVERB_DRY = 3
SREVERB_REVERB_PRE_DELAY = 4
SREVERB_REVERB_HP = 5


SREVERB_PORT_MAP = {
    "Reverb Wet": SREVERB_REVERB_WET,
    "Reverb Dry": SREVERB_REVERB_DRY,
    "Reverb LP": SREVERB_REVERB_COLOR,
    "Reverb HP": SREVERB_REVERB_HP,
}


class sreverb_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, a_val_callback, a_project,
                 a_folder, a_plugin_uid, a_track_name, a_stylesheet,
                 a_configure_callback, a_midi_learn_callback,
                 a_cc_map_callback):
        pydaw_abstract_plugin_ui.__init__(
            self, a_val_callback, a_project, a_plugin_uid, a_stylesheet,
            a_configure_callback, a_folder, a_midi_learn_callback,
            a_cc_map_callback)
        self._plugin_name = "SREVERB"
        self.set_window_title(a_track_name)
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

        self.reverb_groupbox = QGroupBox(_("Reverb"))
        self.reverb_groupbox.setObjectName("plugin_groupbox")
        self.reverb_groupbox_gridlayout = QGridLayout(
            self.reverb_groupbox)
        self.reverb_hlayout = QHBoxLayout()
        self.delay_vlayout.addLayout(self.reverb_hlayout)
        self.reverb_hlayout.addWidget(self.reverb_groupbox)
        self.reverb_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding))

        self.reverb_time_knob = pydaw_knob_control(
            f_knob_size, _("Size"), SREVERB_REVERB_TIME,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 50, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.reverb_time_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 3)

        self.reverb_dry_knob = pydaw_knob_control(
            f_knob_size, _("Dry"), SREVERB_REVERB_DRY,
            self.plugin_rel_callback, self.plugin_val_callback,
            -500, 0, 0, KC_TENTH, self.port_dict, self.preset_manager)
        self.reverb_dry_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 9)

        self.reverb_wet_knob = pydaw_knob_control(
            f_knob_size, _("Wet"), SREVERB_REVERB_WET,
            self.plugin_rel_callback, self.plugin_val_callback,
            -500, 0, -120, KC_TENTH, self.port_dict, self.preset_manager)
        self.reverb_wet_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 10)

        self.reverb_hp_knob = pydaw_knob_control(
            f_knob_size, _("HP"), SREVERB_REVERB_HP,
            self.plugin_rel_callback, self.plugin_val_callback,
            20, 96, 50, KC_PITCH, self.port_dict, self.preset_manager)
        self.reverb_hp_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 15)

        self.reverb_lp_knob = pydaw_knob_control(
            f_knob_size, _("LP"), SREVERB_REVERB_COLOR,
            self.plugin_rel_callback, self.plugin_val_callback,
            48, 120, 90, KC_PITCH, self.port_dict, self.preset_manager)
        self.reverb_lp_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 16)

        self.reverb_predelay_knob = pydaw_knob_control(
            f_knob_size, _("PreDelay"), SREVERB_REVERB_PRE_DELAY,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 1, KC_TIME_DECIMAL, self.port_dict, self.preset_manager)
        self.reverb_predelay_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 21)

        self.delay_spacer_layout = QVBoxLayout()
        self.delay_vlayout.addLayout(self.delay_spacer_layout)
        self.delay_spacer_layout.addItem(
            QSpacerItem(1, 1, vPolicy=QSizePolicy.Expanding))

        self.open_plugin_file()
        self.set_midi_learn(SREVERB_PORT_MAP)

    def open_plugin_file(self):
        pydaw_abstract_plugin_ui.open_plugin_file(self)

    def save_plugin_file(self):
        # Don't allow the spectrum analyzer to run at startup
        pydaw_abstract_plugin_ui.save_plugin_file(self)

    def set_window_title(self, a_track_name):
        self.track_name = str(a_track_name)
        self.widget.setWindowTitle(
            "Simple Reverb - {}".format(self.track_name))

    def widget_close_event(self, a_event):
        pydaw_abstract_plugin_ui.widget_close_event(self, a_event)

    def raise_widget(self):
        pydaw_abstract_plugin_ui.raise_widget(self)

    def ui_message(self, a_name, a_value):
        pydaw_abstract_plugin_ui.ui_message(a_name, a_value)


