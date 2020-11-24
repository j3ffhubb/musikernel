#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

import datetime
import math
import os
import random
import shutil
import subprocess
import traceback

from mkpy.mkqt import *

from . import *
from .filedragdrop import FileDragDropper
from .hardware import MidiDevicesDialog
from .item_editor.audio import (
    AudioItemSeq,
    AudioItemSeqWidget,
)
from .item_editor.automation import (
    AutomationEditor,
    AutomationEditorWidget,
)
from .item_editor.editor import ItemListViewer
from .item_editor.notes import (
    PianoRollEditor,
    PianoRollEditorWidget,
)
from .sequencer import (
    ItemSequencer,
    SequencerWidget,
    TrackPanel,
    TransportWidget,
)
from mkpy.glbl import mk_project
from mkpy.lib import *
from mkpy.lib.util import *
from mkpy.widgets import *
from mkpy.lib.translate import _
from mkpy.plugins import *
from mkpy import glbl
from mkpy import plugins
from mkpy.daw import strings as daw_strings
from mkpy.lib import strings as mk_strings


CLOSE_ENGINE_ON_RENDER = True


class MainWindow(QScrollArea):
    """ The main window for DAW-Next that contains all widgets
        except TransportWidget
    """
    def __init__(self):
        QScrollArea.__init__(self)
        self.first_offline_render = True
        self.last_offline_dir = global_home
        self.copy_to_clipboard_checked = True
        self.last_midi_dir = None

        self.setObjectName("plugin_ui")
        self.widget = QWidget()
        self.widget.setObjectName("plugin_ui")
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.widget.setLayout(self.main_layout)

        # Transport shortcuts (added here so they will work
        # when the transport is hidden)

        self.loop_mode_action = QAction(self)
        self.addAction(self.loop_mode_action)
        self.loop_mode_action.setShortcut(
            QKeySequence.fromString("CTRL+L"))
        self.loop_mode_action.triggered.connect(
            shared.TRANSPORT.toggle_loop_mode,
        )

        self.select_mode_action = QAction(self)
        self.addAction(self.select_mode_action)
        self.select_mode_action.setShortcut(QKeySequence.fromString("A"))
        self.select_mode_action.triggered.connect(
            shared.TRANSPORT.tool_select_clicked,
        )

        self.draw_mode_action = QAction(self)
        self.addAction(self.draw_mode_action)
        self.draw_mode_action.setShortcut(QKeySequence.fromString("S"))
        self.draw_mode_action.triggered.connect(
            shared.TRANSPORT.tool_draw_clicked)

        self.erase_mode_action = QAction(self)
        self.addAction(self.erase_mode_action)
        self.erase_mode_action.setShortcut(QKeySequence.fromString("D"))
        self.erase_mode_action.triggered.connect(
            shared.TRANSPORT.tool_erase_clicked)

        self.split_mode_action = QAction(self)
        self.addAction(self.split_mode_action)
        self.split_mode_action.setShortcut(QKeySequence.fromString("F"))
        self.split_mode_action.triggered.connect(
            shared.TRANSPORT.tool_split_clicked)

        #The tabs
        self.main_tabwidget = QTabWidget()
        self.main_layout.addWidget(self.main_tabwidget)

        self.song_region_tab = QWidget()
        self.song_region_vlayout = QVBoxLayout()
        self.song_region_vlayout.setContentsMargins(1, 1, 1, 1)
        self.song_region_tab.setLayout(self.song_region_vlayout)
        self.sequencer_widget = QWidget()
        self.sequencer_vlayout = QVBoxLayout(self.sequencer_widget)
        self.sequencer_vlayout.setContentsMargins(1, 1, 1, 1)
        self.sequencer_vlayout.addWidget(self.song_region_tab)
        self.main_tabwidget.addTab(self.sequencer_widget, _("Sequencer"))

        self.song_region_vlayout.addWidget(shared.SEQ_WIDGET.widget)

        self.midi_scroll_area = QScrollArea()
        self.midi_scroll_area.setWidgetResizable(True)
        self.midi_scroll_widget = QWidget()
        self.midi_scroll_widget.setContentsMargins(0, 0, 0, 0)
        self.midi_hlayout = QHBoxLayout(self.midi_scroll_widget)
        self.midi_hlayout.setContentsMargins(0, 0, 0, 0)
        self.midi_scroll_area.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn)
        self.midi_scroll_area.setWidget(self.midi_scroll_widget)
        self.midi_hlayout.addWidget(shared.TRACK_PANEL.tracks_widget)
        self.midi_hlayout.addWidget(shared.SEQUENCER)

        self.file_browser = FileDragDropper(util.is_audio_midi_file)
        self.file_browser.set_multiselect(True)
        self.file_browser.hsplitter.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sequencer_vlayout.addWidget(self.file_browser.hsplitter)
        self.file_browser.hsplitter.insertWidget(0, self.midi_scroll_area)
        self.file_browser.hsplitter.setSizes([9999, 200])

        self.midi_scroll_area.scrollContentsBy = self.midi_scrollContentsBy
        self.vscrollbar = self.midi_scroll_area.verticalScrollBar()
        self.vscrollbar.sliderReleased.connect(self.vscrollbar_released)
        self.vscrollbar.setSingleStep(shared.REGION_EDITOR_TRACK_HEIGHT)

        self.main_tabwidget.addTab(shared.PLUGIN_RACK.widget, _("Plugin Rack"))
        self.main_tabwidget.addTab(shared.ITEM_EDITOR.widget, _("Item Editor"))

        self.automation_tab = QWidget()
        self.automation_tab.setObjectName("plugin_ui")

        self.main_tabwidget.addTab(shared.ROUTING_GRAPH_WIDGET, _("Routing"))
        self.main_tabwidget.addTab(shared.MIXER_WIDGET.widget, _("Mixer"))

        self.notes_tab = QTextEdit(self)
        self.notes_tab.setAcceptRichText(False)
        self.notes_tab.leaveEvent = self.on_edit_notes
        self.main_tabwidget.addTab(self.notes_tab, _("Project Notes"))

        self.main_tabwidget.currentChanged.connect(self.tab_changed)

    def vscrollbar_released(self, a_val=None):
        f_val = round(
            self.vscrollbar.value() /
            shared.REGION_EDITOR_TRACK_HEIGHT
        ) * shared.REGION_EDITOR_TRACK_HEIGHT
        self.vscrollbar.setValue(int(f_val))

    def on_offline_render(self):
        def ok_handler():
            if str(f_name.text()) == "":
                QMessageBox.warning(
                    f_window, _("Error"), _("Name cannot be empty"))
                return

            if f_copy_to_clipboard_checkbox.isChecked():
                self.copy_to_clipboard_checked = True
                f_clipboard = QApplication.clipboard()
                f_clipboard.setText(f_name.text())
            else:
                self.copy_to_clipboard_checked = False

            f_stem = 1 if f_stem_render_checkbox.isChecked() else 0
            f_dir = shared.PROJECT.project_folder
            f_out_file = f_name.text()
            f_fini = os.path.join(f_out_file, "finished") if f_stem else None
            f_samp_rate = f_sample_rate.currentText()
            f_buff_size = util.global_device_val_dict["bufferSize"]
            f_thread_count = 1 if util.IS_WINDOWS else \
                util.global_device_val_dict["threads"]

            self.last_offline_dir = os.path.dirname(str(f_name.text()))

            f_window.close()

            if util.IS_LINUX and f_debug_checkbox.isChecked():
                f_cmd = "{} -e bash -c 'gdb {}-dbg'".format(
                    util.TERMINAL, util.BIN_PATH)
                f_run_cmd = [str(x) for x in
                    ("run", "daw", "'{}'".format(f_dir),
                    "'{}'".format(f_out_file), f_start_beat, f_end_beat,
                    f_samp_rate, f_buff_size, f_thread_count, f_stem)]
                f_clipboard = QApplication.clipboard()
                f_clipboard.setText(" ".join(f_run_cmd))
                subprocess.Popen(f_cmd, shell=True)
            else:
                f_cmd = [str(x) for x in
                    (util.BIN_PATH, "daw",
                     f_dir, f_out_file, f_start_beat, f_end_beat,
                     f_samp_rate, f_buff_size, f_thread_count,
                     util.USE_HUGEPAGES, f_stem)]
                glbl.MAIN_WINDOW.show_offline_rendering_wait_window_v2(
                    f_cmd,
                    f_out_file,
                    f_file_name=f_fini,
                )

                if f_stem:
                    f_tracks = shared.PROJECT.get_tracks()
                    for f_file in os.listdir(f_out_file):
                        f_track_num = f_file.split(".", 1)[0].zfill(3)
                        f_track_name = f_tracks.tracks[int(f_track_num)].name
                        f_new = "{}-{}.wav".format(f_track_num, f_track_name)
                        os.rename(
                            os.path.join(f_out_file, f_file),
                            os.path.join(f_out_file, f_new))

        def cancel_handler():
            f_window.close()

        def stem_check_changed(a_val=None):
            f_name.setText("")

        def file_name_select():
            if not os.path.isdir(self.last_offline_dir):
                self.last_offline_dir = global_home
            if f_stem_render_checkbox.isChecked():
                f_file = QFileDialog.getExistingDirectory(
                    MAIN_WINDOW,
                    _('Select an empty directory to render stems to'),
                    self.last_offline_dir,
                    QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog,
                )
                if f_file and str(f_file):
                    if os.listdir(f_file):
                        QMessageBox.warning(
                            self, _("Error"),
                            _("The directory is not empty"))
                    else:
                        f_name.setText(f_file)
                        self.last_offline_dir = f_file
            else:
                f_file_name, f_filter = QFileDialog.getSaveFileName(
                    shared.MAIN_WINDOW,
                    _("Select a file name to save to..."),
                    self.last_offline_dir,
                    options=QFileDialog.DontUseNativeDialog,
                )
                f_file_name = str(f_file_name)
                if f_file_name and str(f_file_name):
                    if not f_file_name.endswith(".wav"):
                        f_file_name += ".wav"
                    if f_file_name and str(f_file_name):
                        f_name.setText(f_file_name)
                    self.last_offline_dir = os.path.dirname(f_file_name)

        f_marker_pos = shared.SEQUENCER.get_loop_pos(a_warn=False)

        if not f_marker_pos:
            QMessageBox.warning(
                MAIN_WINDOW, _("Error"),
                _("You must set the Loop/Export markers first by "
                "right-clicking on the sequencer timeline"))
            return

        # Force the plugin state to be saved to disk first if it changed
        shared.PLUGIN_RACK.tab_selected(False)

        f_start_beat, f_end_beat = f_marker_pos

        f_window = QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Offline Render"))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)

        f_name = QLineEdit()
        f_name.setReadOnly(True)
        f_name.setMinimumWidth(360)
        f_layout.addWidget(QLabel(_("File Name:")), 0, 0)
        f_layout.addWidget(f_name, 0, 1)
        f_select_file = QPushButton(_("Select"))
        f_select_file.pressed.connect(file_name_select)
        f_layout.addWidget(f_select_file, 0, 2)

        f_sample_rate_hlayout = QHBoxLayout()
        f_layout.addLayout(f_sample_rate_hlayout, 3, 1)
        f_sample_rate_hlayout.addWidget(QLabel(_("Sample Rate")))
        f_sample_rate = QComboBox()
        f_sample_rate.setMinimumWidth(105)
        f_sample_rate.addItems([
            "44100",
            "48000",
            "88200",
            "96000",
            "192000",
            "384000",
            "768000",
            "1536000",
        ])

        try:
            f_sr_index = f_sample_rate.findText(
                util.global_device_val_dict["sampleRate"])
            f_sample_rate.setCurrentIndex(f_sr_index)
        except:
            pass

        f_sample_rate_hlayout.addWidget(f_sample_rate)

        f_stem_render_checkbox = QCheckBox(_("Stem Render"))
        f_sample_rate_hlayout.addWidget(f_stem_render_checkbox)
        f_stem_render_checkbox.stateChanged.connect(stem_check_changed)

        f_sample_rate_hlayout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding))

        f_layout.addWidget(QLabel(
            _("File is exported to 32 bit .wav at the selected sample rate. "
            "\nYou can convert the format using "
            "Menu->Tools->MP3/Ogg Converter")),
            6, 1)
        f_copy_to_clipboard_checkbox = QCheckBox(
        _("Copy export path to clipboard? (useful for right-click pasting "
        "back into the audio sequencer)"))
        f_copy_to_clipboard_checkbox.setChecked(self.copy_to_clipboard_checked)
        f_layout.addWidget(f_copy_to_clipboard_checkbox, 7, 1)
        f_ok_layout = QHBoxLayout()

        if util.IS_LINUX:
            f_debug_checkbox = QCheckBox("Debug with GDB?")
            f_ok_layout.addWidget(f_debug_checkbox)

        f_ok_layout.addItem(
            QSpacerItem(10, 10, QSizePolicy.Expanding,
            QSizePolicy.Minimum))
        f_ok = QPushButton(_("OK"))
        f_ok.setMinimumWidth(75)
        f_ok.pressed.connect(ok_handler)
        f_ok_layout.addWidget(f_ok)
        f_layout.addLayout(f_ok_layout, 9, 1)
        f_cancel = QPushButton(_("Cancel"))
        f_cancel.setMinimumWidth(75)
        f_cancel.pressed.connect(cancel_handler)
        f_ok_layout.addWidget(f_cancel)
        f_window.exec_()

    def on_undo(self):
        if glbl.IS_PLAYING or not self.check_tab_for_undo():
            return
        glbl.APP.setOverrideCursor(QtCore.Qt.WaitCursor)
        if shared.PROJECT.undo():
            global_ui_refresh_callback()
            glbl.APP.restoreOverrideCursor()
        else:
            glbl.APP.restoreOverrideCursor()
            QMessageBox.warning(
                MAIN_WINDOW,
                "Error",
                "No more undo history left",
            )

    def on_redo(self):
        if glbl.IS_PLAYING or not self.check_tab_for_undo():
            return
        glbl.APP.setOverrideCursor(QtCore.Qt.WaitCursor)
        if shared.PROJECT.redo():
            shared.global_ui_refresh_callback()
            glbl.APP.restoreOverrideCursor()
        else:
            glbl.APP.restoreOverrideCursor()
            QMessageBox.warning(
                shared.MAIN_WINDOW,
                "Error",
                "Already at the latest commit",
            )

    def check_tab_for_undo(self):
        index = self.main_tabwidget.currentIndex()
        if index in (
            shared.TAB_ITEM_EDITOR,
            shared.TAB_ROUTING,
            shared.TAB_SEQUENCER,
        ):
            return True
        else:
            QMessageBox.warning(
                shared.MAIN_WINDOW, "Error",
                "Undo/redo only supported for the sequencer, item editor "
                "and routing tab.  Individual plugins have undo for each "
                "control by right-clicking and selecting the undo menu")
            return False

    def tab_changed(self):
        f_index = self.main_tabwidget.currentIndex()
        shared.PROJECT.set_undo_context(f_index)
        if f_index == shared.TAB_SEQUENCER and not glbl.IS_PLAYING:
            shared.SEQUENCER.open_region()
        elif f_index == shared.TAB_ITEM_EDITOR:
            shared.ITEM_EDITOR.tab_changed()
        elif f_index == shared.TAB_ROUTING:
            shared.ROUTING_GRAPH_WIDGET.draw_graph(
                shared.PROJECT.get_routing_graph(),
                shared.TRACK_NAMES,
            )
        elif f_index == shared.TAB_MIXER:
            global_open_mixer()

        shared.PLUGIN_RACK.tab_selected(f_index == shared.TAB_PLUGIN_RACK)
        QApplication.restoreOverrideCursor()

    def on_edit_notes(self, a_event=None):
        QTextEdit.leaveEvent(self.notes_tab, a_event)
        shared.PROJECT.write_notes(self.notes_tab.toPlainText())

    def set_tooltips(self, a_on):
        if a_on:
            shared.ROUTING_GRAPH_WIDGET.setToolTip(mk_strings.routing_graph)
        else:
            shared.ROUTING_GRAPH_WIDGET.setToolTip("")

    def midi_scrollContentsBy(self, x, y):
        QScrollArea.scrollContentsBy(self.midi_scroll_area, x, y)
        f_y = self.midi_scroll_area.verticalScrollBar().value()
        shared.SEQUENCER.set_header_y_pos(f_y)

    def configure_callback(self, path, arr):
        f_pc_dict = {}
        f_ui_dict = {}
        f_cc_dict = {}
        for f_line in arr[0].split("\n"):
            if f_line == "":
                break
            a_key, a_val = f_line.split("|", 1)
            if a_key == "pc":
                f_plugin_uid, f_port, f_val = a_val.split("|")
                f_pc_dict[(f_plugin_uid, f_port)] = f_val
            elif a_key == "cur":
                if glbl.IS_PLAYING:
                    f_beat = float(a_val)
                    global_set_playback_pos(f_beat)
            elif a_key == "peak":
                global_update_peak_meters(a_val)
            elif a_key == "cc":
                f_track_num, f_cc, f_val = a_val.split("|")
                f_cc_dict[(f_track_num, f_cc)] = f_val
            elif a_key == "ui":
                f_plugin_uid, f_name, f_val = a_val.split("|", 2)
                f_ui_dict[(f_plugin_uid, f_name)] = f_val
            elif a_key == "mrec":
                MREC_EVENTS.append(a_val)
            elif a_key == "ne":
                f_state, f_note = a_val.split("|")
                shared.PIANO_ROLL_EDITOR.highlight_keys(f_state, f_note)
            elif a_key == "ml":
                glbl.PLUGIN_UI_DICT.midi_learn_control[0].update_cc_map(
                    a_val, glbl.PLUGIN_UI_DICT.midi_learn_control[1])
            elif a_key == "ready":
                glbl.on_ready()
        #This prevents multiple events from moving the same control,
        #only the last goes through
        for k, f_val in f_ui_dict.items():
            f_plugin_uid, f_name = k
            if int(f_plugin_uid) in glbl.PLUGIN_UI_DICT:
                glbl.PLUGIN_UI_DICT[int(f_plugin_uid)].ui_message(
                    f_name, f_val)
        for k, f_val in f_pc_dict.items():
            f_plugin_uid, f_port = (int(x) for x in k)
            if f_plugin_uid in glbl.PLUGIN_UI_DICT:
                glbl.PLUGIN_UI_DICT[f_plugin_uid].set_control_val(
                    f_port, float(f_val))
        for k, f_val in f_cc_dict.items():
            f_track_num, f_cc = (int(x) for x in k)
            uids = []
            if f_track_num in shared.PLUGIN_RACK.plugin_racks:
                rack = shared.PLUGIN_RACK.plugin_racks[f_track_num]
                uids.extend(rack.get_plugin_uids())
            if f_track_num in shared.MIXER_WIDGET.tracks:
                track = shared.MIXER_WIDGET.tracks[f_track_num]
                uids.extend(track.get_plugin_uids())
            for f_plugin_uid in uids:
                if f_plugin_uid in glbl.PLUGIN_UI_DICT:
                    glbl.PLUGIN_UI_DICT[
                        f_plugin_uid].set_cc_val(f_cc, f_val)

    def prepare_to_quit(self):
        try:
            for f_widget in (
                shared.AUDIO_SEQ,
                shared.CC_EDITOR,
                shared.PB_EDITOR,
                shared.PIANO_ROLL_EDITOR,
                shared.ROUTING_GRAPH_WIDGET,
                shared.SEQUENCER,
            ):
                f_widget.prepare_to_quit()
        except Exception as ex:
            print("Exception thrown while attempting to close DAW-Next")
            print("Exception:  {}".format(ex))

def init():
    global MAIN_WINDOW, TRANSPORT
    shared.ATM_REGION = DawAtmRegion()
    shared.SEQUENCER = ItemSequencer()
    shared.PB_EDITOR = AutomationEditor(a_is_cc=False)
    shared.CC_EDITOR = AutomationEditor()
    shared.CC_EDITOR_WIDGET = AutomationEditorWidget(shared.CC_EDITOR)

    shared.SEQ_WIDGET = SequencerWidget()
    shared.TRACK_PANEL = TrackPanel()

    shared.PIANO_ROLL_EDITOR = PianoRollEditor()
    shared.PIANO_ROLL_EDITOR_WIDGET = PianoRollEditorWidget()
    shared.AUDIO_SEQ = AudioItemSeq()
    shared.AUDIO_SEQ_WIDGET = AudioItemSeqWidget()
    shared.ITEM_EDITOR = ItemListViewer()
    shared.MIXER_WIDGET = plugins.MixerWidget(TRACK_COUNT_ALL)

    get_mixer_peak_meters()

    shared.MIDI_EDITORS = (
        shared.CC_EDITOR,
        shared.PB_EDITOR,
        shared.PIANO_ROLL_EDITOR,
    )

    shared.MIDI_DEVICES_DIALOG = MidiDevicesDialog()
    shared.TRANSPORT = TransportWidget()
    TRANSPORT = shared.TRANSPORT

    shared.ROUTING_GRAPH_WIDGET = widgets.RoutingGraphWidget(
        routing_graph_toggle_callback,
    )

    shared.PLUGIN_RACK = PluginRackTab()

    # Must call this after instantiating the other widgets,
    # as it relies on them existing
    shared.MAIN_WINDOW = MainWindow()
    MAIN_WINDOW = shared.MAIN_WINDOW

    shared.PIANO_ROLL_EDITOR.verticalScrollBar().setSliderPosition(
        shared.PIANO_ROLL_EDITOR.scene.height() * 0.4,
    )

    shared.ITEM_EDITOR.snap_combobox.setCurrentIndex(4)

    if glbl.TOOLTIPS_ENABLED:
        set_tooltips_enabled(glbl.TOOLTIPS_ENABLED)

