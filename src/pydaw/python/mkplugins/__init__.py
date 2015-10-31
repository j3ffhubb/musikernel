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

import libmk

import sys
#avoid a circular import
libmk.mkplugins = sys.modules[__name__]

from libmk.mk_project import *
from libpydaw.translate import _
from libpydaw import pydaw_widgets

import mkplugins.euphoria
import mkplugins.rayv
import mkplugins.rayv2
import mkplugins.wayv
import mkplugins.modulex
import mkplugins.mk_channel
import mkplugins.mk_delay
import mkplugins.mk_eq
import mkplugins.simple_fader
import mkplugins.simple_reverb
import mkplugins.sidechain_comp
import mkplugins.trigger_fx
import mkplugins.xfade
import mkplugins.mk_compressor
import mkplugins.mk_vocoder
import mkplugins.mk_limiter

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from libpydaw.pydaw_util import pydaw_clip_value

PLUGIN_INSTRUMENT_COUNT = 3  # For inserting the split line into the menu

PLUGIN_NAMES = [
    "Euphoria", "Ray-V", "Ray-V 2", "Way-V", "MK Channel", "MK Compressor",
    "MK Delay", "MK EQ", "MK Limiter", "MK Vocoder", "Modulex",
    "Sidechain Comp.", "Simple Fader", "Simple Reverb", "TriggerFX",
    "X-Fade",
    ]

PLUGIN_UIDS = {
    "None":0, "Euphoria":1, "Ray-V":2, "Way-V":3, "Modulex":4, "MK Delay":5,
    "MK EQ":6, "Simple Fader":7, "Simple Reverb":8, "TriggerFX":9,
    "Sidechain Comp.":10, "MK Channel":11, "X-Fade":12, "MK Compressor":13,
    "MK Vocoder":14, "MK Limiter":15, "Ray-V 2": 16,
    }

PLUGINS_SYNTH = ["Ray-V", "Ray-V 2", "Way-V"]
PLUGINS_SAMPLER = ["Euphoria",]
PLUGINS_EFFECTS = ["Modulex", "MK Delay", "MK EQ", "Simple Reverb"]
PLUGINS_MIDI_TRIGGERED = ["TriggerFX"]
PLUGINS_DYNAMICS = ["MK Compressor", "MK Limiter"]
PLUGINS_SIDECHAIN = ["Sidechain Comp.", "X-Fade", "MK Vocoder",]
PLUGINS_MIXER = ["Simple Fader", "MK Channel"]

MAIN_PLUGIN_NAMES = [
    ("Synth", PLUGINS_SYNTH), ("Sampler", PLUGINS_SAMPLER),
    ("Effects", PLUGINS_EFFECTS),
    ("MIDI Triggered FX", PLUGINS_MIDI_TRIGGERED),
    ("Dynamics", PLUGINS_DYNAMICS), ("Sidechain", PLUGINS_SIDECHAIN),
    ("Mixer", PLUGINS_MIXER)
]

WAVE_EDITOR_PLUGIN_NAMES = [
    ("Effects", PLUGINS_EFFECTS), ("Dynamics", PLUGINS_DYNAMICS),
    ("Mixer", PLUGINS_MIXER)
]

MIXER_PLUGIN_NAMES = ["None"] + PLUGINS_MIXER
PLUGIN_UIDS_REVERSE = {v:k for k, v in PLUGIN_UIDS.items()}
CC_NAMES = {x:[] for x in PLUGIN_NAMES}
CONTROLLER_PORT_NAME_DICT = {x:{} for x in PLUGIN_NAMES}
CONTROLLER_PORT_NUM_DICT = {x:{} for x in PLUGIN_NAMES}

PLUGIN_UI_TYPES = {
    1:mkplugins.euphoria.euphoria_plugin_ui,
    2:mkplugins.rayv.rayv_plugin_ui,
    3:mkplugins.wayv.wayv_plugin_ui,
    4:mkplugins.modulex.modulex_plugin_ui,
    5:mkplugins.mk_delay.mkdelay_plugin_ui,
    6:mkplugins.mk_eq.mkeq_plugin_ui,
    7:mkplugins.simple_fader.sfader_plugin_ui,
    8:mkplugins.simple_reverb.sreverb_plugin_ui,
    9:mkplugins.trigger_fx.triggerfx_plugin_ui,
    10:mkplugins.sidechain_comp.scc_plugin_ui,
    11:mkplugins.mk_channel.mkchnl_plugin_ui,
    12:mkplugins.xfade.xfade_plugin_ui,
    13:mkplugins.mk_compressor.mk_comp_plugin_ui,
    14:mkplugins.mk_vocoder.mk_vocoder_plugin_ui,
    15:mkplugins.mk_limiter.mk_lim_plugin_ui,
    16:mkplugins.rayv2.rayv_plugin_ui,
}

PORTMAP_DICT = {
    "Euphoria":mkplugins.euphoria.EUPHORIA_PORT_MAP,
    "Way-V":mkplugins.wayv.WAYV_PORT_MAP,
    "Ray-V":mkplugins.rayv.RAYV_PORT_MAP,
    "Ray-V 2":mkplugins.rayv2.RAYV_PORT_MAP,
    "Modulex":mkplugins.modulex.MODULEX_PORT_MAP,
    "MK Channel":mkplugins.mk_channel.MKCHNL_PORT_MAP,
    "MK Compressor":mkplugins.mk_compressor.MK_COMP_PORT_MAP,
    "MK Delay":mkplugins.mk_delay.MKDELAY_PORT_MAP,
    "MK EQ":mkplugins.mk_eq.MKEQ_PORT_MAP,
    "Simple Fader":mkplugins.simple_fader.SFADER_PORT_MAP,
    "Simple Reverb":mkplugins.simple_reverb.SREVERB_PORT_MAP,
    "TriggerFX":mkplugins.trigger_fx.TRIGGERFX_PORT_MAP,
    "Sidechain Comp.":mkplugins.sidechain_comp.SCC_PORT_MAP,
    "X-Fade":mkplugins.xfade.XFADE_PORT_MAP,
    "MK Vocoder":mkplugins.mk_vocoder.MK_VOCODER_PORT_MAP,
    "MK Limiter":mkplugins.mk_limiter.MK_LIM_PORT_MAP,
}

def get_plugin_uid_by_name(a_name):
    return PLUGIN_UIDS[str(a_name)]

class pydaw_controller_map_item:
    def __init__(self, a_name, a_port):
        self.name = str(a_name)
        self.port = int(a_port)

def pydaw_load_controller_maps():
    for k, v in PORTMAP_DICT.items():
        for k2, v2 in v.items():
            f_map = pydaw_controller_map_item(k2, v2)
            CONTROLLER_PORT_NAME_DICT[k][k2] = f_map
            CONTROLLER_PORT_NUM_DICT[k][int(v2)] = f_map
            CC_NAMES[k].append(k2)
        CC_NAMES[k].sort()

pydaw_load_controller_maps()

def pydaw_center_widget_on_screen(a_widget):
    f_desktop_center = QApplication.desktop().screen().rect().center()
    f_widget_center = a_widget.rect().center()
    f_x = pydaw_clip_value(f_desktop_center.x() - f_widget_center.x(), 0, 300)
    f_y = pydaw_clip_value(f_desktop_center.y() - f_widget_center.y(), 0, 200)
    a_widget.move(f_x, f_y)

class mk_plugin_ui_dict:
    def __init__(self, a_project, a_ipc, a_stylesheet):
        """ a_project:    libmk.AbstractProject
            a_ipc:        libmk.AbstractIPC
            a_stylesheet: Qt-CSS string
        """
        self.ui_dict = {}
        self.midi_learn_control = None
        self.ctrl_update_callback = a_ipc.pydaw_update_plugin_control
        self.project = a_project
        self.plugin_pool_dir = a_project.plugin_pool_folder
        self.stylesheet = a_stylesheet
        self.configure_callback = a_ipc.pydaw_configure_plugin
        self.midi_learn_osc_callback = a_ipc.pydaw_midi_learn
        self.load_cc_map_callback = a_ipc.pydaw_load_cc_map

    def __contains__(self, a_plugin_uid):
        return a_plugin_uid in self.ui_dict

    def __getitem__(self, a_plugin_uid):
        return self.ui_dict[a_plugin_uid]

    def open_plugin_ui(
            self, a_plugin_uid, a_plugin_type, a_show=False, a_is_mixer=False):
        if not a_plugin_uid in self.ui_dict:
            f_plugin = PLUGIN_UI_TYPES[a_plugin_type](
                self.ctrl_update_callback, self.project, a_plugin_uid,
                self.stylesheet, self.configure_callback, self.plugin_pool_dir,
                self.midi_learn_callback, self.load_cc_map_callback,
                a_is_mixer)
            pydaw_center_widget_on_screen(f_plugin.widget)
            self.ui_dict[a_plugin_uid] = f_plugin
            if a_show:
                assert False, "This code path should be deprecated"
            else:
                return f_plugin
        else:
            if not a_show:
                return self.ui_dict[a_plugin_uid]
            if self.ui_dict[a_plugin_uid].widget.isHidden():
                self.ui_dict[a_plugin_uid].widget.show()
            self.ui_dict[a_plugin_uid].raise_widget()

    def midi_learn_callback(self, a_plugin, a_control):
        self.midi_learn_control = (a_plugin, a_control)
        self.midi_learn_osc_callback()

    def close_plugin_ui(self, a_track_num):
        f_track_num = int(a_track_num)
        if f_track_num in self.ui_dict:
            self.ui_dict[f_track_num].widget.close()
            self.ui_dict.pop(f_track_num)

    def hide_plugin_ui(self, a_track_num):
        f_track_num = int(a_track_num)
        if f_track_num in self.ui_dict:
            f_widget = self.ui_dict[f_track_num].widget
            f_widget.hide()

    def close_all_plugin_windows(self):
        for v in list(self.ui_dict.values()):
            v.is_quitting = True
            v.widget.close()
        self.ui_dict = {}

    def save_all_plugin_state(self):
        for v in list(self.ui_dict.values()):
            v.save_plugin_file()

PLUGIN_SETTINGS_COPY_OBJ = None
PLUGIN_SETTINGS_IS_CUT = False

class PluginComboBox(QPushButton):
    def __init__(self, a_callback):
        self.callback = a_callback
        QPushButton.__init__(self, _("None"))
        self.setObjectName("plugin_menu")
        self.menu = QMenu()
        self.setMenu(self.menu)
        f_action = self.menu.addAction("None")
        f_action.plugin_name = "None"
        self._index = 0
        self.menu.triggered.connect(self.action_triggered)

    def currentIndex(self):
        return self._index

    def currentText(self):
        return PLUGIN_UIDS_REVERSE[self._index]

    def setCurrentIndex(self, a_index):
        a_index = int(a_index)
        self._index = a_index
        self.setText(PLUGIN_UIDS_REVERSE[a_index])

    def action_triggered(self, a_val):
        a_val = a_val.plugin_name
        self._index = PLUGIN_UIDS[a_val]
        self.setText(a_val)
        self.callback()

    def addItems(self, a_items):
        for k, v in a_items:
            f_menu = self.menu.addMenu(k)
            for f_name in v:
                f_action = f_menu.addAction(f_name)
                f_action.plugin_name = f_name


class AbstractPluginSettings:
    def __init__(
            self, a_set_plugin_func, a_index, a_track_num,
            a_save_callback, a_qcbox=False, a_is_mixer=False):
        self.is_mixer = a_is_mixer
        self.plugin_ui = None
        self.set_plugin_func = a_set_plugin_func
        self.vlayout = QVBoxLayout()
        self.suppress_osc = False
        self.save_callback = a_save_callback
        self.plugin_uid = -1
        self.track_num = a_track_num
        self.index = a_index
        self.plugin_index = None
        # Qt 5.5.0 completely breaks PluginComboBox's use of QMenu,
        # so not using it for now, unfortunately.
        self.qcbox = a_qcbox
        if a_qcbox or True:
            self.plugin_combobox = QComboBox()
        else:
            self.plugin_combobox = PluginComboBox(self.on_plugin_change)
        self.plugin_combobox.setMinimumWidth(150)
        self.plugin_combobox.wheelEvent = self.wheel_event
        if a_qcbox:
            self.plugin_combobox.addItems(self.plugin_list)
        else:
            self.plugin_combobox.addItems(["None"])
            self.plugin_combobox.addItems(
                y for x in self.plugin_list for y in x[1])
        if a_qcbox or True:
            self.plugin_combobox.currentIndexChanged.connect(
                self.on_plugin_change)

        self.power_checkbox = QCheckBox("Power")
        self.power_checkbox.setChecked(True)
        if a_is_mixer:
            self.vlayout.addWidget(self.plugin_combobox)
            self.vlayout.setAlignment(self.plugin_combobox, QtCore.Qt.AlignTop)
        else:
            self.controls_widget = QWidget()
            self.controls_widget.setObjectName("plugin_rack")
            self.layout = QHBoxLayout(self.controls_widget)
            self.layout.addWidget(QLabel(_("Plugin")))
            self.vlayout.addWidget(self.controls_widget)
            self.layout.addWidget(self.plugin_combobox)
            self.power_checkbox.clicked.connect(self.on_power_changed)
            self.layout.addWidget(self.power_checkbox)

    def clear(self):
        self.set_value(libmk.pydaw_track_plugin(self.index, 0, -1))
        self.on_plugin_change()

    def copy(self):
        global PLUGIN_SETTINGS_COPY_OBJ
        PLUGIN_SETTINGS_COPY_OBJ = self.get_value()

    def cut(self):
        global PLUGIN_SETTINGS_IS_CUT
        PLUGIN_SETTINGS_IS_CUT = True
        self.copy()
        libmk.PLUGIN_UI_DICT.hide_plugin_ui(self.plugin_uid)
        self.plugin_combobox.setCurrentIndex(0)

    def paste(self):
        if PLUGIN_SETTINGS_COPY_OBJ is None:
            return
        self.set_value(PLUGIN_SETTINGS_COPY_OBJ)
        global PLUGIN_SETTINGS_IS_CUT
        if PLUGIN_SETTINGS_IS_CUT:
            PLUGIN_SETTINGS_IS_CUT = False
        else:
            self.plugin_uid = libmk.PROJECT.get_next_plugin_uid()
            libmk.PROJECT.copy_plugin(
                PLUGIN_SETTINGS_COPY_OBJ.plugin_uid, self.plugin_uid)
        self.on_plugin_change()

    def set_value(self, a_val):
        self.suppress_osc = True
        # More Qt 5.5.0 regression work-around
        if self.qcbox:
            self.plugin_combobox.setCurrentIndex(a_val.plugin_index)
        else:
            f_name = PLUGIN_UIDS_REVERSE[a_val.plugin_index]
            self.plugin_combobox.setCurrentIndex(
                self.plugin_combobox.findText(f_name))
        self.plugin_index = a_val.plugin_index

        self.plugin_uid = a_val.plugin_uid
        self.power_checkbox.setChecked(a_val.power == 1)
        self.on_show_ui()
        self.suppress_osc = False

    def get_value(self):
        return libmk.pydaw_track_plugin(
            self.index, get_plugin_uid_by_name(
                self.plugin_combobox.currentText()),
            self.plugin_uid,
            a_power=1 if self.power_checkbox.isChecked() else 0)

    def on_plugin_change(self, a_val=None, a_save=True):
        if self.suppress_osc:
            return
        f_index = get_plugin_uid_by_name(self.plugin_combobox.currentText())
        if f_index == 0:
            libmk.PLUGIN_UI_DICT.close_plugin_ui(self.plugin_uid)
            self.plugin_uid = -1
        elif self.plugin_uid == -1 or self.plugin_index != f_index:
            if self.plugin_uid > -1:
                libmk.PLUGIN_UI_DICT.close_plugin_ui(self.plugin_uid)
            self.plugin_uid = libmk.PROJECT.get_next_plugin_uid()
            self.plugin_index = f_index
        self.set_plugin_func(
            self.track_num, self.index, f_index,
            self.plugin_uid, self.power_checkbox.isChecked())
        if a_save:
            self.save_callback()
        self.on_show_ui()

    def on_power_changed(self, a_val=None):
        f_index = get_plugin_uid_by_name(self.plugin_combobox.currentText())
        if f_index:
            self.set_plugin_func(
                self.track_num, self.index, f_index,
                self.plugin_uid, self.power_checkbox.isChecked())
            self.save_callback()

    def wheel_event(self, a_event=None):
        pass

    def on_show_ui(self):
        f_index = get_plugin_uid_by_name(self.plugin_combobox.currentText())
        if f_index == 0 or self.plugin_uid == -1:
            return
        if self.plugin_ui:
            self.vlayout.removeWidget(self.plugin_ui.widget)
        self.plugin_ui = libmk.PLUGIN_UI_DICT.open_plugin_ui(
            self.plugin_uid, f_index)
        self.vlayout.addWidget(self.plugin_ui.widget)


class PluginSettingsMain(AbstractPluginSettings):
    def __init__(
            self, a_set_plugin_func, a_index, a_track_num, a_save_callback):
        self.plugin_list = MAIN_PLUGIN_NAMES

        self.menu_button = QPushButton(_("Menu"))
        self.menu = QMenu()
        self.menu_button.setMenu(self.menu)
        f_copy_action = self.menu.addAction(_("Copy"))
        f_copy_action.triggered.connect(self.copy)
        f_paste_action = self.menu.addAction(_("Paste"))
        f_paste_action.triggered.connect(self.paste)
        self.menu.addSeparator()
        f_cut_action = self.menu.addAction(_("Cut"))
        f_cut_action.triggered.connect(self.cut)
        self.menu.addSeparator()
        f_clear_action = self.menu.addAction(_("Clear"))
        f_clear_action.triggered.connect(self.clear)

        AbstractPluginSettings.__init__(
            self, a_set_plugin_func, a_index, a_track_num, a_save_callback)
        self.layout.addItem(QSpacerItem(1, 1, QSizePolicy.Expanding))


class PluginSettingsMixer(AbstractPluginSettings):
    def __init__(
            self, a_set_plugin_func, a_index, a_track_num, a_save_callback):
        self.plugin_list = MIXER_PLUGIN_NAMES
        AbstractPluginSettings.__init__(
            self, a_set_plugin_func, a_index, a_track_num,
            a_save_callback, a_qcbox=True, a_is_mixer=True)


class PluginSettingsWaveEditor(AbstractPluginSettings):
    def __init__(
            self, a_set_plugin_func, a_index, a_track_num, a_save_callback):
        self.plugin_list = WAVE_EDITOR_PLUGIN_NAMES
        AbstractPluginSettings.__init__(
            self, a_set_plugin_func, a_index, a_track_num, a_save_callback)
        self.layout.addItem(QSpacerItem(1, 1, QSizePolicy.Expanding))


class PluginRackTab:
    def __init__(self):
        self.widget = QWidget(libmk.MAIN_WINDOW)
        self.vlayout = QVBoxLayout(self.widget)
        self.menu_layout = QHBoxLayout()
        self.vlayout.addLayout(self.menu_layout)
        self.track_combobox = QComboBox()
        self.track_combobox.setMinimumWidth(300)
        self.menu_layout.addWidget(QLabel(_("Track")))
        self.menu_layout.addWidget(self.track_combobox)

        self.plugins_button = QPushButton(_("Menu"))
        self.plugins_menu = QMenu(self.widget)
        self.plugins_button.setMenu(self.plugins_menu)
        self.plugins_order_action = self.plugins_menu.addAction(_("Order..."))
        self.plugins_order_action.triggered.connect(self.set_plugin_order)
        self.menu_layout.addItem(QSpacerItem(20, 1))
        self.menu_layout.addWidget(self.plugins_button)

        self.menu_layout.addItem(QSpacerItem(1, 1, QSizePolicy.Expanding))

        self.stacked_widget = QStackedWidget()
        self.vlayout.addWidget(self.stacked_widget)
        self.enabled = True
        self.plugin_racks = {}
        self.last_rack_num = None

    def set_plugin_order(self):
        index = self.track_combobox.currentIndex()
        rack = self.plugin_racks[index]
        rack.set_plugin_order()

    def initialize(self, a_project):
        self.PROJECT = a_project
        self.track_combobox.currentIndexChanged.connect(self.track_changed)

    def tab_selected(self, a_is_selected):
        """ Call this when the parent tab widget switches to/from this tab """
        if a_is_selected:
            self.track_changed()
        else:
            self.close_rack(self.track_combobox.currentIndex())

    def show_rack(self, a_rack_num):
        rack = self.plugin_racks[a_rack_num]
        for plugin in rack.plugins:
            if plugin.plugin_ui:
                plugin.plugin_ui.widget_show()

    def close_rack(self, a_rack_num):
        if a_rack_num not in self.plugin_racks:
            print("{} not in self.plugins_racks".format(a_rack_num))
            return
        rack = self.plugin_racks[a_rack_num]
        for plugin in rack.plugins:
            if plugin.plugin_ui:
                plugin.plugin_ui.widget_close()

    def track_changed(self, a_val=None):
        if not self.enabled:
            return
        f_index = self.track_combobox.currentIndex()
        if f_index not in self.plugin_racks:
            f_rack = PluginRack(self.PROJECT, f_index)
            self.plugin_racks[f_index] = f_rack
            self.stacked_widget.addWidget(self.plugin_racks[f_index].widget)
        self.show_rack(f_index)
        self.stacked_widget.setCurrentWidget(self.plugin_racks[f_index].widget)
        if self.last_rack_num is not None and self.last_rack_num != f_index:
            self.close_rack(self.last_rack_num)
        self.last_rack_num = f_index

    def set_track_names(self, a_list):
        self.track_combobox.clear()
        self.track_combobox.addItems(a_list)

    def set_track_order(self, a_dict):
        self.enabled = False
        f_index = self.track_combobox.currentIndex()
        f_new_index = a_dict[f_index]
        self.plugin_racks = {y:self.plugin_racks[x] for x, y in a_dict.items()}
        for k, v in self.plugin_racks:
            v.track_number = k
        self.track_combobox.setCurrentIndex(f_new_index)
        self.enabled = True


class PluginRack:
    def __init__(self, a_project, a_track_number, a_type=PluginSettingsMain):
        self.track_number = int(a_track_number)
        self.PROJECT = a_project
        self.plugins = [
            a_type(
                self.PROJECT.IPC.pydaw_set_plugin, x, a_track_number,
                self.save_callback)
            for x in range(10)]
        self.widget = QWidget()
        self.vlayout = QVBoxLayout(self.widget)
        self.vlayout.setContentsMargins(1, 1, 1, 1)

        self.scrollarea = QScrollArea()
        self.scrollarea.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollarea.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn)
        self.vlayout.addWidget(self.scrollarea)
        self.scrollarea.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName("plugin_ui")
        self.scroll_vlayout = QVBoxLayout(self.scroll_widget)
        #self.scroll_widget.setContentsMargins(0, 0, 0, 0)
        self.scrollarea.setWidget(self.scroll_widget)
        for plugin in self.plugins:
            self.scroll_vlayout.addLayout(plugin.vlayout)
        self.open_plugins()
        self.scroll_vlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Expanding))

    def get_plugin_uids(self):
        return [x.plugin_uid for x in self.plugins if x.plugin_uid != -1]

    def set_plugin_order(self):
        f_labels = ["{} : {}".format(f_i, x.plugin_combobox.currentText())
            for f_i, x in zip(range(1, 11), self.plugins)]
        f_result = pydaw_widgets.ordered_table_dialog(
            f_labels, self.plugins, 30, 200, libmk.MAIN_WINDOW)
        if f_result:
            for f_i, f_plugin in zip(range(len(f_result)), f_result):
                f_plugin.index = f_i
                f_plugin.on_plugin_change(a_save=False)
            print(self.plugins, f_result)
            self.plugins[0:len(f_result)] = f_result
            print(self.plugins, f_result)
            self.save_callback()
            #self.open_plugins()
            for plugin in self.plugins:
                self.scroll_vlayout.removeItem(plugin.vlayout)
            for plugin in self.plugins:
                self.scroll_vlayout.addLayout(plugin.vlayout)

    def open_plugins(self):
        f_plugins = self.PROJECT.get_track_plugins(self.track_number)
        if f_plugins:
            for f_plugin in f_plugins.plugins:
                self.plugins[f_plugin.index].set_value(f_plugin)

    def save_callback(self):
        f_result = libmk.pydaw_track_plugins()
        f_result.plugins = [x.get_value() for x in self.plugins]
        self.PROJECT.save_track_plugins(self.track_number, f_result)
        self.PROJECT.commit(
            "Update track plugins for track {}".format(self.track_number))


