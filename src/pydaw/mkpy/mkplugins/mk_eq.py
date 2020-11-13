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

from mkpy.libpydaw.pydaw_widgets import *
from mkpy.libpydaw.translate import _


MKEQ_FIRST_CONTROL_PORT = 4
MKEQ_EQ1_FREQ = 4
MKEQ_EQ1_RES = 5
MKEQ_EQ1_GAIN = 6
MKEQ_EQ2_FREQ = 7
MKEQ_EQ2_RES = 8
MKEQ_EQ2_GAIN = 9
MKEQ_EQ3_FREQ = 10
MKEQ_EQ3_RES = 11
MKEQ_EQ3_GAIN = 12
MKEQ_EQ4_FREQ = 13
MKEQ_EQ4_RES = 14
MKEQ_EQ4_GAIN = 15
MKEQ_EQ5_FREQ = 16
MKEQ_EQ5_RES = 17
MKEQ_EQ5_GAIN = 18
MKEQ_EQ6_FREQ = 19
MKEQ_EQ6_RES = 20
MKEQ_EQ6_GAIN = 21
MKEQ_SPECTRUM_ENABLED = 22

MKEQ_PORT_MAP = {}


class mkeq_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, *args, **kwargs):
        pydaw_abstract_plugin_ui.__init__(self, *args, **kwargs)
        self._plugin_name = "MKEQ"
        self.is_instrument = False

        self.preset_manager = None
        self.spectrum_enabled = None

        self.layout.setSizeConstraint(QLayout.SetFixedSize)

        f_knob_size = 48

        self.eq6 = eq6_widget(
            MKEQ_EQ1_FREQ,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, a_preset_mgr=self.preset_manager,
            a_size=f_knob_size, a_vlayout=False)

        self.layout.addWidget(self.eq6.widget)

        self.spectrum_enabled = pydaw_null_control(
            MKEQ_SPECTRUM_ENABLED,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, self.port_dict)

        self.open_plugin_file()
        self.set_midi_learn(MKEQ_PORT_MAP)
        self.enable_spectrum(True)

    def open_plugin_file(self):
        pydaw_abstract_plugin_ui.open_plugin_file(self)
        self.eq6.update_viewer()

    def save_plugin_file(self):
        # Don't allow the spectrum analyzer to run at startup
        self.spectrum_enabled.set_value(0)
        pydaw_abstract_plugin_ui.save_plugin_file(self)

    def widget_close(self):
        self.enable_spectrum(False)
        pydaw_abstract_plugin_ui.widget_close(self)

    def widget_show(self):
        self.enable_spectrum(True)

    def enable_spectrum(self, a_enabled):
        if a_enabled:
            print("Enabling spectrum")
            self.plugin_val_callback(MKEQ_SPECTRUM_ENABLED, 1.0)
        else:
            print("Disabling spectrum")
            self.plugin_val_callback(MKEQ_SPECTRUM_ENABLED, 0.0)

    def ui_message(self, a_name, a_value):
        if a_name == "spectrum":
            self.eq6.set_spectrum(a_value)
        else:
            pydaw_abstract_plugin_ui.ui_message(a_name, a_value)

