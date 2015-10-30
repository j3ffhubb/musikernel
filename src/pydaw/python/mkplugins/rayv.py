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


#Ray-V

RAYV_OUTPUT0 = 0
RAYV_OUTPUT1 = 1
RAYV_FIRST_CONTROL_PORT = 2
RAYV_ATTACK = 2
RAYV_DECAY = 3
RAYV_SUSTAIN = 4
RAYV_RELEASE = 5
RAYV_TIMBRE = 6
RAYV_RES = 7
RAYV_DIST = 8
RAYV_FILTER_ATTACK = 9
RAYV_FILTER_DECAY = 10
RAYV_FILTER_SUSTAIN = 11
RAYV_FILTER_RELEASE = 12
RAYV_NOISE_AMP = 13
RAYV_FILTER_ENV_AMT = 14
RAYV_DIST_WET = 15
RAYV_OSC1_TYPE = 16
RAYV_OSC1_PITCH = 17
RAYV_OSC1_TUNE = 18
RAYV_OSC1_VOLUME = 19
RAYV_OSC2_TYPE = 20
RAYV_OSC2_PITCH = 21
RAYV_OSC2_TUNE = 22
RAYV_OSC2_VOLUME = 23
RAYV_MASTER_VOLUME = 24
RAYV_MASTER_UNISON_VOICES = 25
RAYV_MASTER_UNISON_SPREAD = 26
RAYV_MASTER_GLIDE = 27
RAYV_MASTER_PITCHBEND_AMT = 28
RAYV_PITCH_ENV_TIME = 29
RAYV_PITCH_ENV_AMT = 30
RAYV_LFO_FREQ = 31
RAYV_LFO_TYPE = 32
RAYV_LFO_AMP = 33
RAYV_LFO_PITCH = 34
RAYV_LFO_FILTER = 35
RAYV_OSC_HARD_SYNC = 36
RAYV_RAMP_CURVE = 37
RAYV_FILTER_KEYTRK = 38
RAYV_MONO_MODE = 39
RAYV_LFO_PHASE = 40
RAYV_LFO_PITCH_FINE = 41
RAYV_ADSR_PREFX = 42
RAYV_MIN_NOTE = 43
RAYV_MAX_NOTE = 44
RAYV_MASTER_PITCH = 45
RAYV_ADSR_LIN_MAIN = 46


RAYV_PORT_MAP = {
    "Attack": "2",
    "Decay": "3",
    "Sustain": "4",
    "Release": "5",
    "Filter Cutoff": "6",
    "Res": "7",
    "Dist": "8",
    "Attack Filter": "9",
    "Decay Filter": "10",
    "Sustain Filter": "11",
    "Release Filter": "12",
    "Noise Amp": "13",
    "Filter Env Amt": "14",
    "Dist Wet": "15",
    "Master Glide": "27",
    "Pitch Env Time": "29",
    "Pitch Env Amt": "30",
    "LFO Freq": "31",
    "LFO Amp": "33",
    "LFO Pitch": "34",
    "LFO Pitch Fine": RAYV_LFO_PITCH_FINE,
    "LFO Filter": "35"
}


class rayv_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, a_val_callback, a_project,
                 a_folder, a_plugin_uid, a_track_name,
                 a_stylesheet, a_configure_callback, a_midi_learn_callback,
                 a_cc_map_callback):
        pydaw_abstract_plugin_ui.__init__(
            self, a_val_callback, a_project, a_plugin_uid, a_stylesheet,
            a_configure_callback, a_folder, a_midi_learn_callback,
            a_cc_map_callback)
        self._plugin_name = "RAYV"
        self.is_instrument = True
        f_osc_types = [_("Off"), _("Saw"), _("Square"), _("Triangle"),
                       _("Sine")]
        f_lfo_types = [_("Off"), _("Sine"), _("Triangle")]
        self.preset_manager = pydaw_preset_manager_widget(
            self.get_plugin_name())
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(3, 3, 3, 3)
        self.layout.addLayout(self.main_layout)
        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        self.hlayout0 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout0)
        self.hlayout0.addWidget(self.preset_manager.group_box)
        self.hlayout0.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding))
        f_logo_label = QLabel()
        f_pixmap = QPixmap(
            os.path.join(
                pydaw_util.INSTALL_PREFIX, "lib",
                pydaw_util.global_pydaw_version_string,
                "themes", "default", "rayv.png")
            ).scaled(120, 60, transformMode=QtCore.Qt.SmoothTransformation)
        f_logo_label.setMinimumSize(90, 30)
        f_logo_label.setPixmap(f_pixmap)
        f_knob_size = 55

        self.hlayout0.addWidget(f_logo_label)
        self.hlayout1 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout1)
        self.osc1 = pydaw_osc_widget(
            f_knob_size, RAYV_OSC1_PITCH,
            RAYV_OSC1_TUNE, RAYV_OSC1_VOLUME,
            RAYV_OSC1_TYPE, f_osc_types,
            self.plugin_rel_callback, self.plugin_val_callback,
            _("Oscillator 1"), self.port_dict,
            a_preset_mgr=self.preset_manager, a_default_type=1)
        self.hlayout1.addWidget(self.osc1.group_box)
        self.adsr_amp = pydaw_adsr_widget(
            f_knob_size, True, RAYV_ATTACK, RAYV_DECAY,
            RAYV_SUSTAIN, RAYV_RELEASE,
            _("ADSR Amp"), self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager,
            a_prefx_port=RAYV_ADSR_PREFX, a_knob_type=KC_LOG_TIME,
            a_lin_port=RAYV_ADSR_LIN_MAIN)
        self.hlayout1.addWidget(self.adsr_amp.groupbox)
        self.groupbox_distortion = QGroupBox(_("Distortion"))
        self.groupbox_distortion.setObjectName("plugin_groupbox")
        self.groupbox_distortion_layout = QGridLayout(
            self.groupbox_distortion)
        self.hlayout1.addWidget(self.groupbox_distortion)
        self.dist = pydaw_knob_control(
            f_knob_size, _("Gain"), RAYV_DIST,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 48, 15, KC_INTEGER, self.port_dict, self.preset_manager)
        self.dist.add_to_grid_layout(self.groupbox_distortion_layout, 0)
        self.dist_wet = pydaw_knob_control(
            f_knob_size, _("Wet"), RAYV_DIST_WET,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 0, KC_NONE, self.port_dict, self.preset_manager)
        self.dist_wet.add_to_grid_layout(self.groupbox_distortion_layout, 1)
        self.hlayout2 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout2)
        self.osc2 = pydaw_osc_widget(
            f_knob_size, RAYV_OSC2_PITCH,
            RAYV_OSC2_TUNE, RAYV_OSC2_VOLUME,
            RAYV_OSC2_TYPE, f_osc_types,
            self.plugin_rel_callback, self.plugin_val_callback,
            _("Oscillator 2"), self.port_dict, self.preset_manager)
        self.hlayout2.addWidget(self.osc2.group_box)
        self.sync_groupbox = QGroupBox(_("Sync"))
        self.sync_groupbox.setObjectName("plugin_groupbox")
        self.hlayout2.addWidget(self.sync_groupbox)
        self.sync_gridlayout = QGridLayout(self.sync_groupbox)
        self.sync_gridlayout.setContentsMargins(3, 3, 3, 3)
        self.hard_sync = pydaw_checkbox_control(
            "On", RAYV_OSC_HARD_SYNC,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager)
        self.hard_sync.control.setToolTip(
            _("Setting self hard sync's Osc1 to Osc2. Usually you "
            "would want to distort and pitchbend if this is enabled."))
        self.sync_gridlayout.addWidget(
            self.hard_sync.control, 1, 0, QtCore.Qt.AlignCenter)
        self.groupbox_noise = QGroupBox(_("Noise"))
        self.groupbox_noise.setObjectName("plugin_groupbox")
        self.noise_layout = QGridLayout(self.groupbox_noise)
        self.noise_layout.setContentsMargins(3, 3, 3, 3)
        self.hlayout2.addWidget(self.groupbox_noise)
        self.noise_amp = pydaw_knob_control(
            f_knob_size, _("Vol"), RAYV_NOISE_AMP,
            self.plugin_rel_callback, self.plugin_val_callback,
            -60, 0, -30, KC_INTEGER, self.port_dict, self.preset_manager)
        self.noise_amp.add_to_grid_layout(self.noise_layout, 0)
        self.adsr_filter = pydaw_adsr_widget(
            f_knob_size, False, RAYV_FILTER_ATTACK,
            RAYV_FILTER_DECAY, RAYV_FILTER_SUSTAIN,
            RAYV_FILTER_RELEASE, _("ADSR Filter"),
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager, a_knob_type=KC_LOG_TIME)
        self.hlayout2.addWidget(self.adsr_filter.groupbox)
        self.filter = pydaw_filter_widget(
            f_knob_size, self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, RAYV_TIMBRE, RAYV_RES,
            a_preset_mgr=self.preset_manager)
        self.hlayout2.addWidget(self.filter.groupbox)
        self.filter_env_amt = pydaw_knob_control(
            f_knob_size, _("Env Amt"), RAYV_FILTER_ENV_AMT,
            self.plugin_rel_callback, self.plugin_val_callback,
            -36, 36, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.filter_env_amt.add_to_grid_layout(self.filter.layout, 2)
        self.filter_keytrk = pydaw_knob_control(
            f_knob_size, _("KeyTrk"), RAYV_FILTER_KEYTRK,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 0, KC_NONE, self.port_dict, self.preset_manager)
        self.filter_keytrk.add_to_grid_layout(self.filter.layout, 3)
        self.hlayout3 = QHBoxLayout()
        self.main_layout.addLayout(self.hlayout3)
        self.master = pydaw_master_widget(
            f_knob_size, self.plugin_rel_callback, self.plugin_val_callback,
            RAYV_MASTER_VOLUME, RAYV_MASTER_GLIDE,
            RAYV_MASTER_PITCHBEND_AMT, self.port_dict, _("Master"),
            RAYV_MASTER_UNISON_VOICES,
            RAYV_MASTER_UNISON_SPREAD,
            self.preset_manager, a_poly_port=RAYV_MONO_MODE,
            a_min_note_port=RAYV_MIN_NOTE, a_max_note_port=RAYV_MAX_NOTE,
            a_pitch_port=RAYV_MASTER_PITCH)
        self.hlayout3.addWidget(self.master.group_box)

        self.pitch_env = pydaw_ramp_env_widget(
            f_knob_size, self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, RAYV_PITCH_ENV_TIME,
            RAYV_PITCH_ENV_AMT, _("Pitch Env"),
            self.preset_manager, RAYV_RAMP_CURVE)
        self.hlayout1.addWidget(self.pitch_env.groupbox)
        self.lfo = pydaw_lfo_widget(
            f_knob_size, self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, RAYV_LFO_FREQ,
            RAYV_LFO_TYPE, f_lfo_types, _("LFO"),
            self.preset_manager, RAYV_LFO_PHASE)
        self.hlayout3.addWidget(self.lfo.groupbox)

        self.lfo_amp = pydaw_knob_control(
            f_knob_size, _("Amp"), RAYV_LFO_AMP,
            self.plugin_rel_callback, self.plugin_val_callback,
            -24, 24, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.lfo_amp.add_to_grid_layout(self.lfo.layout, 7)
        self.lfo_pitch = pydaw_knob_control(
            f_knob_size, _("Pitch"), RAYV_LFO_PITCH,
            self.plugin_rel_callback, self.plugin_val_callback,
            -36, 36, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.lfo_pitch.add_to_grid_layout(self.lfo.layout, 8)

        self.lfo_pitch_fine = pydaw_knob_control(
            f_knob_size, _("Fine"), RAYV_LFO_PITCH_FINE,
            self.plugin_rel_callback, self.plugin_val_callback,
            -100, 100, 0, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.lfo_pitch_fine.add_to_grid_layout(self.lfo.layout, 9)

        self.lfo_cutoff = pydaw_knob_control(
            f_knob_size, _("Filter"), RAYV_LFO_FILTER,
            self.plugin_rel_callback, self.plugin_val_callback,
            -48, 48, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.lfo_cutoff.add_to_grid_layout(self.lfo.layout, 10)

        self.open_plugin_file()
        self.set_midi_learn(RAYV_PORT_MAP)


