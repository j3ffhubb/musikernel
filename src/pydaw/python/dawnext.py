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
import os
import subprocess
import random
import shutil
import traceback

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from libpydaw import *
from mkplugins import *

from libpydaw import scales

import math

from libpydaw.pydaw_util import *
from libpydaw.pydaw_widgets import *
from libpydaw.translate import _
import libpydaw.strings
import libdawnext.strings
import libmk
from libmk import mk_project
from libdawnext import *
import mkplugins

TAB_SEQUENCER = 0
TAB_PLUGIN_RACK = 1
TAB_ITEM_EDITOR = 2
TAB_ROUTING = 3
TAB_MIXER = 4
TAB_NOTES = 5

START_PEN = QPen(QColor.fromRgb(120, 120, 255), 6.0)
END_PEN = QPen(QColor.fromRgb(255, 60, 60), 6.0)

def pydaw_get_current_region_length():
    return CURRENT_REGION.get_length() if CURRENT_REGION else 32

def global_get_audio_file_from_clipboard():
    f_clipboard = QApplication.clipboard()
    f_path = f_clipboard.text()
    if not f_path:
        QMessageBox.warning(
            MAIN_WINDOW, _("Error"), _("No text in the system clipboard"))
    else:
        f_path = str(f_path).strip()
        if os.path.isfile(f_path):
            print(f_path)
            return f_path
        else:
            f_path = f_path[:100]
            QMessageBox.warning(
                MAIN_WINDOW, _("Error"),
                _("{} is not a valid file").format(f_path))
    return None


def set_tooltips_enabled(a_enabled):
    """ Set extensive tooltips as an alternative to
        maintaining a separate user manual
    """
    libmk.TOOLTIPS_ENABLED = a_enabled

    f_list = [
        AUDIO_SEQ_WIDGET, PIANO_ROLL_EDITOR, MAIN_WINDOW,
        AUDIO_SEQ, TRANSPORT, MIXER_WIDGET,
        SEQUENCER, TRACK_PANEL, PLUGIN_RACK] + list(AUTOMATION_EDITORS)
    for f_widget in f_list:
        f_widget.set_tooltips(a_enabled)


def global_update_hidden_rows(a_val=None):
    return # TODO
#    REGION_EDITOR.setUpdatesEnabled(False)
#    if CURRENT_REGION and REGION_SETTINGS.hide_inactive:
#        f_active = {x.track_num for x in CURRENT_REGION.items}
#        for k, v in TRACK_PANEL.tracks.items():
#            v.group_box.setHidden(k not in f_active)
#    else:
#        for v in TRACK_PANEL.tracks.values():
#            v.group_box.setHidden(False)
#    REGION_EDITOR.setUpdatesEnabled(True)
#    REGION_EDITOR.update()


CURRENT_REGION = None
CURRENT_REGION_NAME = None
DRAW_SEQUENCER_GRAPHS = True

class RegionSettings:
    """ The widget that holds the sequencer """
    def __init__(self):
        self.enabled = False
        self.widget = QWidget()
        self.widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.hlayout0 = QHBoxLayout(self.widget)
        self.hlayout0.setContentsMargins(1, 1, 1, 1)
        self.edit_mode_combobox = QComboBox()
        self.edit_mode_combobox.setMinimumWidth(132)
        self.edit_mode_combobox.addItems([_("Items"), _("Automation")])
        self.edit_mode_combobox.currentIndexChanged.connect(
            self.edit_mode_changed)

        self.atm_smoothing_combobox = QComboBox()
        self.atm_smoothing_combobox.setMinimumWidth(132)
        self.atm_smoothing_combobox.addItems([_("Linear"), _("Curved")])

        self.menu_button = QPushButton(_("Menu"))
        self.hlayout0.addWidget(self.menu_button)
        self.menu = QMenu(self.menu_button)
        self.menu_button.setMenu(self.menu)

        self.menu_widget = QWidget()
        self.menu_layout = QGridLayout(self.menu_widget)
        self.action_widget = QWidgetAction(self.menu)
        self.action_widget.setDefaultWidget(self.menu_widget)
        self.menu.addAction(self.action_widget)
        self.menu.addSeparator()

        self.menu_layout.addWidget(QLabel(_("Edit Mode:")), 0, 0)
        self.menu_layout.addWidget(self.edit_mode_combobox, 0, 1)

        self.menu_layout.addWidget(QLabel(_("Automation Smoothing:")), 1, 0)
        self.menu_layout.addWidget(self.atm_smoothing_combobox, 1, 1)

        self.reorder_tracks_action = self.menu.addAction(
            _("Reorder Tracks..."))
        self.reorder_tracks_action.triggered.connect(self.set_track_order)
        self.menu.addSeparator()
        self.hide_inactive = False
#        self.toggle_hide_action = self.menu.addAction(
#            _("Hide Inactive Instruments"))
#        self.toggle_hide_action.setCheckable(True)
#        self.toggle_hide_action.triggered.connect(self.toggle_hide_inactive)
#        self.toggle_hide_action.setShortcut(
#            QKeySequence.fromString("CTRL+H"))
        self.menu.addSeparator()
        self.unsolo_action = self.menu.addAction(_("Un-Solo All"))
        self.unsolo_action.triggered.connect(self.unsolo_all)
        self.unsolo_action.setShortcut(QKeySequence.fromString("CTRL+J"))
        self.unmute_action = self.menu.addAction(_("Un-Mute All"))
        self.unmute_action.triggered.connect(self.unmute_all)
        self.unmute_action.setShortcut(QKeySequence.fromString("CTRL+M"))

        self.snap_combobox = QComboBox()
        self.snap_combobox.addItems(
            [_("None"), _("Beat"), "1/8", "1/12", "1/16"])
        self.snap_combobox.currentIndexChanged.connect(self.set_snap)

        self.menu_layout.addWidget(QLabel(_("Snap:")), 5, 0)
        self.menu_layout.addWidget(self.snap_combobox, 5, 1)

        self.follow_checkbox = QCheckBox(_("Follow"))
        self.hlayout0.addWidget(self.follow_checkbox)

        self.hlayout0.addWidget(QLabel("H"))
        self.hzoom_slider = QSlider(QtCore.Qt.Horizontal)
        self.hlayout0.addWidget(self.hzoom_slider)
        self.hzoom_slider.setObjectName("zoom_slider")
        self.hzoom_slider.setRange(0, 30)
        self.hzoom_slider.setValue(3)
        self.hzoom_slider.setFixedWidth(90)
        self.hzoom_slider.sliderPressed.connect(self.hzoom_pressed)
        self.hzoom_slider.sliderReleased.connect(self.hzoom_released)
        self.hzoom_slider.valueChanged.connect(self.set_hzoom)

        self.hlayout0.addWidget(QLabel("V"))
        self.vzoom_slider = QSlider(QtCore.Qt.Horizontal)
        self.hlayout0.addWidget(self.vzoom_slider)
        self.vzoom_slider.setObjectName("zoom_slider")
        self.vzoom_slider.setRange(0, 60)
        self.vzoom_slider.setValue(0)
        self.vzoom_slider.setFixedWidth(60)
        self.vzoom_slider.sliderPressed.connect(self.vzoom_pressed)
        self.vzoom_slider.sliderReleased.connect(self.vzoom_released)
        self.vzoom_slider.valueChanged.connect(self.set_vzoom)

        self.size_label = QLabel()
        self.size_label.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.scrollbar = SEQUENCER.horizontalScrollBar()
        self.scrollbar.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.scrollbar.sliderPressed.connect(self.scrollbar_pressed)
        self.scrollbar.sliderReleased.connect(self.scrollbar_released)
        self.hlayout0.addWidget(self.scrollbar)
        self.scrollbar.setSingleStep(SEQUENCER_PX_PER_BEAT)

        self.widgets_to_disable = (
            self.hzoom_slider, self.vzoom_slider, self.menu_button)

    def scrollbar_pressed(self, a_val=None):
        if libmk.IS_PLAYING and self.follow_checkbox.isChecked():
            self.follow_checkbox.setChecked(False)

    def scrollbar_released(self, a_val=None):
        f_val = round(self.scrollbar.value() /
            SEQUENCER_PX_PER_BEAT) * SEQUENCER_PX_PER_BEAT
        self.scrollbar.setValue(int(f_val))

    def vzoom_pressed(self, a_val=None):
        self.old_px_per_beat = SEQUENCER_PX_PER_BEAT
        #self.size_label.move(QCursor.pos())
        self.size_label.setText("Track Height")
        self.set_vzoom_size()
        f_widget = MAIN_WINDOW.midi_scroll_area
        f_point = QtCore.QPoint(0, REGION_EDITOR_HEADER_HEIGHT + 2)
        self.size_label.setParent(f_widget)
        self.size_label.setStyleSheet(
            "QLabel { background-color: black; color: white }")
        self.size_label.move(f_point)
        self.size_label.show()
        self.old_height_px = REGION_EDITOR_TRACK_HEIGHT

    def vzoom_released(self, a_val=None):
        TRACK_PANEL.set_track_height()
        self.open_region()

        f_scrollbar = MAIN_WINDOW.midi_scroll_area.verticalScrollBar()
        f_scrollbar.setValue(
            (REGION_EDITOR_TRACK_HEIGHT / self.old_height_px) *
            f_scrollbar.value())
        MAIN_WINDOW.vscrollbar_released()  # Quantizes the vertical pos
        f_scrollbar.setSingleStep(REGION_EDITOR_TRACK_HEIGHT)
        self.size_label.hide()

    def set_vzoom_size(self):
        self.size_label.setFixedSize(
            REGION_TRACK_WIDTH, REGION_EDITOR_TRACK_HEIGHT + 2)

    def set_vzoom(self, a_val=None):
        global REGION_EDITOR_TRACK_HEIGHT, REGION_EDITOR_TOTAL_HEIGHT
        f_val = self.vzoom_slider.value()
        REGION_EDITOR_TRACK_HEIGHT = (f_val * 8) + 64
        REGION_EDITOR_TOTAL_HEIGHT = (REGION_EDITOR_TRACK_COUNT *
            REGION_EDITOR_TRACK_HEIGHT)
        self.set_vzoom_size()

    def hzoom_pressed(self, a_val=None):
        self.old_px_per_beat = SEQUENCER_PX_PER_BEAT
        #self.size_label.move(QCursor.pos())
        self.size_label.setText("Beat")
        self.set_hzoom_size()
        f_point = QtCore.QPoint(REGION_TRACK_WIDTH + 10, 2)
        f_widget = MAIN_WINDOW.midi_scroll_area
        self.size_label.setParent(f_widget)
        self.size_label.setStyleSheet(
            "QLabel { background-color: black; color: white }")
        self.size_label.move(f_point)
        self.size_label.show()

    def hzoom_released(self, a_val=None):
        pydaw_set_seq_snap()
        self.open_region()
        self.scrollbar.setValue(
            (SEQUENCER_PX_PER_BEAT / self.old_px_per_beat) *
            self.scrollbar.value())
        self.scrollbar.setSingleStep(SEQUENCER_PX_PER_BEAT)
        self.size_label.hide()

    def set_hzoom_size(self):
        self.size_label.setFixedSize(
            SEQUENCER_PX_PER_BEAT, REGION_EDITOR_HEADER_HEIGHT)

    def set_hzoom(self, a_val=None):
        global SEQUENCER_PX_PER_BEAT, DRAW_SEQUENCER_GRAPHS
        f_val = self.hzoom_slider.value()
        if f_val < 3:
            DRAW_SEQUENCER_GRAPHS = False
            f_length = pydaw_get_current_region_length()
            f_width = SEQUENCER.width()
            f_factor = {0:1, 1:2, 2:4}[f_val]
            SEQUENCER_PX_PER_BEAT = (f_width / f_length) * f_factor
            self.size_label.setText("Project * {}".format(f_factor))
            self.size_label.setFixedSize(
                150, REGION_EDITOR_HEADER_HEIGHT)
        else:
            if f_val < 6:
                f_val = 6
            DRAW_SEQUENCER_GRAPHS = True
            SEQUENCER_PX_PER_BEAT = ((f_val - 6) * 4) + 24
            self.size_label.setText("Beat")
            self.set_hzoom_size()

    def set_snap(self, a_val=None):
        pydaw_set_seq_snap(a_val)
        MAIN_WINDOW.tab_changed()

    def edit_mode_changed(self, a_value=None):
        global REGION_EDITOR_MODE
        REGION_EDITOR_MODE = a_value
        SEQUENCER.open_region()

    def toggle_hide_inactive(self):
        self.hide_inactive = self.toggle_hide_action.isChecked()
        global_update_hidden_rows()

    def unsolo_all(self):
        for f_track in TRACK_PANEL.tracks.values():
            f_track.solo_checkbox.setChecked(False)

    def unmute_all(self):
        for f_track in TRACK_PANEL.tracks.values():
            f_track.mute_checkbox.setChecked(False)

    def open_region(self):
        self.enabled = False
        global CURRENT_REGION
        if CURRENT_REGION:
            self.clear_items()
        CURRENT_REGION = PROJECT.get_region()
        self.enabled = True
        SEQUENCER.open_region()
        global_update_hidden_rows()
        #TRANSPORT.set_time(TRANSPORT.get_bar_value(), 0.0)

    def clear_items(self):
        SEQUENCER.clear_drawn_items()
        global CURRENT_REGION
        CURRENT_REGION = None

    def clear_new(self):
        global CURRENT_REGION
        CURRENT_REGION = None
        SEQUENCER.clear_new()

    def on_play(self):
        for f_widget in self.widgets_to_disable:
            f_widget.setEnabled(False)

    def on_stop(self):
        for f_widget in self.widgets_to_disable:
            f_widget.setEnabled(True)

    def set_track_order(self):
        f_result = pydaw_widgets.ordered_table_dialog(
            TRACK_NAMES[1:], [x + 1 for x in range(len(TRACK_NAMES[1:]))],
            30, 200, MAIN_WINDOW)
        if f_result:
            f_result = {f_result[x]:x + 1 for x in range(len(f_result))}
            f_result[0] = 0 # master track
            PROJECT.reorder_tracks(f_result)
            TRACK_PANEL.open_tracks()
            self.open_region()
            MIDI_DEVICES_DIALOG.set_routings()
            TRANSPORT.open_project()


REGION_EDITOR_SNAP = True
REGION_EDITOR_GRID_WIDTH = 1000.0
REGION_TRACK_WIDTH = 180  #Width of the tracks in px
REGION_EDITOR_TRACK_HEIGHT = 64

REGION_EDITOR_TRACK_COUNT = 32

REGION_EDITOR_HEADER_ROW_HEIGHT = 18
REGION_EDITOR_HEADER_HEIGHT = REGION_EDITOR_HEADER_ROW_HEIGHT * 3
#gets updated by the region editor to it's real value:
REGION_EDITOR_TOTAL_HEIGHT = (REGION_EDITOR_TRACK_COUNT *
    REGION_EDITOR_TRACK_HEIGHT)
REGION_EDITOR_QUANTIZE_INDEX = 4

SELECTED_ITEM_GRADIENT = QLinearGradient(
    QtCore.QPointF(0, 0), QtCore.QPointF(0, 12))
SELECTED_ITEM_GRADIENT.setColorAt(0, QColor(180, 172, 100))
SELECTED_ITEM_GRADIENT.setColorAt(1, QColor(240, 240, 240))

REGION_EDITOR_MODE = 0
SEQUENCER_PX_PER_BEAT = 24

def region_editor_set_delete_mode(a_enabled):
    global REGION_EDITOR_DELETE_MODE
    if a_enabled:
        SEQUENCER.setDragMode(QGraphicsView.NoDrag)
        REGION_EDITOR_DELETE_MODE = True
        QApplication.setOverrideCursor(
            QCursor(QtCore.Qt.ForbiddenCursor))
    else:
        SEQUENCER.setDragMode(QGraphicsView.RubberBandDrag)
        REGION_EDITOR_DELETE_MODE = False
        SEQUENCER.selected_item_strings = set()
        QApplication.restoreOverrideCursor()


REGION_EDITOR_MIN_NOTE_LENGTH = REGION_EDITOR_GRID_WIDTH / 128.0

REGION_EDITOR_DELETE_MODE = False

REGION_EDITOR_HEADER_GRADIENT = QLinearGradient(
    0.0, 0.0, 0.0, REGION_EDITOR_HEADER_HEIGHT)
REGION_EDITOR_HEADER_GRADIENT.setColorAt(0.0, QColor.fromRgb(61, 61, 61))
REGION_EDITOR_HEADER_GRADIENT.setColorAt(0.5, QColor.fromRgb(50,50, 50))
REGION_EDITOR_HEADER_GRADIENT.setColorAt(0.6, QColor.fromRgb(43, 43, 43))
REGION_EDITOR_HEADER_GRADIENT.setColorAt(1.0, QColor.fromRgb(65, 65, 65))


ALL_PEAK_METERS = {}

class TrackPanel:
    """ The widget that sits next to the sequencer QGraphicsView and
        contains the individual tracks
    """
    def __init__(self):
        self.tracks = {}
        self.plugin_uid_map = {}
        self.tracks_widget = QWidget()
        self.tracks_widget.setObjectName("plugin_ui")
        self.tracks_widget.setContentsMargins(0, 0, 0, 0)
        self.tracks_layout = QVBoxLayout(self.tracks_widget)
        self.tracks_layout.addItem(
            QSpacerItem(0, REGION_EDITOR_HEADER_HEIGHT + 2.0,
            vPolicy=QSizePolicy.MinimumExpanding))
        self.tracks_layout.setContentsMargins(0, 0, 0, 0)
        for i in range(REGION_EDITOR_TRACK_COUNT):
            f_track = SeqTrack(i, TRACK_NAMES[i])
            self.tracks[i] = f_track
            self.tracks_layout.addWidget(f_track.group_box)
        self.automation_dict = {
            x:(None, None) for x in range(REGION_EDITOR_TRACK_COUNT)}
        self.set_track_height()

    def set_tooltips(self, a_on):
        if a_on:
            self.tracks_widget.setToolTip(libpydaw.strings.track_panel)
        else:
            self.tracks_widget.setToolTip("")

    def set_track_height(self):
        self.tracks_widget.setUpdatesEnabled(False)
        self.tracks_widget.setFixedSize(
            QtCore.QSize(REGION_TRACK_WIDTH,
            (REGION_EDITOR_TRACK_HEIGHT * REGION_EDITOR_TRACK_COUNT) +
            REGION_EDITOR_HEADER_HEIGHT))
        for f_track in self.tracks.values():
            f_track.group_box.setFixedHeight(REGION_EDITOR_TRACK_HEIGHT)
        self.tracks_widget.setUpdatesEnabled(True)

    def get_track_names(self):
        return [
            self.tracks[k].track_name_lineedit.text()
            for k in sorted(self.tracks)]

    def get_atm_params(self, a_track_num):
        f_track = self.tracks[int(a_track_num)]
        return (
            f_track.automation_uid, f_track.automation_plugin)

    def update_automation(self):
        self.automation_dict = {
            x:(self.tracks[x].port_num, self.tracks[x].automation_uid)
            for x in self.tracks}

    def update_plugin_track_map(self):
        self.plugin_uid_map = {}
        for x in self.tracks:
            plugins = PROJECT.get_track_plugins(x)
            if plugins:
                for y in plugins.plugins:
                    self.plugin_uid_map[int(y.plugin_uid)] = int(x)

    def has_automation(self, a_track_num):
        return self.automation_dict[int(a_track_num)]

    def update_ccs_in_use(self):
        for v in self.tracks.values():
            v.update_in_use_combobox()

    def open_tracks(self):
        global TRACK_NAMES
        f_tracks = PROJECT.get_tracks()
        TRACK_NAMES = f_tracks.get_names()
        global_update_track_comboboxes()
        for key, f_track in f_tracks.tracks.items():
            self.tracks[key].open_track(f_track)
            self.tracks[key].refresh()
        self.update_plugin_track_map()

    def get_tracks(self):
        f_result = pydaw_tracks()
        for k, v in self.tracks.items():
            f_result.add_track(k, v.get_track())
        return f_result


ATM_POINT_DIAMETER = 6.0
ATM_POINT_RADIUS = ATM_POINT_DIAMETER * 0.5

ATM_GRADIENT = QLinearGradient(
    0, 0, ATM_POINT_DIAMETER, ATM_POINT_DIAMETER)
ATM_GRADIENT.setColorAt(0, QColor(255, 255, 255))
ATM_GRADIENT.setColorAt(0.5, QColor(210, 210, 210))

ATM_REGION = pydaw_atm_region()

class SeqAtmItem(QGraphicsEllipseItem):
    """ This is an automation point within the ItemSequencer, these are only
        drawn when "Automation" mode is selected in RegionSettings
    """
    def __init__(self, a_item, a_save_callback, a_min_y, a_max_y):
        QGraphicsEllipseItem.__init__(
            self, 0, 0, ATM_POINT_DIAMETER, ATM_POINT_DIAMETER)
        self.save_callback = a_save_callback
        self.item = a_item
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setZValue(1100.0)
        self.set_brush()
        self.min_y = a_min_y
        self.max_y = a_max_y
        self.is_deleted = False

    def itemChange(self, a_change, a_value):
        if a_change == QGraphicsItem.ItemSelectedHasChanged:
            self.set_brush()
        return QGraphicsItem.itemChange(self, a_change, a_value)

    def set_brush(self):
        if self.isSelected():
            self.setBrush(QtCore.Qt.black)
        else:
            self.setBrush(ATM_GRADIENT)

    def mousePressEvent(self, a_event):
        a_event.setAccepted(True)
        QGraphicsEllipseItem.mousePressEvent(self, a_event)
        self.quantize()

    def mouseMoveEvent(self, a_event):
        QGraphicsEllipseItem.mouseMoveEvent(self, a_event)
        self.quantize()

    def quantize(self):
        f_pos = self.pos()
        f_x = f_pos.x()
        if SEQ_QUANTIZE:
            f_x = round(f_x / SEQUENCER_QUANTIZE_PX) * SEQUENCER_QUANTIZE_PX
        else:
            f_x = round(
                f_x / SEQUENCER_QUANTIZE_64TH) * SEQUENCER_QUANTIZE_64TH
        f_x = pydaw_util.pydaw_clip_min(f_x, 0.0)
        f_y = pydaw_util.pydaw_clip_value(f_pos.y(), self.min_y, self.max_y)
        self.setPos(f_x, f_y)

    def mouseReleaseEvent(self, a_event):
        a_event.setAccepted(True)
        QGraphicsEllipseItem.mouseReleaseEvent(self, a_event)
        f_pos = self.pos()
        f_point = self.item
        f_point.track, f_point.beat, f_point.cc_val = \
            SEQUENCER.get_item_coord(f_pos, a_clip=True)
        self.save_callback()

    def __lt__(self, other):
        return self.pos().x() < other.pos().x()


ATM_CLIPBOARD = []
REGION_CLIPBOARD = []

NO_PEN = QPen(QtCore.Qt.NoPen)
NO_PEN.setWidth(0)

def global_update_track_comboboxes(a_index=None, a_value=None):
    if not a_index is None and not a_value is None:
        TRACK_NAMES[int(a_index)] = str(a_value)
    global SUPPRESS_TRACK_COMBOBOX_CHANGES
    SUPPRESS_TRACK_COMBOBOX_CHANGES = True
    for f_cbox in TRACK_NAME_COMBOBOXES:
        f_current_index = f_cbox.currentIndex()
        f_cbox.clear()
        f_cbox.clearEditText()
        f_cbox.addItems(TRACK_NAMES)
        f_cbox.setCurrentIndex(f_current_index)

    PLUGIN_RACK.set_track_names(TRACK_NAMES)

    SUPPRESS_TRACK_COMBOBOX_CHANGES = False
    ROUTING_GRAPH_WIDGET.draw_graph(
        PROJECT.get_routing_graph(), TRACK_PANEL.get_track_names())
    global_open_mixer()

def pydaw_seconds_to_beats(a_seconds):
    '''converts seconds to regions'''
    return a_seconds * (CURRENT_REGION.get_tempo_at_pos(
        CURRENT_ITEM_REF.start_beat) / 60.0)


class AbstractItemEditor(QGraphicsView):
    """ Base class for things on the "Items" tab.  Over time, more
        functionality should be absorbed into here and standardized
        across the different editors.
    """
    def __init__(self, a_cursor_offset=0.0):
        QGraphicsView.__init__(self)
        self.playback_cursor = None
        self.header = None
        self.cursor_offset = a_cursor_offset
        self.px_per_beat = None
        self.total_height = 2000

    def set_playback_pos(self, a_beat=0.0):
        if not all((CURRENT_ITEM_REF, self.playback_cursor)):
            return
        start = CURRENT_ITEM_REF.start_beat
        self.playback_pos = pydaw_util.pydaw_clip_value(
            float(a_beat) - start, 0.0, CURRENT_ITEM_REF.length_beats)
        f_pos = (self.playback_pos * self.px_per_beat) + self.cursor_offset
        self.playback_cursor.setPos(f_pos, 0.0)

    def draw_header(self, a_header_width, a_header_height):
        self.header = QGraphicsRectItem(
            0, 0, a_header_width, a_header_height)
        if not CURRENT_ITEM_REF:
            return
        self.playback_cursor = self.scene.addLine(
            0.0, 0.0, 0.0, self.total_height, QPen(QtCore.Qt.red, 2.0))
        self.playback_cursor.setZValue(1000.0)
        self.header.mousePressEvent = self.header_click_event
        self.set_playback_pos()

    def header_click_event(self, a_event):
        if not CURRENT_ITEM_REF:
            return
        if not libmk.IS_PLAYING and \
        a_event.button() != QtCore.Qt.RightButton:
            f_beat = int((a_event.scenePos().x() - self.cursor_offset)
                / self.px_per_beat) + CURRENT_ITEM_REF.start_beat
            self.set_playback_pos(f_beat)
            SEQUENCER.set_playback_pos(f_beat)
            TRANSPORT.set_time(f_beat)


class SequencerItem(QGraphicsRectItem):
    """ This is an individual sequencer item within the ItemSequencer
    """
    def __init__(self, a_name, a_audio_item):
        QGraphicsRectItem.__init__(self)
        self.name = str(a_name)
        self.is_deleted = False

        if REGION_EDITOR_MODE == 0:
            self.setFlag(QGraphicsItem.ItemIsMovable)
            self.setFlag(QGraphicsItem.ItemIsSelectable)
            self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        else:
            self.setEnabled(False)
            self.setOpacity(0.2)

        self.setFlag(QGraphicsItem.ItemClipsChildrenToShape)

        self.audio_item = a_audio_item
        self.orig_string = str(a_audio_item)
        self.track_num = a_audio_item.track_num

        self.pixmap_items = []

        if DRAW_SEQUENCER_GRAPHS:
            f_pixmaps, f_transform, self.x_scale, self.y_scale = \
                PROJECT.get_item_path(
                    a_audio_item.item_uid, SEQUENCER_PX_PER_BEAT,
                    REGION_EDITOR_TRACK_HEIGHT,
                    CURRENT_REGION.get_tempo_at_pos(a_audio_item.start_beat))
            for f_pixmap in f_pixmaps:
                f_pixmap_item = QGraphicsPixmapItem(self)
                f_pixmap_item.setCacheMode(
                    QGraphicsItem.DeviceCoordinateCache)
                f_pixmap_item.setPixmap(f_pixmap)
                f_pixmap_item.setTransform(f_transform)
                f_pixmap_item.setZValue(1900.0)
                self.pixmap_items.append(f_pixmap_item)

        self.label = QGraphicsSimpleTextItem(str(a_name), parent=self)
        self.label.setPen(NO_PEN)
        self.label.setBrush(QtCore.Qt.white)

        self.label.setPos(1.0, 1.0)
        self.label.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.label.setZValue(2100.00)

        self.start_handle = QGraphicsRectItem(parent=self)
        self.start_handle.setZValue(2200.0)
        self.start_handle.setAcceptHoverEvents(True)
        self.start_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.start_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.start_handle.setRect(
            QtCore.QRectF(
                0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE, AUDIO_ITEM_HANDLE_HEIGHT))
        self.start_handle.mousePressEvent = self.start_handle_mouseClickEvent
        self.start_handle_line = QGraphicsLineItem(
            0.0, AUDIO_ITEM_HANDLE_HEIGHT, 0.0,
            (REGION_EDITOR_TRACK_HEIGHT * -1.0) + AUDIO_ITEM_HANDLE_HEIGHT,
            self.start_handle)

        self.start_handle_line.setPen(AUDIO_ITEM_LINE_PEN)

        self.length_handle = QGraphicsRectItem(parent=self)
        self.length_handle.setZValue(2200.0)
        self.length_handle.setAcceptHoverEvents(True)
        self.length_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.length_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.length_handle.setRect(
            QtCore.QRectF(0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE,
                          AUDIO_ITEM_HANDLE_HEIGHT))
        self.length_handle.mousePressEvent = self.length_handle_mouseClickEvent
        self.length_handle_line = QGraphicsLineItem(
            AUDIO_ITEM_HANDLE_SIZE, AUDIO_ITEM_HANDLE_HEIGHT,
            AUDIO_ITEM_HANDLE_SIZE,
            (REGION_EDITOR_TRACK_HEIGHT * -1.0) + AUDIO_ITEM_HANDLE_HEIGHT,
            self.length_handle)

        self.stretch_handle = QGraphicsRectItem(parent=self)
        self.stretch_handle.setAcceptHoverEvents(True)
        self.stretch_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.stretch_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.stretch_handle.setRect(
            QtCore.QRectF(0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE,
                          AUDIO_ITEM_HANDLE_HEIGHT))
        self.stretch_handle.mousePressEvent = \
            self.stretch_handle_mouseClickEvent
        self.stretch_handle_line = QGraphicsLineItem(
            AUDIO_ITEM_HANDLE_SIZE,
            (AUDIO_ITEM_HANDLE_HEIGHT * 0.5) -
                (REGION_EDITOR_TRACK_HEIGHT * 0.5),
            AUDIO_ITEM_HANDLE_SIZE,
            (REGION_EDITOR_TRACK_HEIGHT * 0.5) +
                (AUDIO_ITEM_HANDLE_HEIGHT * 0.5),
            self.stretch_handle)
        self.stretch_handle.hide()

        self.split_line = QGraphicsLineItem(
            0.0, 0.0, 0.0, REGION_EDITOR_TRACK_HEIGHT, self)
        self.split_line.mapFromParent(0.0, 0.0)
        self.split_line.hide()
        self.split_line_is_shown = False

        self.setAcceptHoverEvents(True)

        self.is_start_resizing = False
        self.is_resizing = False
        self.is_copying = False
        self.is_fading_in = False
        self.is_fading_out = False
        self.is_stretching = False
        self.set_brush()
        self.waveforms_scaled = False
        self.event_pos_orig = None
        self.width_orig = None
        self.quantize_offset = 0.0
        if libmk.TOOLTIPS_ENABLED:
            self.set_tooltips(True)
        self.draw()

    def itemChange(self, a_change, a_value):
        if a_change == QGraphicsItem.ItemSelectedHasChanged:
            self.set_brush()
        return QGraphicsItem.itemChange(self, a_change, a_value)

    def get_selected_string(self):
        return str(self.audio_item)

    def mouseDoubleClickEvent(self, a_event):
        a_event.setAccepted(True)
        QGraphicsRectItem.mouseDoubleClickEvent(self, a_event)
        global_open_items(
            self.name, a_reset_scrollbar=True, a_new_ref=self.audio_item)
        editors = (CURRENT_ITEM.items, CURRENT_ITEM.notes,
             CURRENT_ITEM.ccs, CURRENT_ITEM.pitchbends)
        current_index = ITEM_EDITOR.tab_widget.currentIndex()
        if current_index < len(editors) and not editors[current_index]:
            for i in range(len(editors)):
                if editors[i]:
                    current_index = i
                    ITEM_EDITOR.tab_widget.setCurrentIndex(current_index)
                    break
        MAIN_WINDOW.main_tabwidget.setCurrentIndex(TAB_ITEM_EDITOR)
        #Ensure that notes are visible
        if current_index == 1 and CURRENT_ITEM.notes:
            height = PIANO_ROLL_EDITOR.geometry().height()
            average = sum(
                x.pos().y() for x in PIANO_ROLL_EDITOR.note_items
                ) / len(PIANO_ROLL_EDITOR.note_items)
            val = int(average - (height * 0.5))
            PIANO_ROLL_EDITOR.verticalScrollBar().setValue(val)

    def generic_hoverEnterEvent(self, a_event):
        if not libmk.IS_PLAYING:
            QApplication.setOverrideCursor(QCursor(QtCore.Qt.SizeHorCursor))

    def generic_hoverLeaveEvent(self, a_event):
        QApplication.restoreOverrideCursor()

    def draw(self):
        f_start = self.audio_item.start_beat * SEQUENCER_PX_PER_BEAT
        f_length = (self.audio_item.length_beats * SEQUENCER_PX_PER_BEAT)

        self.length_orig = f_length
        self.length_px_start = (self.audio_item.start_offset *
            SEQUENCER_PX_PER_BEAT)
        self.length_px_minus_start = f_length - self.length_px_start

        self.rect_orig = QtCore.QRectF(
            0.0, 0.0, f_length, REGION_EDITOR_TRACK_HEIGHT)
        self.setRect(self.rect_orig)

        f_track_num = REGION_EDITOR_HEADER_HEIGHT + (
            REGION_EDITOR_TRACK_HEIGHT * self.audio_item.track_num)

        self.setPos(f_start, f_track_num)
        self.is_moving = False
#        if self.audio_item.time_stretch_mode >= 3 or \
#        (self.audio_item.time_stretch_mode == 2 and \
#        (self.audio_item.timestretch_amt_end ==
#        self.audio_item.timestretch_amt)):
#            self.stretch_width_default = \
#                f_length / self.audio_item.timestretch_amt

        self.sample_start_offset_px = -self.length_px_start

        if DRAW_SEQUENCER_GRAPHS:
            f_offset = 0
            f_offset_inc = project.PIXMAP_TILE_WIDTH * self.x_scale
            for f_pixmap_item in self.pixmap_items:
                f_pixmap_item.setPos(
                    f_offset + self.sample_start_offset_px, 0.0)
                f_offset += f_offset_inc

        self.start_handle_scene_min = f_start + self.sample_start_offset_px
        self.start_handle_scene_max = self.start_handle_scene_min + f_length

        self.length_handle.setPos(
            f_length - AUDIO_ITEM_HANDLE_SIZE,
            REGION_EDITOR_TRACK_HEIGHT - AUDIO_ITEM_HANDLE_HEIGHT)
        self.start_handle.setPos(
            0.0, REGION_EDITOR_TRACK_HEIGHT - AUDIO_ITEM_HANDLE_HEIGHT)
#        if self.audio_item.time_stretch_mode >= 2 and \
#        (((self.audio_item.time_stretch_mode != 5) and \
#        (self.audio_item.time_stretch_mode != 2)) \
#        or (self.audio_item.timestretch_amt_end ==
#        self.audio_item.timestretch_amt)):
#            self.stretch_handle.show()
#            self.stretch_handle.setPos(
#                f_length - AUDIO_ITEM_HANDLE_SIZE,
#                (REGION_EDITOR_TRACK_HEIGHT * 0.5) - \
#                (AUDIO_ITEM_HANDLE_HEIGHT * 0.5))

    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip(libdawnext.strings.sequencer_item)
            self.start_handle.setToolTip(
                _("Use this handle to resize the item by changing "
                "the start point."))
            self.length_handle.setToolTip(
                _("Use this handle to resize the item by "
                "changing the end point."))
            self.stretch_handle.setToolTip(
                _("Use this handle to resize the item by "
                "time-stretching it."))
        else:
            self.setToolTip("")
            self.start_handle.setToolTip("")
            self.length_handle.setToolTip("")
            self.stretch_handle.setToolTip("")

    def clip_at_region_end(self):
        f_current_region_length = pydaw_get_current_region_length()
        f_max_x = f_current_region_length * SEQUENCER_PX_PER_BEAT
        f_pos_x = self.pos().x()
        f_end = f_pos_x + self.rect().width()
        if f_end > f_max_x:
            f_end_px = f_max_x - f_pos_x
            self.setRect(0.0, 0.0, f_end_px, REGION_EDITOR_TRACK_HEIGHT)
            self.audio_item.sample_end = \
                ((self.rect().width() + self.length_px_start) /
                self.length_orig) * 1000.0
            self.audio_item.sample_end = pydaw_util.pydaw_clip_value(
                self.audio_item.sample_end, 1.0, 1000.0, True)
            self.draw()
            return True
        else:
            return False

    def set_brush(self, a_index=None):
        if self.isSelected():
            self.setBrush(pydaw_selected_gradient)
            self.start_handle.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.length_handle.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.stretch_handle.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.split_line.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)

            self.start_handle_line.setPen(AUDIO_ITEM_LINE_SELECTED_PEN)
            self.length_handle_line.setPen(AUDIO_ITEM_LINE_SELECTED_PEN)
            self.stretch_handle_line.setPen(AUDIO_ITEM_LINE_SELECTED_PEN)

            self.label.setBrush(QtCore.Qt.black)
            self.start_handle.setBrush(AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.length_handle.setBrush(AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.stretch_handle.setBrush(AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
        else:
            self.start_handle.setPen(AUDIO_ITEM_HANDLE_PEN)
            self.length_handle.setPen(AUDIO_ITEM_HANDLE_PEN)
            self.stretch_handle.setPen(AUDIO_ITEM_HANDLE_PEN)
            self.split_line.setPen(AUDIO_ITEM_HANDLE_PEN)

            self.start_handle_line.setPen(AUDIO_ITEM_LINE_PEN)
            self.length_handle_line.setPen(AUDIO_ITEM_LINE_PEN)
            self.stretch_handle_line.setPen(AUDIO_ITEM_LINE_PEN)

            self.label.setBrush(QtCore.Qt.white)
            self.start_handle.setBrush(AUDIO_ITEM_HANDLE_BRUSH)
            self.length_handle.setBrush(AUDIO_ITEM_HANDLE_BRUSH)
            self.stretch_handle.setBrush(AUDIO_ITEM_HANDLE_BRUSH)
            if a_index is None:
                self.setBrush(pydaw_track_gradients[
                self.audio_item.track_num % len(pydaw_track_gradients)])
            else:
                self.setBrush(pydaw_track_gradients[
                    a_index % len(pydaw_track_gradients)])

    def pos_to_musical_time(self, a_pos):
        return a_pos / SEQUENCER_PX_PER_BEAT

    def start_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.length_handle, a_event)
        for f_item in SEQUENCER.audio_items:
            if f_item.isSelected():
                f_item.min_start = f_item.pos().x() * -1.0
                f_item.is_start_resizing = True
                f_item.setFlag(
                    QGraphicsItem.ItemClipsChildrenToShape, False)

    def length_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.length_handle, a_event)
        for f_item in SEQUENCER.audio_items:
            if f_item.isSelected():
                f_item.is_resizing = True
                f_item.setFlag(
                    QGraphicsItem.ItemClipsChildrenToShape, False)

    def stretch_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.stretch_handle, a_event)
        f_max_region_pos = (SEQUENCER_PX_PER_BEAT *
            pydaw_get_current_region_length())
        for f_item in SEQUENCER.audio_items:
            if f_item.isSelected() and \
            f_item.audio_item.time_stretch_mode >= 2:
                f_item.is_stretching = True
                f_item.max_stretch = f_max_region_pos - f_item.pos().x()
                f_item.setFlag(
                    QGraphicsItem.ItemClipsChildrenToShape, False)
                #for f_path in f_item.path_items:
                #    f_path.hide()

    def check_selected_status(self):
        """ If a handle is clicked and not selected, clear the selection
            and select only this item
        """
        if not self.isSelected():
            SEQUENCER.scene.clearSelection()
            self.setSelected(True)

    def select_file_instance(self):
        SEQUENCER.scene.clearSelection()
        f_uid = self.audio_item.uid
        for f_item in SEQUENCER.audio_items:
            if f_item.audio_item.uid == f_uid:
                f_item.setSelected(True)

    def sends_dialog(self):
        def ok_handler():
            f_list = [x.audio_item for x in SEQUENCER.audio_items
                if x.isSelected()]
            for f_item in f_list:
                f_item.output_track = f_track_cboxes[0].currentIndex()
                f_item.vol = get_vol(f_track_vols[0].value())
                f_item.s0_sc = f_sc_checkboxes[0].isChecked()
                f_item.send1 = f_track_cboxes[1].currentIndex() - 1
                f_item.s1_vol = get_vol(f_track_vols[1].value())
                f_item.s1_sc = f_sc_checkboxes[1].isChecked()
                f_item.send2 = f_track_cboxes[2].currentIndex() - 1
                f_item.s2_vol = get_vol(f_track_vols[2].value())
                f_item.s2_sc = f_sc_checkboxes[2].isChecked()
            PROJECT.save_region(CURRENT_REGION)
            PROJECT.commit(_("Update sends for sequencer item(s)"))
            f_dialog.close()

        def cancel_handler():
            f_dialog.close()

        def vol_changed(a_val=None):
            for f_vol_label, f_vol_slider in zip(f_vol_labels, f_track_vols):
                f_vol_label.setText(
                    "{}dB".format(get_vol(f_vol_slider.value())))

        def get_vol(a_val):
            return round(a_val * 0.1, 1)

        f_dialog = QDialog(MAIN_WINDOW)
        f_dialog.setWindowTitle(_("Set Volume for all Instance of File"))
        f_layout = QGridLayout(f_dialog)
        f_layout.setAlignment(QtCore.Qt.AlignCenter)
        f_track_cboxes = []
        f_sc_checkboxes = []
        f_track_vols = []
        f_vol_labels = []
        f_current_vals = [
            (self.audio_item.output_track, self.audio_item.vol,
             self.audio_item.s0_sc),
            (self.audio_item.send1, self.audio_item.s1_vol,
             self.audio_item.s1_sc),
            (self.audio_item.send2, self.audio_item.s2_vol,
             self.audio_item.s2_sc)]
        for f_i in range(3):
            f_out, f_vol, f_sc = f_current_vals[f_i]
            f_tracks_combobox = QComboBox()
            f_track_cboxes.append(f_tracks_combobox)
            if f_i == 0:
                f_tracks_combobox.addItems(TRACK_NAMES)
                f_tracks_combobox.setCurrentIndex(f_out)
            else:
                f_tracks_combobox.addItems(["None"] + TRACK_NAMES)
                f_tracks_combobox.setCurrentIndex(f_out + 1)
            f_tracks_combobox.setMinimumWidth(105)
            f_layout.addWidget(f_tracks_combobox, 0, f_i)
            f_sc_checkbox = QCheckBox(_("Sidechain"))
            f_sc_checkboxes.append(f_sc_checkbox)
            if f_sc:
                f_sc_checkbox.setChecked(True)
            f_layout.addWidget(f_sc_checkbox, 1, f_i)
            f_vol_slider = QSlider(QtCore.Qt.Vertical)
            f_track_vols.append(f_vol_slider)
            f_vol_slider.setRange(-240, 240)
            f_vol_slider.setMinimumHeight(360)
            f_vol_slider.valueChanged.connect(vol_changed)
            f_layout.addWidget(f_vol_slider, 2, f_i, QtCore.Qt.AlignCenter)
            f_vol_label = QLabel("0.0dB")
            f_vol_labels.append(f_vol_label)
            f_layout.addWidget(f_vol_label, 3, f_i)
            f_vol_slider.setValue(f_vol * 10.0)

        f_ok_cancel_layout = QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout, 10, 2)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_handler)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.exec_()

    def reset_end(self):
        f_list = SEQUENCER.get_selected()
        for f_item in f_list:
            f_old = f_item.audio_item.start_offset
            f_item.audio_item.start_offset = 0.0
            f_item.audio_item.length_beats += f_old
            self.draw()
            self.clip_at_region_end()
        PROJECT.save_region(CURRENT_REGION)
        PROJECT.commit(_("Reset sample ends for item(s)"))
        global_open_audio_items()

    def mousePressEvent(self, a_event):
        if libmk.IS_PLAYING or a_event.button() == QtCore.Qt.RightButton:
            return

        if a_event.modifiers() == (
        QtCore.Qt.AltModifier | QtCore.Qt.ShiftModifier):
            self.setSelected((not self.isSelected()))
            return

        if not self.isSelected():
            SEQUENCER.scene.clearSelection()
            self.setSelected(True)

        if a_event.modifiers() == QtCore.Qt.ShiftModifier:
            f_item = self.audio_item
            f_item_old = f_item.clone()
            CURRENT_REGION.add_item(f_item_old)
            f_scene_pos = self.quantize(a_event.scenePos().x())
            f_musical_pos = self.pos_to_musical_time(
                f_scene_pos) - f_item_old.start_beat
            f_item.start_beat = f_item.start_beat + f_musical_pos
            f_item.length_beats = f_item_old.length_beats - f_musical_pos
            f_item.start_offset = f_musical_pos + f_item_old.start_offset
            f_item_old.length_beats = f_musical_pos
            PROJECT.save_region(CURRENT_REGION)
            PROJECT.commit(_("Split sequencer item"))
            REGION_SETTINGS.open_region()
        else:
            if a_event.modifiers() == QtCore.Qt.ControlModifier:
                a_event.accept()
            QGraphicsRectItem.mousePressEvent(self, a_event)
            self.event_pos_orig = a_event.pos().x()
            for f_item in SEQUENCER.get_selected():
                f_item_pos = f_item.pos().x()
                f_item.setZValue(2400.0)
                f_item.quantize_offset = \
                    f_item_pos - f_item.quantize_all(f_item_pos)
                if a_event.modifiers() == QtCore.Qt.ControlModifier:
                    f_item.is_copying = True
                    f_item.width_orig = f_item.rect().width()
                    SEQUENCER.draw_item(f_item.name, f_item.audio_item)
                if self.is_start_resizing:
                    f_item.width_orig = 0.0
                else:
                    f_item.width_orig = f_item.rect().width()

    def hoverEnterEvent(self, a_event):
        f_item_pos = self.pos().x()
        self.quantize_offset = f_item_pos - self.quantize_all(f_item_pos)

    def hoverMoveEvent(self, a_event):
        if a_event.modifiers() == QtCore.Qt.ShiftModifier:
            if not self.split_line_is_shown:
                self.split_line_is_shown = True
                self.split_line.show()
            f_x = a_event.pos().x()
            f_x = self.quantize_all(f_x)
            f_x -= self.quantize_offset
            self.split_line.setPos(f_x, 0.0)
        else:
            if self.split_line_is_shown:
                self.split_line_is_shown = False
                self.split_line.hide()

    def hoverLeaveEvent(self, a_event):
        if self.split_line_is_shown:
            self.split_line_is_shown = False
            self.split_line.hide()

    def y_pos_to_lane_number(self, a_y_pos):
        f_lane_num = int((a_y_pos - REGION_EDITOR_HEADER_HEIGHT) /
            REGION_EDITOR_TRACK_HEIGHT)
        f_lane_num = pydaw_clip_value(
            f_lane_num, 0, AUDIO_ITEM_MAX_LANE)
        f_y_pos = (f_lane_num *
            REGION_EDITOR_TRACK_HEIGHT) + REGION_EDITOR_HEADER_HEIGHT
        return f_lane_num, f_y_pos

    def lane_number_to_y_pos(self, a_lane_num):
        a_lane_num = pydaw_util.pydaw_clip_value(
            a_lane_num, 0, project.TRACK_COUNT_ALL)
        return (a_lane_num *
            REGION_EDITOR_TRACK_HEIGHT) + REGION_EDITOR_HEADER_HEIGHT

    def quantize_all(self, a_x):
        f_x = a_x
        if SEQ_QUANTIZE:
            f_x = round(f_x / SEQUENCER_QUANTIZE_PX) * SEQUENCER_QUANTIZE_PX
        return f_x

    def quantize(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        if SEQ_QUANTIZE and f_x < SEQUENCER_QUANTIZE_PX:
            f_x = SEQUENCER_QUANTIZE_PX
        return f_x

    def quantize_start(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        if f_x >= self.length_handle.pos().x():
            f_x -= SEQUENCER_QUANTIZE_PX
        return f_x

    def quantize_scene(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        return f_x

    def mouseMoveEvent(self, a_event):
        if libmk.IS_PLAYING or self.event_pos_orig is None:
            return

        f_event_pos = a_event.pos().x()
        f_event_diff = f_event_pos - self.event_pos_orig

        if self.is_resizing:
            for f_item in SEQUENCER.get_selected():
                f_x = f_item.width_orig + f_event_diff + \
                    f_item.quantize_offset
                f_x = pydaw_clip_min(f_x, AUDIO_ITEM_HANDLE_SIZE)
                f_x = f_item.quantize(f_x)
                f_x -= f_item.quantize_offset
                f_item.length_handle.setPos(
                    f_x - AUDIO_ITEM_HANDLE_SIZE,
                    REGION_EDITOR_TRACK_HEIGHT - AUDIO_ITEM_HANDLE_HEIGHT)
        elif self.is_start_resizing:
            for f_item in SEQUENCER.get_selected():
                f_x = f_item.width_orig + f_event_diff + \
                    f_item.quantize_offset
                f_x = pydaw_clip_value(
                    f_x, f_item.sample_start_offset_px,
                    f_item.length_handle.pos().x())
                f_x = pydaw_clip_min(f_x, f_item.min_start)
                if f_x > f_item.min_start:
                    f_x = f_item.quantize_start(f_x)
                    f_x -= f_item.quantize_offset
                f_item.start_handle.setPos(
                    f_x, REGION_EDITOR_TRACK_HEIGHT -
                        AUDIO_ITEM_HANDLE_HEIGHT)
        elif self.is_stretching:
            for f_item in SEQUENCER.audio_items:
                if f_item.isSelected() and \
                f_item.audio_item.time_stretch_mode >= 2:
                    f_x = f_item.width_orig + f_event_diff + \
                        f_item.quantize_offset
                    f_x = pydaw_clip_value(
                        f_x, f_item.stretch_width_default * 0.1,
                        f_item.stretch_width_default * 200.0)
                    f_x = pydaw_clip_max(f_x, f_item.max_stretch)
                    f_x = f_item.quantize(f_x)
                    f_x -= f_item.quantize_offset
                    f_item.stretch_handle.setPos(
                        f_x - AUDIO_ITEM_HANDLE_SIZE,
                        (REGION_EDITOR_TRACK_HEIGHT * 0.5) -
                        (AUDIO_ITEM_HANDLE_HEIGHT * 0.5))
        else:
            QGraphicsRectItem.mouseMoveEvent(self, a_event)
            if SEQ_QUANTIZE:
                f_max_x = (pydaw_get_current_region_length() *
                    SEQUENCER_PX_PER_BEAT) - SEQUENCER_QUANTIZE_PX
            else:
                f_max_x = (pydaw_get_current_region_length() *
                    SEQUENCER_PX_PER_BEAT) - AUDIO_ITEM_HANDLE_SIZE
            f_new_lane, f_ignored = self.y_pos_to_lane_number(
                a_event.scenePos().y())
            f_lane_offset = f_new_lane - self.audio_item.track_num
            for f_item in SEQUENCER.get_selected():
                f_pos_x = f_item.pos().x()
                f_pos_x = pydaw_clip_value(f_pos_x, 0.0, f_max_x)
                f_pos_y = self.lane_number_to_y_pos(
                    f_lane_offset + f_item.audio_item.track_num)
                f_pos_x = f_item.quantize_scene(f_pos_x)
                f_item.setPos(f_pos_x, f_pos_y)
                if not f_item.is_moving:
                    f_item.is_moving = True
                    # Triggers a bug in Qt5 where the pixmaps in a long
                    # tiled item disappear
                    #f_item.setGraphicsEffect(QGraphicsOpacityEffect())

    def mouseReleaseEvent(self, a_event):
        if libmk.IS_PLAYING or self.event_pos_orig is None:
            return
        f_was_resizing = self.is_resizing
        QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        QApplication.restoreOverrideCursor()
        #Set to True when testing, set to False for better UI performance...
        f_reset_selection = True
        f_did_change = False
        f_was_stretching = False
        f_stretched_items = []
        f_event_pos = a_event.pos().x()
        f_event_diff = f_event_pos - self.event_pos_orig
        f_was_copying = self.is_copying
        if f_was_copying:
            a_event.accept()
        for f_audio_item in SEQUENCER.get_selected():
            f_item = f_audio_item.audio_item
            f_pos_x = pydaw_util.pydaw_clip_min(f_audio_item.pos().x(), 0.0)
            if f_audio_item.is_resizing:
                f_x = (f_audio_item.width_orig + f_event_diff +
                    f_audio_item.quantize_offset)
                f_x = pydaw_clip_min(f_x, AUDIO_ITEM_HANDLE_SIZE)
                f_x = f_audio_item.quantize(f_x)
                f_x -= f_audio_item.quantize_offset
                f_audio_item.setRect(
                    0.0, 0.0, f_x, REGION_EDITOR_TRACK_HEIGHT)
                f_item.length_beats = f_x /SEQUENCER_PX_PER_BEAT
                print(f_item.length_beats)
                f_did_change = True
            elif f_audio_item.is_start_resizing:
                f_x = f_audio_item.start_handle.scenePos().x()
                f_x = pydaw_clip_min(f_x, 0.0)
                f_x = self.quantize_all(f_x)
                if f_x < f_audio_item.sample_start_offset_px:
                    f_x = f_audio_item.sample_start_offset_px
                f_old_start = f_item.start_beat
                f_item.start_beat = self.pos_to_musical_time(f_x)
                f_item.start_offset = ((f_x -
                    f_audio_item.start_handle_scene_min) /
                    (f_audio_item.start_handle_scene_max -
                    f_audio_item.start_handle_scene_min)) * \
                    f_item.length_beats
                f_item.start_offset = pydaw_clip_min(
                    f_item.start_offset, 0.0)
                f_item.length_beats -= f_item.start_beat - f_old_start
            elif f_audio_item.is_stretching and \
            f_item.time_stretch_mode >= 2:
                f_reset_selection = True
                f_x = f_audio_item.width_orig + f_event_diff + \
                    f_audio_item.quantize_offset
                f_x = pydaw_clip_value(
                    f_x, f_audio_item.stretch_width_default * 0.1,
                    f_audio_item.stretch_width_default * 200.0)
                f_x = pydaw_clip_max(f_x, f_audio_item.max_stretch)
                f_x = f_audio_item.quantize(f_x)
                f_x -= f_audio_item.quantize_offset
                f_item.timestretch_amt = \
                    f_x / f_audio_item.stretch_width_default
                f_item.timestretch_amt_end = f_item.timestretch_amt
                if f_item.time_stretch_mode >= 3 and \
                f_audio_item.orig_string != str(f_item):
                    f_was_stretching = True
                    f_ts_result = libmk.PROJECT.timestretch_audio_item(f_item)
                    if f_ts_result is not None:
                        f_stretched_items.append(f_ts_result)
                f_audio_item.setRect(0.0, 0.0, f_x, REGION_EDITOR_TRACK_HEIGHT)
            else:
                f_item.modified = True
                f_pos_y = f_audio_item.pos().y()
                if f_audio_item.is_copying:
                    f_reset_selection = True
                    f_item_old = f_item.clone()
                    CURRENT_REGION.add_item(f_item_old)
                else:
                    f_audio_item.set_brush(f_item.track_num)
                f_pos_x = self.quantize_all(f_pos_x)
                f_item.track_num, f_pos_y = self.y_pos_to_lane_number(f_pos_y)
                f_audio_item.setPos(f_pos_x, f_pos_y)
                f_item.start_beat = f_audio_item.pos_to_musical_time(f_pos_x)
                f_did_change = True
            f_audio_item.clip_at_region_end()
            f_item_str = str(f_item)
            if f_item_str != f_audio_item.orig_string:
                f_audio_item.orig_string = f_item_str
                f_did_change = True
                if not f_reset_selection:
                    f_audio_item.draw()
            f_audio_item.is_moving = False
            f_audio_item.is_resizing = False
            f_audio_item.is_start_resizing = False
            f_audio_item.is_copying = False
            f_audio_item.is_fading_in = False
            f_audio_item.is_fading_out = False
            f_audio_item.is_stretching = False
            f_audio_item.setGraphicsEffect(None)
            f_audio_item.setFlag(QGraphicsItem.ItemClipsChildrenToShape)
        if f_was_resizing:
            global LAST_ITEM_LENGTH
            LAST_ITEM_LENGTH = self.audio_item.length_beats

        if f_did_change:
            #f_audio_items.deduplicate_items()
            if f_was_stretching:
                pass
            PROJECT.save_region(CURRENT_REGION)
            PROJECT.commit(_("Update sequencer items"))
        SEQUENCER.set_selected_strings()
        REGION_SETTINGS.open_region()

LAST_ITEM_LENGTH = 4

class ItemSequencer(QGraphicsView):
    """ This is the sequencer QGraphicsView and QGraphicsScene on
        the "Sequencer" tab
    """
    def __init__(self):
        QGraphicsView.__init__(self)

        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.DontSavePainterState)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing)
        #self.setRenderHint(QPainter.HighQualityAntialiasing)

        # The below code is broken on Qt5.3.<=2, so not using it for
        # now, but this will obviously be quite desirable some day
#        self.opengl_widget = QOpenGLWidget()
#        self.surface_format = QSurfaceFormat()
#        self.surface_format.setRenderableType(QSurfaceFormat.OpenGL)
#        #self.surface_format.setSamples(4)
#        #self.surface_format.setSwapInterval(10)
#        self.opengl_widget.setFormat(self.surface_format)
#        self.setViewport(self.opengl_widget)

        self.ignore_selection_change = False
        self.playback_pos = 0.0
        self.playback_pos_orig = 0.0
        self.selected_item_strings = set()
        self.selected_point_strings = set()
        self.clipboard = []
        self.automation_points = []
        self.region_clipboard = None

        self.atm_select_pos_x = None
        self.atm_select_track = None
        self.atm_delete = False

        self.current_coord = None
        self.current_item = None

        self.reset_line_lists()
        self.h_zoom = 1.0
        self.v_zoom = 1.0
        self.header_y_pos = 0.0
        self.scene = QGraphicsScene(self)
        self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        #self.scene.setItemIndexMethod(QGraphicsScene.BspTreeIndex)
        self.scene.dropEvent = self.sceneDropEvent
        self.scene.dragEnterEvent = self.sceneDragEnterEvent
        self.scene.dragMoveEvent = self.sceneDragMoveEvent
        self.scene.contextMenuEvent = self.sceneContextMenuEvent
        self.scene.setBackgroundBrush(QColor(90, 90, 90))
        #self.scene.selectionChanged.connect(self.highlight_selected)
        self.scene.mouseMoveEvent = self.sceneMouseMoveEvent
        self.scene.mouseReleaseEvent = self.sceneMouseReleaseEvent
        #self.scene.selectionChanged.connect(self.set_selected_strings)
        self.setAcceptDrops(True)
        self.setScene(self.scene)
        self.audio_items = []
        self.track = 0
        self.gradient_index = 0
        self.playback_px = 0.0
        #self.draw_header(0)
        self.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.is_playing = False
        self.reselect_on_stop = []
        self.playback_cursor = None
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.menu = QMenu(self)
        self.atm_menu = QMenu(self)

        self.copy_action = self.menu.addAction(_("Copy"))
        self.copy_action.triggered.connect(self.copy_selected)
        self.copy_action.setShortcut(QKeySequence.Copy)
        self.addAction(self.copy_action)
        self.atm_menu.addAction(self.copy_action)

        self.cut_action = self.menu.addAction(_("Cut"))
        self.cut_action.triggered.connect(self.cut_selected)
        self.cut_action.setShortcut(QKeySequence.Cut)
        self.addAction(self.cut_action)

        self.paste_action = self.atm_menu.addAction(_("Paste"))
        self.paste_action.triggered.connect(self.paste_clipboard)

        self.paste_orig_action = self.menu.addAction(
            _("Paste to Original Track"))
        self.paste_orig_action.triggered.connect(self.paste_clipboard)

        self.paste_ctrl_action = self.atm_menu.addAction(
            _("Paste Plugin Control"))
        self.paste_ctrl_action.triggered.connect(self.paste_atm_point)

        self.smooth_atm_action = self.atm_menu.addAction(
            _("Smooth Selected Points"))
        self.smooth_atm_action.triggered.connect(self.smooth_atm_points)
        self.smooth_atm_action.setShortcut(
            QKeySequence.fromString("ALT+S"))
        self.addAction(self.smooth_atm_action)

        self.track_atm_menu = self.atm_menu.addMenu(
            _("All Plugins for Track"))
        self.track_atm_clipboard = []

        self.copy_track_region_action = self.track_atm_menu.addAction(
            _("Copy Region"))
        self.copy_track_region_action.triggered.connect(
            self.copy_track_region)
        self.paste_track_region_action = self.track_atm_menu.addAction(
            _("Paste Region"))
        self.paste_track_region_action.triggered.connect(
            self.paste_track_region)
        self.track_atm_menu.addSeparator()
        self.clear_track_region_action = self.track_atm_menu.addAction(
            _("Clear Region"))
        self.clear_track_region_action.triggered.connect(
            self.clear_track_region)

        self.atm_clear_menu = self.atm_menu.addMenu(_("Clear All"))

        #self.clear_port_action = self.atm_clear_menu.addAction(
        #    _("Current Control"))
        #self.clear_port_action.triggered.connect(self.clear_port)

        self.atm_clear_menu.addSeparator()
        self.clear_plugin_action = self.atm_clear_menu.addAction(
            _("Current Plugin"))
        self.clear_plugin_action.triggered.connect(self.clear_plugin)

        self.atm_clear_menu.addSeparator()
        self.clear_track_action = self.atm_clear_menu.addAction(
            _("Track"))
        self.clear_track_action.triggered.connect(self.clear_track)

        self.transform_atm_action = self.atm_menu.addAction(_("Transform..."))
        self.transform_atm_action.triggered.connect(self.transform_atm)

        self.lfo_atm_action = self.atm_menu.addAction(_("LFO Tool..."))
        self.lfo_atm_action.triggered.connect(self.lfo_atm)

        self.atm_menu.addSeparator()

        self.delete_action = self.menu.addAction(_("Delete"))
        self.delete_action.triggered.connect(self.delete_selected)
        self.delete_action.setShortcut(QKeySequence.Delete)
        self.addAction(self.delete_action)
        self.atm_menu.addAction(self.delete_action)

        self.menu.addSeparator()

        self.takes_menu = self.menu.addMenu(_("Takes"))
        self.takes_menu.triggered.connect(self.takes_menu_triggered)

        self.unlink_selected_action = self.menu.addAction(
            _("Create New Take for Item(s)"))
        self.unlink_selected_action.setShortcut(
            QKeySequence.fromString("CTRL+U"))
        self.unlink_selected_action.triggered.connect(
            self.on_auto_unlink_selected)
        self.addAction(self.unlink_selected_action)

        self.unlink_unique_action = self.menu.addAction(
            _("Create New Take for Unique Item(s)"))
        self.unlink_unique_action.setShortcut(
            QKeySequence.fromString("ALT+U"))
        self.unlink_unique_action.triggered.connect(self.on_auto_unlink_unique)
        self.addAction(self.unlink_unique_action)

        self.unlink_action = self.menu.addAction(
            _("Create Named Take for Single Item..."))
        self.unlink_action.triggered.connect(self.on_unlink_item)
        self.addAction(self.unlink_action)

        self.menu.addSeparator()

        self.rename_action = self.menu.addAction(
            _("Rename Selected Item(s)..."))
        self.rename_action.triggered.connect(self.on_rename_items)
        self.addAction(self.rename_action)

        self.transpose_action = self.menu.addAction(_("Transpose..."))
        self.transpose_action.triggered.connect(self.transpose_dialog)
        self.addAction(self.transpose_action)

        self.glue_action = self.menu.addAction(_("Glue Selected"))
        self.glue_action.triggered.connect(self.glue_selected)
        self.glue_action.setShortcut(
            QKeySequence.fromString("CTRL+G"))
        self.addAction(self.glue_action)
        self.context_menu_enabled = True

    def clear_port(self):
        if not self.current_coord:
            return
        f_track = self.current_coord[0]
        f_track_port_num, f_track_index = TRACK_PANEL.has_automation(f_track)
        if f_track_port_num is None:
            QMessageBox.warning(
                self, _("Error"),
                _("No automation selected for this track"))
            return
        f_index, f_plugin = TRACK_PANEL.get_atm_params(f_track)
        ATM_REGION.clear_port(f_index, f_track_port_num)
        self.automation_save_callback()
        self.open_region()

    def clear_plugin(self):
        if not self.current_coord:
            return
        f_track = self.current_coord[0]
        f_track_port_num, f_track_index = TRACK_PANEL.has_automation(f_track)
        if f_track_port_num is None:
            QMessageBox.warning(
                self, _("Error"),
                _("No automation selected for this track"))
            return
        f_index, f_plugin = TRACK_PANEL.get_atm_params(f_track)
        ATM_REGION.clear_plugins([f_index])
        self.automation_save_callback()
        self.open_region()

    def clear_track(self):
        if not self.current_coord:
            return
        f_track = self.current_coord[0]
        f_plugins = PROJECT.get_track_plugin_uids(f_track)
        if not f_plugins:
            return
        ATM_REGION.clear_plugins(f_plugins)
        self.automation_save_callback()
        self.open_region()

    def copy_track_region(self):
        if not self.current_coord:
            return
        f_range = self.get_loop_pos()
        if not f_range:
            return
        f_start, f_end = f_range
        f_track = self.current_coord[0]
        f_plugins = PROJECT.get_track_plugin_uids(f_track)
        if not f_plugins:
            return
        self.track_atm_clipboard = ATM_REGION.copy_range_by_plugins(
            f_start, f_end, f_plugins)
        self.automation_save_callback()
        self.open_region()

    def paste_track_region(self):
        if not self.current_coord or not self.track_atm_clipboard:
            return
        f_beat = self.quantize(self.current_coord[1])
        for f_point in (x.clone() for x in self.track_atm_clipboard):
            f_point.beat += f_beat
            ATM_REGION.add_point(f_point)
        self.automation_save_callback()
        self.open_region()

    def clear_track_region(self):
        if not self.current_coord:
            return
        f_range = self.get_loop_pos()
        if not f_range:
            return
        f_start, f_end = f_range
        f_track, f_beat = self.current_coord[:2]
        f_plugins = PROJECT.get_track_plugin_uids(f_track)
        if not f_plugins:
            return
        ATM_REGION.clear_range_by_plugins(f_start, f_end, f_plugins)
        self.automation_save_callback()
        self.open_region()

    def takes_menu_triggered(self, a_action):
        f_uid = self.current_item.audio_item.item_uid
        f_new_uid = a_action.item_uid
        for f_item in self.get_selected_items():
            if f_item.audio_item.item_uid == f_uid:
                f_item_obj = f_item.audio_item
                CURRENT_REGION.remove_item_ref(f_item_obj)
                f_item_obj.uid = f_new_uid
                self.selected_item_strings.add(str(f_item_obj))
                f_item_ref = f_item_obj.clone()
                f_item_ref.item_uid = f_new_uid
                CURRENT_REGION.add_item_ref_by_uid(f_item_ref)
        PROJECT.save_region(CURRENT_REGION)
        PROJECT.commit(_("Change active take"))
        REGION_SETTINGS.open_region()

    def populate_takes_menu(self):
        self.takes_menu.clear()
        if self.current_item:
            f_takes = PROJECT.get_takes()
            f_take_list = f_takes.get_take(
                self.current_item.audio_item.item_uid)
            if f_take_list:
                f_items_dict = PROJECT.get_items_dict()
                for f_uid in f_take_list[1]:
                    f_name = f_items_dict.get_name_by_uid(f_uid)
                    f_action = self.takes_menu.addAction(f_name)
                    f_action.item_uid = f_uid

    def show_context_menu(self):
        if libmk.IS_PLAYING:
            return
        if not self.context_menu_enabled:
            self.context_menu_enabled = True
            return
        if REGION_EDITOR_MODE == 0:
            self.populate_takes_menu()
            self.menu.exec_(QCursor.pos())
        elif REGION_EDITOR_MODE == 1:
            self.atm_menu.exec_(QCursor.pos())
        self.context_menu_enabled = False

    def get_item(self, a_pos):
        for f_item in self.scene.items(a_pos):
            if isinstance(f_item, SequencerItem):
                return f_item
        return None

    def check_header(self, a_pos):
        for f_item in self.scene.items(a_pos):
            if f_item == self.header:
                return True
        return False

    def mousePressEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        f_pos = self.mapToScene(a_event.pos())
        self.current_coord = self.get_item_coord(f_pos)

        if f_pos.x() > self.max_x:
            return

        if self.check_header(f_pos):
            if a_event.button() == QtCore.Qt.LeftButton:
                f_beat = int(f_pos.x() / SEQUENCER_PX_PER_BEAT)
                self.set_playback_pos(f_beat)
                TRANSPORT.set_time(f_beat)
            return

        if a_event.button() == QtCore.Qt.RightButton:
            if self.current_coord:
                if REGION_EDITOR_MODE == 0:
                    self.current_item = self.get_item(f_pos)
                    if self.current_item and \
                    not self.current_item.isSelected():
                        self.scene.clearSelection()
                        self.current_item.setSelected(True)
                        self.selected_item_strings = {
                            self.current_item.get_selected_string()}
                self.show_context_menu()
        elif REGION_EDITOR_MODE == 0:
            self.current_item = self.get_item(f_pos)
            self.setDragMode(QGraphicsView.RubberBandDrag)
            if a_event.modifiers() == QtCore.Qt.ControlModifier:
                f_item = self.get_item(f_pos)
                if f_item:
                    if not f_item.isSelected():
                        self.scene.clearSelection()
                    f_item.setSelected(True)
                    self.selected_item_strings = {f_item.get_selected_string()}
                    QGraphicsView.mousePressEvent(self, a_event)
                    return
                self.scene.clearSelection()
                f_pos_x = f_pos.x()
                f_pos_y = f_pos.y() - REGION_EDITOR_HEADER_HEIGHT
                f_beat = float(f_pos_x // SEQUENCER_PX_PER_BEAT)
                f_track = int(f_pos_y // REGION_EDITOR_TRACK_HEIGHT)
                f_uid = PROJECT.create_empty_item()
                f_item_ref = project.pydaw_sequencer_item(
                    f_track, f_beat, LAST_ITEM_LENGTH, f_uid)
                CURRENT_REGION.add_item_ref_by_uid(f_item_ref)
                self.selected_item_strings = {str(f_item_ref)}
                TRACK_PANEL.tracks[f_track].check_output()
                PROJECT.save_region(CURRENT_REGION)
                PROJECT.commit(_("Add new item"))
                REGION_SETTINGS.open_region()
                return
            elif a_event.modifiers() == QtCore.Qt.ShiftModifier:
                f_item = self.get_item(f_pos)
                if not f_item:
                    self.deleted_items = []
                    region_editor_set_delete_mode(True)
            else:
                f_item = self.get_item(f_pos)
                if f_item:
                    self.selected_item_strings = {
                        f_item.get_selected_string()}
                else:
                    self.clear_selected_item_strings()

        elif REGION_EDITOR_MODE == 1:
            self.setDragMode(QGraphicsView.NoDrag)
            self.atm_select_pos_x = None
            self.atm_select_track = None
            if a_event.modifiers() == QtCore.Qt.ControlModifier or \
            a_event.modifiers() == QtCore.Qt.ShiftModifier:
                self.current_coord = self.get_item_coord(f_pos, True)
                self.scene.clearSelection()
                self.atm_select_pos_x = f_pos.x()
                self.atm_select_track = self.current_coord[0]
                if a_event.modifiers() == QtCore.Qt.ShiftModifier:
                    self.atm_delete = True
                    return
            elif a_event.button() == QtCore.Qt.RightButton:
                pass
            elif self.current_coord is not None:
                f_port, f_index = TRACK_PANEL.has_automation(
                    self.current_coord[0])
                if f_port is not None:
                    f_track, f_beat, f_val = self.current_coord
                    f_point = pydaw_atm_point(
                        f_beat, f_port, f_val,
                        *TRACK_PANEL.get_atm_params(f_track))
                    ATM_REGION.add_point(f_point)
                    self.draw_point(f_point)
                    self.automation_save_callback()
        a_event.accept()
        QGraphicsView.mousePressEvent(self, a_event)

    def sceneMouseMoveEvent(self, a_event):
        QGraphicsScene.mouseMoveEvent(self.scene, a_event)
        if REGION_EDITOR_MODE == 0:
            if REGION_EDITOR_DELETE_MODE:
                f_item = self.get_item(a_event.scenePos())
                if f_item and not f_item.audio_item in self.deleted_items:
                    f_item.hide()
                    self.deleted_items.append(f_item.audio_item)
        elif REGION_EDITOR_MODE == 1:
            if self.atm_select_pos_x is not None:
                f_pos_x = a_event.scenePos().x()
                f_vals = sorted((f_pos_x, self.atm_select_pos_x))
                for f_item in self.get_all_points(self.atm_select_track):
                    f_item_pos_x = f_item.pos().x()
                    if f_item_pos_x >= f_vals[0] and \
                    f_item_pos_x <= f_vals[1]:
                        f_item.setSelected(True)
                    else:
                        f_item.setSelected(False)

    def sceneMouseReleaseEvent(self, a_event):
        if REGION_EDITOR_MODE == 0:
            if REGION_EDITOR_DELETE_MODE:
                region_editor_set_delete_mode(False)
                self.scene.clearSelection()
                self.selected_item_strings = set()
                for f_item in self.deleted_items:
                    CURRENT_REGION.remove_item_ref(f_item)
                PROJECT.save_region(CURRENT_REGION)
                PROJECT.commit("Delete sequencer items")
                self.open_region()
                libmk.clean_wav_pool()
            else:
                QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        elif REGION_EDITOR_MODE == 1:
            if self.atm_delete:
                self.delete_selected_atm(self.atm_select_track)
            QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        else:
            QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        self.atm_select_pos_x = None
        self.atm_select_track = None
        self.atm_delete = False

    def get_item_coord(self, a_pos, a_clip=False):
        f_pos_x = a_pos.x()
        f_pos_y = a_pos.y() - REGION_EDITOR_HEADER_HEIGHT
        if a_clip or (
        f_pos_x > 0 and
        f_pos_y > 0 and
        f_pos_y < REGION_EDITOR_TOTAL_HEIGHT):
            f_pos_x = pydaw_util.pydaw_clip_min(f_pos_x, 0.0)
            f_pos_y = pydaw_util.pydaw_clip_value(
                f_pos_y, 0.0, REGION_EDITOR_TOTAL_HEIGHT)
            f_track_height = REGION_EDITOR_TRACK_HEIGHT - ATM_POINT_DIAMETER
            f_track = int(f_pos_y / REGION_EDITOR_TRACK_HEIGHT)
            f_val = (1.0 - ((f_pos_y - (f_track * REGION_EDITOR_TRACK_HEIGHT))
                / f_track_height)) * 127.0
            f_beat = f_pos_x / SEQUENCER_PX_PER_BEAT
            return f_track, round(f_beat, 6), round(f_val, 6)
        else:
            return None

    def delete_selected_atm(self, a_track):
        self.copy_selected()
        f_selected = list(self.get_selected_points(a_track))
        self.scene.clearSelection()
        self.selected_point_strings = set()
        for f_point in f_selected:
            self.automation_points.remove(f_point)
            ATM_REGION.remove_point(f_point.item)
        self.automation_save_callback()
        self.open_region()

    def get_selected_items(self):
        return [x for x in self.audio_items if x.isSelected()]

    def set_selected_strings(self):
        if self.ignore_selection_change:
            return
        self.selected_item_strings = {x.get_selected_string()
            for x in self.get_selected_items()}

    def clear_selected_item_strings(self):
        self.selected_item_strings = set()

    def set_selected_point_strings(self):
        self.selected_point_strings = {
            str(x.item) for x in self.get_selected_points()}

    def get_all_points(self, a_track=None):
        f_dict = TRACK_PANEL.plugin_uid_map
        if a_track is None:
            for f_point in self.automation_points:
                yield f_point
        else:
            a_track = int(a_track)
            for f_point in self.automation_points:
                if f_dict[f_point.item.index] == a_track:
                    yield f_point

    def get_selected_points(self, a_track=None):
        f_dict = TRACK_PANEL.plugin_uid_map
        if a_track is None:
            for f_point in self.automation_points:
                if f_point.isSelected():
                    yield f_point
        else:
            a_track = int(a_track)
            for f_point in self.automation_points:
                if f_dict[f_point.item.index] == a_track and \
                f_point.isSelected():
                    yield f_point

    def open_region(self):
        if REGION_EDITOR_MODE == 0:
            SEQUENCER.setDragMode(QGraphicsView.NoDrag)
        elif REGION_EDITOR_MODE == 1:
            SEQUENCER.setDragMode(QGraphicsView.RubberBandDrag)
        self.enabled = False
        global ATM_REGION
        ATM_REGION = PROJECT.get_atm_region()
        f_items_dict = PROJECT.get_items_dict()
        f_scrollbar = self.horizontalScrollBar()
        f_scrollbar_value = f_scrollbar.value()
        self.setUpdatesEnabled(False)
        self.clear_drawn_items()
        self.ignore_selection_change = True
        #, key=lambda x: x.bar_num,
        for f_item in sorted(CURRENT_REGION.items, reverse=True):
            if f_item.start_beat < pydaw_get_current_region_length():
                f_item_name = f_items_dict.get_name_by_uid(f_item.item_uid)
                f_new_item = self.draw_item(f_item_name, f_item)
                if f_new_item.get_selected_string() in \
                self.selected_item_strings:
                    f_new_item.setSelected(True)
        self.ignore_selection_change = False
        if REGION_EDITOR_MODE == 1:
            self.open_atm_region()
            TRACK_PANEL.update_ccs_in_use()
        f_scrollbar.setValue(f_scrollbar_value)
        self.setUpdatesEnabled(True)
        self.update()
        self.enabled = True

    def open_atm_region(self):
        for f_track in TRACK_PANEL.tracks:
            f_port, f_index = TRACK_PANEL.has_automation(f_track)
            if f_port is not None:
                for f_point in ATM_REGION.get_points(f_index, f_port):
                    self.draw_point(f_point)

    def reset_line_lists(self):
        self.text_list = []
        self.beat_line_list = []

    def prepare_to_quit(self):
        self.scene.clearSelection()
        self.scene.clear()

    def keyPressEvent(self, a_event):
        #Done this way to prevent the region editor from grabbing the key
        if a_event.key() == QtCore.Qt.Key_Delete:
            self.delete_selected()
        else:
            QGraphicsView.keyPressEvent(self, a_event)
        QApplication.restoreOverrideCursor()

    def set_header_y_pos(self, a_y=None):
        if a_y is not None:
            self.header_y_pos = a_y
        self.header.setPos(0.0, self.header_y_pos - 2.0)

    def get_selected(self):
        return [x for x in self.audio_items if x.isSelected()]

    def delete_selected(self):
        if self.check_running():
            return
        if REGION_EDITOR_MODE == 0:
            f_item_list = self.get_selected()
            if f_item_list:
                for f_item in f_item_list:
                    CURRENT_REGION.remove_item_ref(f_item.audio_item)
                PROJECT.save_region(CURRENT_REGION)
                PROJECT.commit(_("Delete item(s)"))
                REGION_SETTINGS.open_region()
                libmk.clean_wav_pool()
        elif REGION_EDITOR_MODE == 1:
            for f_point in self.get_selected_points():
                ATM_REGION.remove_point(f_point.item)
            self.automation_save_callback()
            self.open_region()

    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip(libdawnext.strings.sequencer)
        else:
            self.setToolTip("")
        for f_item in self.audio_items:
            f_item.set_tooltips(a_on)

    def resizeEvent(self, a_event):
        QGraphicsView.resizeEvent(self, a_event)

    def sceneContextMenuEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        QGraphicsScene.contextMenuEvent(self.scene, a_event)
        self.show_context_menu()

    def highlight_selected(self):
        self.setUpdatesEnabled(False)
        self.has_selected = False
        if REGION_EDITOR_MODE == 0:
            for f_item in self.audio_items:
                f_item.set_brush()
                self.has_selected = True
        elif REGION_EDITOR_MODE == 1:
            for f_item in self.get_all_points():
                f_item.set_brush()
                self.has_selected = True
        self.setUpdatesEnabled(True)
        self.update()

    def sceneDragEnterEvent(self, a_event):
        a_event.setAccepted(True)

    def sceneDragMoveEvent(self, a_event):
        a_event.setDropAction(QtCore.Qt.CopyAction)

    def check_running(self):
        if libmk.IS_PLAYING:
            return True
        return False

    def sceneDropEvent(self, a_event):
        f_pos = a_event.scenePos()
        libmk.APP.setOverrideCursor(QtCore.Qt.WaitCursor)
        if AUDIO_ITEMS_TO_DROP:
            self.add_items(f_pos, AUDIO_ITEMS_TO_DROP)
        elif MIDI_FILES_TO_DROP:
            f_midi_path = MIDI_FILES_TO_DROP[0]
            f_beat, f_lane_num = self.pos_to_beat_and_track(f_pos)
            f_midi = project.DawNextMidiFile(f_midi_path, PROJECT)
            PROJECT.import_midi_file(f_midi, f_beat, f_lane_num)
            PROJECT.commit("Import MIDI file")
            REGION_SETTINGS.open_region()
        libmk.APP.restoreOverrideCursor()

    def quantize(self, a_beat):
        if SEQ_QUANTIZE:
            return int(a_beat * SEQ_QUANTIZE_AMT) / SEQ_QUANTIZE_AMT
        else:
            return a_beat

    def pos_to_beat_and_track(self, a_pos):
        f_beat_frac = (a_pos.x() / SEQUENCER_PX_PER_BEAT)
        f_beat_frac = pydaw_clip_min(f_beat_frac, 0.0)
        f_beat_frac = self.quantize(f_beat_frac)

        f_lane_num = int((a_pos.y() - REGION_EDITOR_HEADER_HEIGHT) /
            REGION_EDITOR_TRACK_HEIGHT)
        f_lane_num = pydaw_clip_value(
            f_lane_num, 0, project.TRACK_COUNT_ALL - 1)

        return f_beat_frac, f_lane_num

    def add_items(self, a_pos, a_item_list):
        if self.check_running():
            return

        f_beat_frac, f_lane_num = self.pos_to_beat_and_track(a_pos)

        f_seconds_per_beat = (60.0 /
            CURRENT_REGION.get_tempo_at_pos(f_beat_frac))

        f_restart = False

        for f_file_name in a_item_list:
            libmk.APP.processEvents()
            f_file_name_str = str(f_file_name)
            f_item_name = os.path.basename(f_file_name_str)
            if f_file_name_str:
                TRACK_PANEL.tracks[f_lane_num].check_output()
                f_item_uid = PROJECT.create_empty_item(f_item_name)
                f_items = PROJECT.get_item_by_uid(f_item_uid)
                f_index = f_items.get_next_index()

                if f_index == -1:
                    QMessageBox.warning(self, _("Error"),
                    _("No more available audio item slots, "
                    "max per region is {}").format(MAX_AUDIO_ITEM_COUNT))
                    break

                f_uid = libmk.PROJECT.get_wav_uid_by_name(f_file_name_str)
                f_graph = libmk.PROJECT.get_sample_graph_by_uid(f_uid)
                f_delta = datetime.timedelta(
                    seconds=f_graph.length_in_seconds)
                if not f_restart and libmk.add_entropy(f_delta):
                    f_restart = True
                f_length = f_graph.length_in_seconds / f_seconds_per_beat
                f_item_ref = project.pydaw_sequencer_item(
                    f_lane_num, f_beat_frac, f_length, f_item_uid)
                CURRENT_REGION.add_item_ref_by_uid(f_item_ref)
                f_item = pydaw_audio_item(
                    f_uid, a_start_bar=0, a_start_beat=0.0, a_lane_num=0)
                f_items.add_item(f_index, f_item)
                PROJECT.save_item_by_uid(f_item_uid, f_items)

                f_lane_num += 1
                if f_lane_num >= project.TRACK_COUNT_ALL:
                    break

        PROJECT.save_region(CURRENT_REGION, a_notify=not f_restart)
        PROJECT.commit("Added audio items")
        REGION_SETTINGS.open_region()
        self.last_open_dir = os.path.dirname(f_file_name_str)

        if f_restart:
            libmk.restart_engine()

    def get_beat_value(self):
        return self.playback_pos

    def set_playback_pos(self, a_beat=0.0):
        f_right = self.sceneRect().right()
        self.playback_pos = float(a_beat)
        if self.playback_pos > f_right:
            return
        f_pos = (self.playback_pos * SEQUENCER_PX_PER_BEAT)
        self.playback_cursor.setPos(f_pos, 0.0)
        if libmk.IS_PLAYING and REGION_SETTINGS.follow_checkbox.isChecked():
            f_port_rect = self.viewport().rect()
            f_rect = self.mapToScene(f_port_rect).boundingRect()
            if not (f_pos > f_rect.left() and f_pos < f_rect.right()):
                f_pos = int(self.playback_pos) * SEQUENCER_PX_PER_BEAT
                REGION_SETTINGS.scrollbar.setValue(int(f_pos))

    def start_playback(self):
        self.playback_pos_orig = self.playback_pos
        if REGION_EDITOR_MODE == 0:
            self.set_selected_strings()
        elif REGION_EDITOR_MODE == 1:
            self.set_selected_point_strings()

    def set_playback_clipboard(self):
        self.reselect_on_stop = []
        for f_item in self.audio_items:
            if f_item.isSelected():
                self.reselect_on_stop.append(str(f_item.audio_item))

    def stop_playback(self):
        self.reset_selection()
        self.set_playback_pos(self.playback_pos_orig)

    def reset_selection(self):
        for f_item in self.audio_items:
            if str(f_item.audio_item) in self.reselect_on_stop:
                f_item.setSelected(True)

    def set_zoom(self, a_scale):
        self.h_zoom = a_scale
        self.update_zoom()

    def set_v_zoom(self, a_scale):
        self.v_zoom = a_scale
        self.update_zoom()

    def update_zoom(self):
        pass
        #pydaw_set_SEQUENCER_zoom(self.h_zoom, self.v_zoom)

    def header_click_event(self, a_event):
        if not libmk.IS_PLAYING and \
        a_event.button() != QtCore.Qt.RightButton:
            f_beat = int(a_event.scenePos().x() / SEQUENCER_PX_PER_BEAT)
            self.set_playback_pos(f_beat)
            TRANSPORT.set_time(f_beat)

    def check_line_count(self):
        """ Check that there are not too many vertical
            lines on the screen
        """
        return

        f_num_count = len(self.text_list)
        if f_num_count == 0:
            return
        f_num_visible_count = int(f_num_count /
            pydaw_clip_min(self.h_zoom, 1))

        if f_num_visible_count > 24:
            for f_line in self.beat_line_list:
                f_line.setVisible(False)
            f_factor = f_num_visible_count // 24
            if f_factor == 1:
                for f_num in self.text_list:
                    f_num.setVisible(True)
            else:
                f_factor = int(round(f_factor / 2.0) * 2)
                for f_num in self.text_list:
                    f_num.setVisible(False)
                for f_num in self.text_list[::f_factor]:
                    f_num.setVisible(True)
        else:
            for f_line in self.beat_line_list:
                f_line.setVisible(True)
            for f_num in self.text_list:
                f_num.setVisible(True)

    def header_time_modify(self):
        def ok_handler():
            f_marker = project.pydaw_tempo_marker(
                self.header_event_pos, f_tempo.value(),
                f_tsig_num.value(), int(str(f_tsig_den.currentText())))
            CURRENT_REGION.set_marker(f_marker)
            PROJECT.save_region(CURRENT_REGION)
            PROJECT.commit(_("Set tempo marker"))
            REGION_SETTINGS.open_region()
            f_window.close()

        def cancel_handler():
            f_marker = CURRENT_REGION.has_marker(self.header_event_pos, 2)
            if f_marker and self.header_event_pos:
                CURRENT_REGION.delete_marker(f_marker)
                PROJECT.save_region(CURRENT_REGION)
                PROJECT.commit(_("Delete tempo marker"))
                REGION_SETTINGS.open_region()
            f_window.close()

        f_window = QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Tempo / Time Signature"))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)

        f_marker = CURRENT_REGION.has_marker(self.header_event_pos, 2)

        f_tempo = QSpinBox()
        f_tempo.setRange(30, 240)
        f_layout.addWidget(QLabel(_("Tempo")), 0, 0)
        f_layout.addWidget(f_tempo, 0, 1)
        f_tsig_layout = QHBoxLayout()
        f_layout.addLayout(f_tsig_layout, 1, 1)
        f_tsig_num = QSpinBox()
        f_tsig_num.setRange(1, 16)
        f_layout.addWidget(QLabel(_("Time Signature")), 1, 0)
        f_tsig_layout.addWidget(f_tsig_num)
        f_tsig_layout.addWidget(QLabel("/"))

        f_tsig_den = QComboBox()
        f_tsig_den.setMinimumWidth(60)
        f_tsig_layout.addWidget(f_tsig_den)
        f_tsig_den.addItems(["2", "4", "8", "16"])

        if f_marker:
            f_tempo.setValue(f_marker.tempo)
            f_tsig_num.setValue(f_marker.tsig_num)
            f_tsig_den.setCurrentIndex(
                f_tsig_den.findText(str(f_marker.tsig_den)))
        else:
            f_tempo.setValue(128)
            f_tsig_num.setValue(4)
            f_tsig_den.setCurrentIndex(1)

        f_ok = QPushButton(_("Save"))
        f_ok.pressed.connect(ok_handler)
        f_layout.addWidget(f_ok, 6, 0)
        if self.header_event_pos:
            f_cancel = QPushButton(_("Delete"))
        else:
            f_cancel = QPushButton(_("Cancel"))
        f_cancel.pressed.connect(cancel_handler)
        f_layout.addWidget(f_cancel, 6, 1)
        f_window.exec_()

    def header_marker_modify(self):
        def ok_handler():
            f_marker = project.pydaw_sequencer_marker(
                self.header_event_pos, f_text.text())
            CURRENT_REGION.set_marker(f_marker)
            PROJECT.save_region(CURRENT_REGION)
            PROJECT.commit(_("Add text marker"))
            REGION_SETTINGS.open_region()
            f_window.close()

        def cancel_handler():
            f_marker = CURRENT_REGION.has_marker(self.header_event_pos, 3)
            if f_marker:
                CURRENT_REGION.delete_marker(f_marker)
                PROJECT.save_region(CURRENT_REGION)
                PROJECT.commit(_("Delete text marker"))
                REGION_SETTINGS.open_region()
            f_window.close()

        f_window = QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Marker"))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)

        f_marker = CURRENT_REGION.has_marker(self.header_event_pos, 3)

        f_text = QLineEdit()
        f_text.setMaxLength(21)

        if f_marker:
            f_text.setText(f_marker.text)

        f_layout.addWidget(QLabel(_("Text")), 0, 0)
        f_layout.addWidget(f_text, 0, 1)
        f_ok_cancel_layout = QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout, 6, 1)
        f_ok = QPushButton(_("Save"))
        f_ok.pressed.connect(ok_handler)
        f_ok_cancel_layout.addWidget(f_ok)
        if CURRENT_REGION.has_marker(self.header_event_pos, 3):
            f_cancel = QPushButton(_("Delete"))
        else:
            f_cancel = QPushButton(_("Cancel"))
        f_cancel.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec_()

    def header_loop_start(self):
        f_tsig_beats = CURRENT_REGION.get_tsig_at_pos(self.header_event_pos)
        if CURRENT_REGION.loop_marker:
            f_end = pydaw_util.pydaw_clip_min(
                CURRENT_REGION.loop_marker.beat,
                self.header_event_pos + f_tsig_beats)
        else:
            f_end = self.header_event_pos + f_tsig_beats

        f_marker = project.pydaw_loop_marker(f_end, self.header_event_pos)
        CURRENT_REGION.set_loop_marker(f_marker)
        PROJECT.save_region(CURRENT_REGION)
        PROJECT.commit(_("Set region start"))
        REGION_SETTINGS.open_region()

    def header_loop_end(self):
        f_tsig_beats = CURRENT_REGION.get_tsig_at_pos(self.header_event_pos)
        CURRENT_REGION.loop_marker.beat = pydaw_util.pydaw_clip_min(
            self.header_event_pos, f_tsig_beats)
        CURRENT_REGION.loop_marker.start_beat = pydaw_util.pydaw_clip_max(
            CURRENT_REGION.loop_marker.start_beat,
            CURRENT_REGION.loop_marker.beat - f_tsig_beats)
        PROJECT.save_region(CURRENT_REGION)
        PROJECT.commit(_("Set region end"))
        REGION_SETTINGS.open_region()

    def headerContextMenuEvent(self, a_event):
        self.context_menu_enabled = False
        self.header_event_pos = int(a_event.pos().x() / SEQUENCER_PX_PER_BEAT)
        f_menu = QMenu(self)
        f_marker_action = f_menu.addAction(_("Text Marker..."))
        f_marker_action.triggered.connect(self.header_marker_modify)
        f_time_modify_action = f_menu.addAction(_("Time/Tempo Marker..."))
        f_time_modify_action.triggered.connect(self.header_time_modify)
        f_menu.addSeparator()
        f_loop_start_action = f_menu.addAction(_("Set Region Start"))
        f_loop_start_action.triggered.connect(self.header_loop_start)
        if CURRENT_REGION.loop_marker:
            f_loop_end_action = f_menu.addAction(_("Set Region End"))
            f_loop_end_action.triggered.connect(self.header_loop_end)
            f_select_region = f_menu.addAction(_("Select Items in Region"))
            f_select_region.triggered.connect(self.select_region_items)
            f_copy_region_action = f_menu.addAction(_("Copy Region"))
            f_copy_region_action.triggered.connect(self.copy_region)
            if self.region_clipboard:
                f_insert_region_action = f_menu.addAction(_("Insert Region"))
                f_insert_region_action.triggered.connect(self.insert_region)
        f_menu.exec_(QCursor.pos())

    def copy_region(self):
        f_region_start = CURRENT_REGION.loop_marker.start_beat
        f_region_end = CURRENT_REGION.loop_marker.beat
        f_region_length = f_region_end - f_region_start
        f_list = [x.audio_item.clone() for x in self.get_region_items()]
        f_atm_list = ATM_REGION.copy_range_all(f_region_start, f_region_end)
        for f_item in f_list:
            f_item.start_beat -= f_region_start
        for f_point in f_atm_list:
            f_point.beat -= f_region_start
        self.region_clipboard = (f_region_length, f_list, f_atm_list)

    def insert_region(self):
        f_region_length, f_list, f_atm_list = self.region_clipboard
        f_list = [x.clone() for x in f_list]
        f_atm_list = [x.clone() for x in f_atm_list]
        CURRENT_REGION.insert_space(self.header_event_pos, f_region_length)
        for f_item in f_list:
            f_item.start_beat += self.header_event_pos
            CURRENT_REGION.add_item_ref_by_uid(f_item)
        for f_point in f_atm_list:
            f_point.beat += self.header_event_pos
            ATM_REGION.add_point(f_point)
        self.automation_save_callback()
        PROJECT.save_region(CURRENT_REGION)
        PROJECT.commit(_("Insert region"))
        REGION_SETTINGS.open_region()

    def get_region_items(self):
        f_region_start = CURRENT_REGION.loop_marker.start_beat
        f_region_end = CURRENT_REGION.loop_marker.beat
        f_result = []
        for f_item in self.audio_items:
            f_seq_item = f_item.audio_item
            f_item_start = f_seq_item.start_beat
            f_item_end = f_item_start + f_seq_item.length_beats
            if f_item_start >= f_region_start and \
            f_item_end <= f_region_end:
                f_result.append(f_item)
        return f_result

    def select_region_items(self):
        self.scene.clearSelection()
        for f_item in self.get_region_items():
            f_item.setSelected(True)

    def get_loop_pos(self, a_warn=True):
        if self.loop_start is None:
            if a_warn:
                QMessageBox.warning(
                    self, _("Error"),
                    _("You must set the region markers first by "
                    "right-clicking on the scene header"))
            return None
        else:
            return self.loop_start, self.loop_end

    def draw_header(self, a_cursor_pos=None):
        self.loop_start = self.loop_end = None
        f_region_length = pydaw_get_current_region_length()
        f_size = SEQUENCER_PX_PER_BEAT * f_region_length
        self.max_x = f_size
        self.setSceneRect(
            -3.0, 0.0, f_size + self.width() + 3.0, REGION_EDITOR_TOTAL_HEIGHT)
        self.header = QGraphicsRectItem(
            0, 0, f_size, REGION_EDITOR_HEADER_HEIGHT)
        self.header.setZValue(1500.0)
        self.header.setBrush(REGION_EDITOR_HEADER_GRADIENT)
        self.header.mousePressEvent = self.header_click_event
        self.header.contextMenuEvent = self.headerContextMenuEvent
        self.scene.addItem(self.header)
        for f_marker in CURRENT_REGION.get_markers():
            if f_marker.type == 1:
                self.loop_start = f_marker.start_beat
                self.loop_end = f_marker.beat
                f_x = f_marker.start_beat * SEQUENCER_PX_PER_BEAT
                f_start = QGraphicsLineItem(
                    f_x, 0, f_x, REGION_EDITOR_HEADER_HEIGHT, self.header)
                f_start.setPen(START_PEN)

                f_x = f_marker.beat * SEQUENCER_PX_PER_BEAT
                f_end = QGraphicsLineItem(
                    f_x, 0, f_x, REGION_EDITOR_HEADER_HEIGHT, self.header)
                f_end.setPen(END_PEN)
            elif f_marker.type == 2:
                f_text = "{} : {}/{}".format(
                    f_marker.tempo, f_marker.tsig_num, f_marker.tsig_den)
                f_item = QGraphicsSimpleTextItem(f_text, self.header)
                f_item.setBrush(QtCore.Qt.white)
                f_item.setPos(
                    f_marker.beat * SEQUENCER_PX_PER_BEAT,
                    REGION_EDITOR_HEADER_ROW_HEIGHT)
                self.draw_region(f_marker)
            elif f_marker.type == 3:
                f_item = QGraphicsSimpleTextItem(
                    f_marker.text, self.header)
                f_item.setBrush(QtCore.Qt.white)
                f_item.setPos(
                    f_marker.beat * SEQUENCER_PX_PER_BEAT,
                    REGION_EDITOR_HEADER_ROW_HEIGHT * 2)
            else:
                assert False, "Invalid marker type"

        f_total_height = (REGION_EDITOR_TRACK_COUNT *
            (REGION_EDITOR_TRACK_HEIGHT)) + REGION_EDITOR_HEADER_HEIGHT
        self.playback_cursor = self.scene.addLine(
            0.0, 0.0, 0.0, f_total_height, QPen(QtCore.Qt.red, 2.0))
        self.playback_cursor.setZValue(1000.0)

        self.set_playback_pos(self.playback_pos)
        self.check_line_count()
        self.set_header_y_pos()

    def draw_region(self, a_marker):
        f_region_length = pydaw_get_current_region_length()
        f_size = SEQUENCER_PX_PER_BEAT * f_region_length
        f_v_pen = QPen(QtCore.Qt.black)
        f_beat_pen = QPen(QColor(210, 210, 210))
        f_16th_pen = QPen(QColor(120, 120, 120))
        f_reg_pen = QPen(QtCore.Qt.white)
        f_total_height = (REGION_EDITOR_TRACK_COUNT *
            (REGION_EDITOR_TRACK_HEIGHT)) + REGION_EDITOR_HEADER_HEIGHT

        f_x_offset = a_marker.beat * SEQUENCER_PX_PER_BEAT
        i3 = f_x_offset

        for i in range(int(a_marker.length)):
            if i % a_marker.tsig_num == 0:
                f_number = QGraphicsSimpleTextItem(
                    str((i // a_marker.tsig_num) + 1), self.header)
                f_number.setFlag(
                    QGraphicsItem.ItemIgnoresTransformations)
                f_number.setBrush(QtCore.Qt.white)
                f_number.setZValue(1000.0)
                self.text_list.append(f_number)
                self.scene.addLine(i3, 0.0, i3, f_total_height, f_v_pen)
                f_number.setPos(i3 + 3.0, 2)
                if SEQ_LINES_ENABLED and DRAW_SEQUENCER_GRAPHS:
                    for f_i4 in range(1, SEQ_SNAP_RANGE):
                        f_sub_x = i3 + (SEQUENCER_QUANTIZE_PX * f_i4)
                        f_line = self.scene.addLine(
                            f_sub_x, REGION_EDITOR_HEADER_HEIGHT,
                            f_sub_x, f_total_height, f_16th_pen)
                        self.beat_line_list.append(f_line)
            elif DRAW_SEQUENCER_GRAPHS:
                f_beat_x = i3
                f_line = self.scene.addLine(
                    f_beat_x, 0.0, f_beat_x, f_total_height, f_beat_pen)
                self.beat_line_list.append(f_line)
                if SEQ_LINES_ENABLED:
                    for f_i4 in range(1, SEQ_SNAP_RANGE):
                        f_sub_x = f_beat_x + (SEQUENCER_QUANTIZE_PX * f_i4)
                        f_line = self.scene.addLine(
                            f_sub_x, REGION_EDITOR_HEADER_HEIGHT,
                            f_sub_x, f_total_height, f_16th_pen)
                        self.beat_line_list.append(f_line)
            i3 += SEQUENCER_PX_PER_BEAT
        self.scene.addLine(
            i3, REGION_EDITOR_HEADER_HEIGHT, i3, f_total_height, f_reg_pen)
        for i2 in range(REGION_EDITOR_TRACK_COUNT):
            f_y = (REGION_EDITOR_TRACK_HEIGHT *
                (i2 + 1)) + REGION_EDITOR_HEADER_HEIGHT
            self.scene.addLine(f_x_offset, f_y, f_size, f_y)

    def clear_drawn_items(self):
        self.reset_line_lists()
        self.audio_items = []
        self.automation_points = []
        self.ignore_selection_change = True
        self.scene.clear()
        self.ignore_selection_change = False
        self.draw_header()

    def draw_item(self, a_name, a_item):
        f_item = SequencerItem(a_name, a_item)
        self.audio_items.append(f_item)
        self.scene.addItem(f_item)
        return f_item

    def draw_point(self, a_point):
        if a_point.index not in TRACK_PANEL.plugin_uid_map:
            print("{} not in {}".format(
                a_point.index, TRACK_PANEL.plugin_uid_map))
            return
        f_track = TRACK_PANEL.plugin_uid_map[a_point.index]
        f_min = (f_track *
            REGION_EDITOR_TRACK_HEIGHT) + REGION_EDITOR_HEADER_HEIGHT
        f_max = f_min + REGION_EDITOR_TRACK_HEIGHT - ATM_POINT_DIAMETER
        f_item = SeqAtmItem(
            a_point, self.automation_save_callback, f_min, f_max)
        self.scene.addItem(f_item)
        f_item.setPos(self.get_pos_from_point(a_point))
        self.automation_points.append(f_item)
        if str(a_point) in self.selected_point_strings:
            f_item.setSelected(True)
        return f_item

    def get_pos_from_point(self, a_point):
        f_track_height = REGION_EDITOR_TRACK_HEIGHT - ATM_POINT_DIAMETER
        f_track = TRACK_PANEL.plugin_uid_map[a_point.index]
        return QtCore.QPointF(
            (a_point.beat * SEQUENCER_PX_PER_BEAT),
            (f_track_height * (1.0 - (a_point.cc_val / 127.0))) +
            (REGION_EDITOR_TRACK_HEIGHT * f_track) +
            REGION_EDITOR_HEADER_HEIGHT)

    def automation_save_callback(self):
        PROJECT.save_atm_region(ATM_REGION)

    def transform_atm_callback(self, a_add, a_mul):
        self.setUpdatesEnabled(False)
        for f_point, f_val in zip(self.atm_selected, self.atm_selected_vals):
            f_val = (f_val * a_mul) + a_add
            f_val = pydaw_util.pydaw_clip_value(f_val, 0.0, 127.0, True)
            f_point.item.cc_val = f_val
            f_point.setPos(self.get_pos_from_point(f_point.item))
        self.setUpdatesEnabled(True)
        self.update()

    def transform_atm(self):
        self.atm_selected = sorted(self.get_selected_points())
        if not self.atm_selected:
            QMessageBox.warning(
                self, _("Error"), _("No automation points selected"))
            return
        f_start_beat = self.atm_selected[0].item.beat
        self.set_playback_pos(f_start_beat)
        f_scrollbar = self.horizontalScrollBar()
        f_scrollbar.setValue(SEQUENCER_PX_PER_BEAT * f_start_beat)

        self.atm_selected_vals = [x.item.cc_val for x in self.atm_selected]

        f_result = pydaw_widgets.add_mul_dialog(
            self.transform_atm_callback, self.automation_save_callback)

        if not f_result:
            for f_point, f_val in zip(
            self.atm_selected, self.atm_selected_vals):
                f_point.item.cc_val = f_val
            self.automation_save_callback()
        self.open_region()

    def lfo_atm_callback(
            self, a_phase, a_start_freq, a_start_amp, a_start_center,
            a_start_fade, a_end_fade, a_end_freq, a_end_amp, a_end_center):
        a_phase, a_start_freq, a_start_fade, a_end_freq, a_end_fade = (
            x * 0.01 for x in
            (a_phase, a_start_freq, a_start_fade, a_end_freq, a_end_fade))
        a_phase *= math.pi
        f_start_beat, f_end_beat = self.get_loop_pos()

        f_length_beats = f_end_beat - f_start_beat
        two_pi = 2.0 * math.pi
        f_start_radians_p64, f_end_radians_p64 = (
            (x * two_pi) / 64.0 for x in (a_start_freq, a_end_freq))
        f_length_beats_recip = 1.0 / f_length_beats

        self.setUpdatesEnabled(False)

        for f_point in self.atm_selected:
            f_pos_beats = f_point.item.beat - f_start_beat
            f_pos = f_pos_beats * f_length_beats_recip
            f_center = pydaw_util.linear_interpolate(
                a_start_center, a_end_center, f_pos)
            f_amp = pydaw_util.linear_interpolate(
                a_start_amp, a_end_amp, f_pos)

            if f_pos < a_start_fade:
                f_amp *= f_pos / a_start_fade
            elif f_pos > a_end_fade:
                f_amp *= 1.0 - (
                    (f_pos - a_end_fade) / (1.0 - a_end_fade))

            f_val = (math.sin(a_phase) * f_amp) + f_center
            f_val = pydaw_util.pydaw_clip_value(f_val, 0.0, 127.0, True)
            f_point.item.cc_val = f_val
            f_point.setPos(self.get_pos_from_point(f_point.item))

            a_phase += pydaw_util.linear_interpolate(
                f_start_radians_p64, f_end_radians_p64, f_pos)
            if a_phase >= two_pi:
                a_phase -= two_pi

        self.setUpdatesEnabled(True)
        self.update()

    def lfo_atm(self):
        if not self.current_coord:
            return
        f_range = self.get_loop_pos()
        if not f_range:
            return
        f_start_beat, f_end_beat = f_range
        if f_end_beat - f_start_beat > 64:
            QMessageBox.warning(
                self, _("Error"),
                _("LFO patterns are limited to 64 beats in length"))
            return
        f_scrollbar = self.horizontalScrollBar()
        f_scrollbar.setValue(SEQUENCER_PX_PER_BEAT * f_start_beat)
        self.set_playback_pos(f_start_beat)
        f_step = 1.0 / 64.0
        f_track, f_beat, f_val = self.current_coord
        f_index, f_plugin = TRACK_PANEL.get_atm_params(f_track)
        if f_index is None:
            QMessageBox.warning(
                self, _("Error"), _("Track has no automation selected"))
            return

        f_port, f_atm_uid = TRACK_PANEL.has_automation(f_track)
        f_old = ATM_REGION.clear_range(
            f_index, f_port, f_start_beat, f_end_beat)
        if f_old:
            self.automation_save_callback()
            self.open_region()
        f_pos = f_start_beat
        self.scene.clearSelection()
        self.atm_selected = []

        for f_i in range(int((f_end_beat - f_start_beat) / f_step)):
            f_point = project.pydaw_atm_point(
                f_pos, f_port, 64.0, f_index, f_plugin)
            ATM_REGION.add_point(f_point)
            f_item = self.draw_point(f_point)
            self.atm_selected.append(f_item)
            f_pos += f_step

        f_result = pydaw_widgets.lfo_dialog(
            self.lfo_atm_callback, self.automation_save_callback)

        if not f_result:
            for f_point in self.atm_selected:
                ATM_REGION.remove_point(f_point.item)
            if f_old:
                for f_point in f_old:
                    ATM_REGION.add_point(f_point)
            self.automation_save_callback()
        self.open_region()

    def smooth_atm_points(self):
        if not self.current_coord:
            return
        f_track, f_beat, f_val = self.current_coord
        f_index, f_plugin = TRACK_PANEL.get_atm_params(f_track)
        if f_index is None:
            return
        f_port, f_index = TRACK_PANEL.has_automation(f_track)
        f_points = [x.item for x in self.get_selected_points()]
        f_is_linear = \
            not REGION_SETTINGS.atm_smoothing_combobox.currentIndex()
        ATM_REGION.smooth_points(
            f_index, f_port, f_plugin, f_points, f_is_linear)
        self.selected_point_strings = set(str(x) for x in f_points)
        self.automation_save_callback()
        self.open_region()

    def transpose_dialog(self):
        if REGION_EDITOR_MODE != 0:
            return
        f_item_set = {x.name for x in self.get_selected_items()}
        if len(f_item_set) == 0:
            QMessageBox.warning(
                MAIN_WINDOW, _("Error"), _("No items selected"))
            return

        def transpose_ok_handler():
            for f_item_name in f_item_set:
                f_item = PROJECT.get_item_by_name(f_item_name)
                f_item.transpose(
                    f_semitone.value(), f_octave.value(),
                    a_selected_only=False,
                    a_duplicate=f_duplicate_notes.isChecked())
                PROJECT.save_item(f_item_name, f_item)
            PROJECT.commit(_("Transpose item(s)"))
            if CURRENT_ITEM:
                global_open_items(CURRENT_ITEM_NAME)
            f_window.close()

        def transpose_cancel_handler():
            f_window.close()

        f_window = QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Transpose"))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)

        f_semitone = QSpinBox()
        f_semitone.setRange(-12, 12)
        f_layout.addWidget(QLabel(_("Semitones")), 0, 0)
        f_layout.addWidget(f_semitone, 0, 1)
        f_octave = QSpinBox()
        f_octave.setRange(-5, 5)
        f_layout.addWidget(QLabel(_("Octaves")), 1, 0)
        f_layout.addWidget(f_octave, 1, 1)
        f_duplicate_notes = QCheckBox(_("Duplicate notes?"))
        f_duplicate_notes.setToolTip(
            _("Checking this box causes the transposed "
            "notes to be added rather than moving the existing notes."))
        f_layout.addWidget(f_duplicate_notes, 2, 1)
        f_ok = QPushButton(_("OK"))
        f_ok.pressed.connect(transpose_ok_handler)
        f_layout.addWidget(f_ok, 6, 0)
        f_cancel = QPushButton(_("Cancel"))
        f_cancel.pressed.connect(transpose_cancel_handler)
        f_layout.addWidget(f_cancel, 6, 1)
        f_window.exec_()

    def glue_selected(self):
        if libmk.IS_PLAYING:
            return
        f_did_something = False
        f_selected = [x.audio_item for x in self.get_selected()]
        for f_i in range(project.TRACK_COUNT_ALL):
            f_track_items = [x for x in f_selected if x.track_num == f_i]
            if len(f_track_items) > 1:
                f_did_something = True
                f_track_items.sort()
                f_new_ref = f_track_items[0].clone()
                f_items_dict = PROJECT.get_items_dict()
                f_old_name = f_items_dict.get_name_by_uid(f_new_ref.item_uid)
                f_new_name = PROJECT.get_next_default_item_name(
                    f_old_name, f_items_dict)
                f_new_uid = PROJECT.create_empty_item(f_new_name)
                f_new_item = PROJECT.get_item_by_uid(f_new_uid)
                f_tempo = CURRENT_REGION.get_tempo_at_pos(f_new_ref.start_beat)
                f_last_ref = f_track_items[-1]
                f_new_ref.item_uid = f_new_uid
                f_new_ref.length_beats = (f_last_ref.start_beat -
                    f_new_ref.start_beat) + f_last_ref.length_beats
                CURRENT_REGION.add_item_ref_by_uid(f_new_ref)
                f_first = True
                for f_ref in f_track_items:
                    f_tempo = CURRENT_REGION.get_tempo_at_pos(f_ref.start_beat)
                    f_item = PROJECT.get_item_by_uid(f_ref.item_uid)
                    f_new_item.extend(f_new_ref, f_ref, f_item, f_tempo)
                    if not f_first:
                        CURRENT_REGION.remove_item_ref(f_ref)
                    else:
                        f_first = False
                pydaw_util.print_sorted_dict(locals())
                PROJECT.save_item(f_new_name, f_new_item)
        if f_did_something:
            PROJECT.save_region(CURRENT_REGION)
            PROJECT.commit(_("Glue sequencer items"))
            REGION_SETTINGS.open_region()
        else:
            QMessageBox.warning(
                MAIN_WINDOW, _("Error"),
                _("You must select at least 2 items on one or more tracks"))


    def cut_selected(self):
        self.copy_selected()
        self.delete_selected()

    def on_rename_items(self):
        if REGION_EDITOR_MODE != 0:
            return
        f_result = []
        for f_item_name in (x.name for x in self.get_selected_items()):
            if not f_item_name in f_result:
                f_result.append(f_item_name)
        if not f_result:
            return

        def ok_handler():
            f_new_name = str(f_new_lineedit.text())
            if f_new_name == "":
                QMessageBox.warning(
                    self.group_box, _("Error"), _("Name cannot be blank"))
                return
            global REGION_CLIPBOARD
            #Clear the clipboard, otherwise the names could be invalid
            REGION_CLIPBOARD = []
            PROJECT.rename_items(f_result, f_new_name)
            PROJECT.commit(_("Rename items"))
            REGION_SETTINGS.open_region()
            if DRAW_LAST_ITEMS:
                global_open_items()
            f_window.close()

        def cancel_handler():
            f_window.close()

        def on_name_changed():
            f_new_lineedit.setText(
                pydaw_remove_bad_chars(f_new_lineedit.text()))

        f_window = QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Rename selected items..."))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)
        f_new_lineedit = QLineEdit()
        f_new_lineedit.editingFinished.connect(on_name_changed)
        f_new_lineedit.setMaxLength(24)
        f_layout.addWidget(QLabel(_("New name:")), 0, 0)
        f_layout.addWidget(f_new_lineedit, 0, 1)
        f_ok_button = QPushButton(_("OK"))
        f_layout.addWidget(f_ok_button, 5, 0)
        f_ok_button.clicked.connect(ok_handler)
        f_cancel_button = QPushButton(_("Cancel"))
        f_layout.addWidget(f_cancel_button, 5, 1)
        f_cancel_button.clicked.connect(cancel_handler)
        f_window.exec_()

    def on_unlink_item(self):
        """ Rename a single instance of an item and
            make it into a new item
        """
        if REGION_EDITOR_MODE != 0:
            return

        if not self.current_coord or not self.current_item:
            return

        f_uid_dict = PROJECT.get_items_dict()
        f_current_item = self.current_item.audio_item

        f_current_item_text = f_uid_dict.get_name_by_uid(
            f_current_item.item_uid)

        def note_ok_handler():
            f_cell_text = str(f_new_lineedit.text())
            if f_cell_text == f_current_item_text:
                QMessageBox.warning(
                    self.group_box, _("Error"),
                    _("You must choose a different name than the "
                    "original item"))
                return
            if PROJECT.item_exists(f_cell_text):
                QMessageBox.warning(
                    self.group_box, _("Error"),
                    _("An item with this name already exists."))
                return
            f_uid = PROJECT.copy_item(
                f_current_item_text, str(f_new_lineedit.text()))
            self.last_item_copied = f_cell_text

            f_item_ref = f_current_item.clone()
            f_takes = PROJECT.get_takes()
            f_takes.add_item(f_current_item.item_uid, f_uid)
            f_item_ref.item_uid = f_uid
            CURRENT_REGION.add_item_ref_by_uid(f_item_ref)
            PROJECT.save_takes(f_takes)
            PROJECT.save_region(CURRENT_REGION)
            PROJECT.commit(
                _("Unlink item '{}' as '{}'").format(
                f_current_item_text, f_cell_text))
            self.open_region()
            f_window.close()

        def note_cancel_handler():
            f_window.close()

        def on_name_changed():
            f_new_lineedit.setText(
                pydaw_remove_bad_chars(f_new_lineedit.text()))

        f_window = QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Copy and unlink item..."))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)
        f_new_lineedit = QLineEdit(f_current_item_text)
        f_new_lineedit.editingFinished.connect(on_name_changed)
        f_new_lineedit.setMaxLength(24)
        f_layout.addWidget(QLabel(_("New name:")), 0, 0)
        f_layout.addWidget(f_new_lineedit, 0, 1)
        f_ok_button = QPushButton(_("OK"))
        f_layout.addWidget(f_ok_button, 5, 0)
        f_ok_button.clicked.connect(note_ok_handler)
        f_cancel_button = QPushButton(_("Cancel"))
        f_layout.addWidget(f_cancel_button, 5, 1)
        f_cancel_button.clicked.connect(note_cancel_handler)
        f_window.exec_()

    def on_auto_unlink_selected(self):
        """ Adds an automatic -N suffix """
        if REGION_EDITOR_MODE != 0:
            return
        f_selected = list(self.get_selected_items())
        if not f_selected:
            return

        f_takes = PROJECT.get_takes()

        self.selected_item_strings = set()
        for f_item in sorted(
        f_selected, key=lambda x:
        (x.audio_item.track_num, x.audio_item.start_beat)):
            f_name_suffix = 1
            while PROJECT.item_exists(
            "{}-{}".format(f_item.name, f_name_suffix)):
                f_name_suffix += 1
            f_cell_text = "{}-{}".format(f_item.name, f_name_suffix)
            f_uid = PROJECT.copy_item(f_item.name, f_cell_text)
            f_item_obj = f_item.audio_item
            f_takes.add_item(f_item_obj.item_uid, f_uid)
            CURRENT_REGION.remove_item_ref(f_item_obj)
            f_item_obj.uid = f_uid
            f_item_ref = f_item_obj.clone()
            f_item_ref.item_uid = f_uid
            self.selected_item_strings.add(str(f_item_ref))
            CURRENT_REGION.add_item_ref_by_uid(f_item_ref)
        PROJECT.save_region(CURRENT_REGION)
        PROJECT.save_takes(f_takes)
        PROJECT.commit(_("Auto-Unlink items"))
        REGION_SETTINGS.open_region()

    def on_auto_unlink_unique(self):
        if REGION_EDITOR_MODE != 0:
            return
        f_result = [(x.name, x.audio_item) for x in self.get_selected_items()]

        if not f_result:
            return

        old_new_map = {}

        f_takes = PROJECT.get_takes()

        for f_item_name in set(x[0] for x in f_result):
            f_name_suffix = 1
            while PROJECT.item_exists(
            "{}-{}".format(f_item_name, f_name_suffix)):
                f_name_suffix += 1
            f_cell_text = "{}-{}".format(f_item_name, f_name_suffix)
            f_uid = PROJECT.copy_item(f_item_name, f_cell_text)
            old_new_map[f_item_name] = f_uid

        self.selected_item_strings = set()

        for k, v in f_result:
            CURRENT_REGION.remove_item_ref(v)
            f_new_uid = old_new_map[k]
            f_takes.add_item(v.item_uid, f_new_uid)
            v.uid = f_new_uid
            f_item_ref = project.pydaw_sequencer_item(
                v.track_num, v.start_beat, v.length_beats, f_new_uid)
            self.selected_item_strings.add(str(f_item_ref))
            CURRENT_REGION.add_item_ref_by_uid(f_item_ref)
        PROJECT.save_region(CURRENT_REGION)
        PROJECT.save_takes(f_takes)
        PROJECT.commit(_("Auto-Unlink unique items"))
        REGION_SETTINGS.open_region()

    def copy_selected(self):
        if not self.enabled:
            self.warn_no_region_selected()
            return
        if REGION_EDITOR_MODE == 0:
            global REGION_CLIPBOARD
            REGION_CLIPBOARD = [x.audio_item.clone() for x in
                self.get_selected_items()]
            if REGION_CLIPBOARD:
                REGION_CLIPBOARD.sort()
                f_start = int(REGION_CLIPBOARD[0].start_beat)
                for f_item in REGION_CLIPBOARD:
                    f_item.start_beat -= f_start
        elif REGION_EDITOR_MODE == 1:
            global ATM_CLIPBOARD
            ATM_CLIPBOARD = [x.item.clone() for x in
                self.get_selected_points(self.current_coord[0])]
            if ATM_CLIPBOARD:
                ATM_CLIPBOARD.sort()
                f_start = int(ATM_CLIPBOARD[0].beat)
                for f_item in ATM_CLIPBOARD:
                    f_item.beat -= f_start

    def paste_clipboard(self):
        if libmk.IS_PLAYING or not self.current_coord:
            return
        self.scene.clearSelection()
        f_track, f_beat, f_val = self.current_coord
        f_beat = int(f_beat)
        if REGION_EDITOR_MODE == 0:
            self.selected_item_strings = set()
            for f_item in REGION_CLIPBOARD:
                f_new_item = f_item.clone()
                f_new_item.start_beat += f_beat
                CURRENT_REGION.add_item_ref_by_uid(f_new_item)
                self.selected_item_strings.add(str(f_new_item))
            PROJECT.save_region(CURRENT_REGION)
            REGION_SETTINGS.open_region()
        elif REGION_EDITOR_MODE == 1:
            f_track_port_num, f_track_index = TRACK_PANEL.has_automation(
                self.current_coord[0])
            if f_track_port_num is None:
                QMessageBox.warning(
                    self, _("Error"),
                    _("No automation selected for this track"))
                return
            f_track_params = TRACK_PANEL.get_atm_params(f_track)
            f_end = ATM_CLIPBOARD[-1].beat + f_beat
            f_point = ATM_CLIPBOARD[0]
            ATM_REGION.clear_range(
                f_point.index, f_point.port_num, f_beat, f_end)
            for f_point in ATM_CLIPBOARD:
                ATM_REGION.add_point(
                    pydaw_atm_point(
                        f_point.beat + f_beat, f_track_port_num,
                        f_point.cc_val, *f_track_params))
            self.automation_save_callback()
            self.open_region()

    def paste_atm_point(self):
        if libmk.IS_PLAYING:
            return
        self.context_menu_enabled = False
        if pydaw_widgets.CC_CLIPBOARD is None:
            QMessageBox.warning(
                self, _("Error"),
                _("Nothing copied to the clipboard.\n"
                "Right-click->'Copy' on any knob on any plugin."))
            return
        f_track, f_beat, f_val = self.current_coord
        f_beat = self.quantize(f_beat)
        f_val = pydaw_widgets.CC_CLIPBOARD
        f_port, f_index = TRACK_PANEL.has_automation(self.current_coord[0])
        if f_port is not None:
            f_point = pydaw_atm_point(
                f_beat, f_port, f_val, *TRACK_PANEL.get_atm_params(f_track))
            ATM_REGION.add_point(f_point)
            self.draw_point(f_point)
            self.automation_save_callback()


def pydaw_set_audio_seq_zoom(a_horizontal, a_vertical):
    global AUDIO_PX_PER_BEAT, AUDIO_ITEM_HEIGHT

    f_width = float(AUDIO_SEQ.rect().width()) - \
        float(AUDIO_SEQ.verticalScrollBar().width()) - 6.0
    f_region_length = CURRENT_ITEM_LEN
    f_region_px = f_region_length * 100.0
    f_region_scale = f_width / f_region_px

    AUDIO_PX_PER_BEAT = 100.0 * a_horizontal * f_region_scale
    AUDIO_SEQ.px_per_beat = AUDIO_PX_PER_BEAT
    pydaw_set_audio_snap(AUDIO_SNAP_VAL)
    AUDIO_ITEM_HEIGHT = 75.0 * a_vertical

SEQUENCER_SNAP_VAL = 3
SEQUENCER_QUANTIZE_PX = SEQUENCER_PX_PER_BEAT
SEQUENCER_QUANTIZE_64TH = SEQUENCER_PX_PER_BEAT / 16.0
SEQ_QUANTIZE = True
SEQ_QUANTIZE_AMT = 1.0
SEQ_LINES_ENABLED = False
SEQ_SNAP_RANGE = 8


def pydaw_set_seq_snap(a_val=None):
    global SEQUENCER_QUANTIZE_PX, SEQ_QUANTIZE, SEQ_QUANTIZE_AMT, \
        SEQ_LINES_ENABLED, SEQ_SNAP_RANGE, SEQUENCER_SNAP_VAL, \
        SEQUENCER_QUANTIZE_64TH
    if a_val is None:
        a_val = SEQUENCER_SNAP_VAL
    else:
        SEQUENCER_SNAP_VAL = a_val
    SEQ_SNAP_RANGE = 8
    f_divisor = ITEM_SNAP_DIVISORS[a_val]
    if a_val > 0:
        SEQ_QUANTIZE = True
        SEQ_LINES_ENABLED = False
    else:
        SEQ_QUANTIZE = False
        SEQ_LINES_ENABLED = False
    SEQUENCER_QUANTIZE_PX = SEQUENCER_PX_PER_BEAT / f_divisor
    SEQUENCER_QUANTIZE_64TH = SEQUENCER_PX_PER_BEAT / 16.0
    SEQ_QUANTIZE_AMT = f_divisor

def pydaw_set_audio_snap(a_val):
    global AUDIO_QUANTIZE, AUDIO_QUANTIZE_PX, AUDIO_QUANTIZE_AMT, \
        AUDIO_SNAP_VAL, AUDIO_LINES_ENABLED, AUDIO_SNAP_RANGE

    AUDIO_SNAP_VAL = a_val
    AUDIO_QUANTIZE = True
    AUDIO_LINES_ENABLED = True
    AUDIO_SNAP_RANGE = 8

    f_divisor = ITEM_SNAP_DIVISORS[a_val]

    AUDIO_QUANTIZE_PX = AUDIO_PX_PER_BEAT / f_divisor
    AUDIO_SNAP_RANGE = int(f_divisor)
    AUDIO_QUANTIZE_AMT = f_divisor

    if a_val == 0:
        AUDIO_QUANTIZE = False
        AUDIO_LINES_ENABLED = False
    elif a_val == 1:
        AUDIO_LINES_ENABLED = False


AUDIO_LINES_ENABLED = True
AUDIO_SNAP_RANGE = 8
AUDIO_SNAP_VAL = 2
AUDIO_PX_PER_BEAT = 100.0

AUDIO_QUANTIZE = False
AUDIO_QUANTIZE_PX = 100.0
AUDIO_QUANTIZE_AMT = 1.0

AUDIO_RULER_HEIGHT = 20.0
AUDIO_ITEM_HEIGHT = 75.0

AUDIO_ITEM_HANDLE_HEIGHT = 12.0
AUDIO_ITEM_HANDLE_SIZE = 6.25

AUDIO_ITEM_HANDLE_BRUSH = QLinearGradient(
    0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE, AUDIO_ITEM_HANDLE_HEIGHT)
AUDIO_ITEM_HANDLE_BRUSH.setColorAt(
    0.0, QColor.fromRgb(255, 255, 255, 120))
AUDIO_ITEM_HANDLE_BRUSH.setColorAt(
    0.0, QColor.fromRgb(255, 255, 255, 90))

AUDIO_ITEM_HANDLE_SELECTED_BRUSH = QLinearGradient(
    0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE, AUDIO_ITEM_HANDLE_HEIGHT)
AUDIO_ITEM_HANDLE_SELECTED_BRUSH.setColorAt(
    0.0, QColor.fromRgb(24, 24, 24, 120))
AUDIO_ITEM_HANDLE_SELECTED_BRUSH.setColorAt(
    0.0, QColor.fromRgb(24, 24, 24, 90))


AUDIO_ITEM_HANDLE_PEN = QPen(QtCore.Qt.white)
AUDIO_ITEM_LINE_PEN = QPen(QtCore.Qt.white, 2.0)
AUDIO_ITEM_HANDLE_SELECTED_PEN = QPen(QColor.fromRgb(24, 24, 24))
AUDIO_ITEM_LINE_SELECTED_PEN = QPen(
    QColor.fromRgb(24, 24, 24), 2.0)

AUDIO_ITEM_MAX_LANE = 23
AUDIO_ITEM_LANE_COUNT = 24

LAST_AUDIO_ITEM_DIR = global_home


def normalize_dialog():
    def on_ok():
        f_window.f_result = f_db_spinbox.value()
        f_window.close()

    def on_cancel():
        f_window.close()

    f_window = QDialog(MAIN_WINDOW)
    f_window.f_result = None
    f_window.setWindowTitle(_("Normalize"))
    f_window.setFixedSize(150, 90)
    f_layout = QVBoxLayout()
    f_window.setLayout(f_layout)
    f_hlayout = QHBoxLayout()
    f_layout.addLayout(f_hlayout)
    f_hlayout.addWidget(QLabel("dB"))
    f_db_spinbox = QDoubleSpinBox()
    f_db_spinbox.setDecimals(1)
    f_hlayout.addWidget(f_db_spinbox)
    f_db_spinbox.setRange(-18, 0)
    f_ok_button = QPushButton(_("OK"))
    f_ok_cancel_layout = QHBoxLayout()
    f_layout.addLayout(f_ok_cancel_layout)
    f_ok_cancel_layout.addWidget(f_ok_button)
    f_ok_button.pressed.connect(on_ok)
    f_cancel_button = QPushButton(_("Cancel"))
    f_ok_cancel_layout.addWidget(f_cancel_button)
    f_cancel_button.pressed.connect(on_cancel)
    f_window.exec_()
    return f_window.f_result

PAINTER_PATH_CACHE = {}

class AudioSeqItem(QGraphicsRectItem):
    """ This is an individual audio item within the AudioItemSeq """
    def __init__(self, a_track_num, a_audio_item, a_graph):
        QGraphicsRectItem.__init__(self)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemClipsChildrenToShape)

        self.sample_length = a_graph.length_in_seconds
        self.graph_object = a_graph
        self.audio_item = a_audio_item
        self.orig_string = str(a_audio_item)
        self.track_num = a_track_num

        f_uid = self.audio_item.uid
        if f_uid in PAINTER_PATH_CACHE:
            self.painter_paths = PAINTER_PATH_CACHE[f_uid]
        else:
            self.painter_paths = a_graph.create_sample_graph(True)
            PAINTER_PATH_CACHE[f_uid] = self.painter_paths

        self.y_inc = AUDIO_ITEM_HEIGHT / len(self.painter_paths)
        f_y_pos = 0.0
        self.path_items = []
        for f_painter_path in self.painter_paths:
            f_path_item = QGraphicsPathItem(f_painter_path)
            f_path_item.setBrush(QtCore.Qt.darkGray)
            f_path_item.setPen(NO_PEN)
            f_path_item.setParentItem(self)
            f_path_item.mapToParent(0.0, 0.0)
            self.path_items.append(f_path_item)
            f_y_pos += self.y_inc
        f_file_name = libmk.PROJECT.get_wav_name_by_uid(
            self.audio_item.uid)
        f_file_name = libmk.PROJECT.timestretch_lookup_orig_path(
            f_file_name)
        f_name_arr = f_file_name.rsplit("/", 1)
        f_name = f_name_arr[-1]
        self.label = QGraphicsSimpleTextItem(f_name, parent=self)
        self.label.setPos(10, (AUDIO_ITEM_HEIGHT * 0.5) -
            (self.label.boundingRect().height() * 0.5))
        self.label.setFlag(QGraphicsItem.ItemIgnoresTransformations)

        self.start_handle = QGraphicsRectItem(parent=self)
        self.start_handle.setAcceptHoverEvents(True)
        self.start_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.start_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.start_handle.setRect(
            QtCore.QRectF(0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE,
                          AUDIO_ITEM_HANDLE_HEIGHT))
        self.start_handle.mousePressEvent = self.start_handle_mouseClickEvent
        self.start_handle_line = QGraphicsLineItem(
            0.0, AUDIO_ITEM_HANDLE_HEIGHT, 0.0,
            (AUDIO_ITEM_HEIGHT * -1.0) + AUDIO_ITEM_HANDLE_HEIGHT,
            self.start_handle)

        self.start_handle_line.setPen(AUDIO_ITEM_LINE_PEN)

        self.length_handle = QGraphicsRectItem(parent=self)
        self.length_handle.setAcceptHoverEvents(True)
        self.length_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.length_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.length_handle.setRect(
            QtCore.QRectF(0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE,
                          AUDIO_ITEM_HANDLE_HEIGHT))
        self.length_handle.mousePressEvent = self.length_handle_mouseClickEvent
        self.length_handle_line = QGraphicsLineItem(
            AUDIO_ITEM_HANDLE_SIZE, AUDIO_ITEM_HANDLE_HEIGHT,
            AUDIO_ITEM_HANDLE_SIZE,
            (AUDIO_ITEM_HEIGHT * -1.0) + AUDIO_ITEM_HANDLE_HEIGHT,
            self.length_handle)

        self.fade_in_handle = QGraphicsRectItem(parent=self)
        self.fade_in_handle.setAcceptHoverEvents(True)
        self.fade_in_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.fade_in_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.fade_in_handle.setRect(
            QtCore.QRectF(0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE,
                          AUDIO_ITEM_HANDLE_HEIGHT))
        self.fade_in_handle.mousePressEvent = \
            self.fade_in_handle_mouseClickEvent
        self.fade_in_handle_line = QGraphicsLineItem(
            0.0, 0.0, 0.0, 0.0, self)

        self.fade_out_handle = QGraphicsRectItem(parent=self)
        self.fade_out_handle.setAcceptHoverEvents(True)
        self.fade_out_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.fade_out_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.fade_out_handle.setRect(
            QtCore.QRectF(0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE,
                          AUDIO_ITEM_HANDLE_HEIGHT))
        self.fade_out_handle.mousePressEvent = \
            self.fade_out_handle_mouseClickEvent
        self.fade_out_handle_line = QGraphicsLineItem(
            0.0, 0.0, 0.0, 0.0, self)

        self.stretch_handle = QGraphicsRectItem(parent=self)
        self.stretch_handle.setAcceptHoverEvents(True)
        self.stretch_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.stretch_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.stretch_handle.setRect(
            QtCore.QRectF(0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE,
                          AUDIO_ITEM_HANDLE_HEIGHT))
        self.stretch_handle.mousePressEvent = \
            self.stretch_handle_mouseClickEvent
        self.stretch_handle_line = QGraphicsLineItem(
            AUDIO_ITEM_HANDLE_SIZE,
            (AUDIO_ITEM_HANDLE_HEIGHT * 0.5) - (AUDIO_ITEM_HEIGHT * 0.5),
            AUDIO_ITEM_HANDLE_SIZE,
            (AUDIO_ITEM_HEIGHT * 0.5) + (AUDIO_ITEM_HANDLE_HEIGHT * 0.5),
            self.stretch_handle)
        self.stretch_handle.hide()

        self.split_line = QGraphicsLineItem(
            0.0, 0.0, 0.0, AUDIO_ITEM_HEIGHT, self)
        self.split_line.mapFromParent(0.0, 0.0)
        self.split_line.hide()
        self.split_line_is_shown = False

        self.setAcceptHoverEvents(True)

        self.is_start_resizing = False
        self.is_resizing = False
        self.is_copying = False
        self.is_fading_in = False
        self.is_fading_out = False
        self.is_stretching = False
        self.set_brush()
        self.waveforms_scaled = False
        self.is_amp_curving = False
        self.is_amp_dragging = False
        self.event_pos_orig = None
        self.width_orig = None
        self.vol_linear = pydaw_db_to_lin(self.audio_item.vol)
        self.quantize_offset = 0.0
        if libmk.TOOLTIPS_ENABLED:
            self.set_tooltips(True)
        self.draw()

    def generic_hoverEnterEvent(self, a_event):
        QApplication.setOverrideCursor(
            QCursor(QtCore.Qt.SizeHorCursor))

    def generic_hoverLeaveEvent(self, a_event):
        QApplication.restoreOverrideCursor()

    def draw(self):
        f_temp_seconds = self.sample_length

        if self.audio_item.time_stretch_mode == 1 and \
        (self.audio_item.pitch_shift_end == self.audio_item.pitch_shift):
            f_temp_seconds /= pydaw_pitch_to_ratio(self.audio_item.pitch_shift)
        elif self.audio_item.time_stretch_mode == 2 and \
        (self.audio_item.timestretch_amt_end ==
        self.audio_item.timestretch_amt):
            f_temp_seconds *= self.audio_item.timestretch_amt

        f_start = self.audio_item.start_beat
        f_start *= AUDIO_PX_PER_BEAT

        f_length_seconds = pydaw_seconds_to_beats(
            f_temp_seconds) * AUDIO_PX_PER_BEAT
        self.length_seconds_orig_px = f_length_seconds
        self.rect_orig = QtCore.QRectF(
            0.0, 0.0, f_length_seconds, AUDIO_ITEM_HEIGHT)
        self.length_px_start = (self.audio_item.sample_start *
            0.001 * f_length_seconds)
        self.length_px_minus_start = f_length_seconds - self.length_px_start
        self.length_px_minus_end = (self.audio_item.sample_end *
            0.001 * f_length_seconds)
        f_length = self.length_px_minus_end - self.length_px_start

        f_track_num = (AUDIO_RULER_HEIGHT +
            AUDIO_ITEM_HEIGHT * self.audio_item.lane_num)

        f_fade_in = self.audio_item.fade_in * 0.001
        f_fade_out = self.audio_item.fade_out * 0.001
        self.setRect(0.0, 0.0, f_length, AUDIO_ITEM_HEIGHT)
        f_fade_in_handle_pos = (f_length * f_fade_in)
        f_fade_in_handle_pos = pydaw_clip_value(
            f_fade_in_handle_pos, 0.0, (f_length - 6.0))
        f_fade_out_handle_pos = \
            (f_length * f_fade_out) - AUDIO_ITEM_HANDLE_SIZE
        f_fade_out_handle_pos = pydaw_clip_value(
            f_fade_out_handle_pos, (f_fade_in_handle_pos + 6.0), f_length)
        self.fade_in_handle.setPos(f_fade_in_handle_pos, 0.0)
        self.fade_out_handle.setPos(f_fade_out_handle_pos, 0.0)
        self.update_fade_in_line()
        self.update_fade_out_line()
        self.setPos(f_start, f_track_num)
        self.is_moving = False
        if self.audio_item.time_stretch_mode >= 3 or \
        (self.audio_item.time_stretch_mode == 2 and \
        (self.audio_item.timestretch_amt_end ==
        self.audio_item.timestretch_amt)):
            self.stretch_width_default = \
                f_length / self.audio_item.timestretch_amt

        self.sample_start_offset_px = (self.audio_item.sample_start *
            -0.001 * self.length_seconds_orig_px)

        self.start_handle_scene_min = f_start + self.sample_start_offset_px
        self.start_handle_scene_max = (self.start_handle_scene_min +
            self.length_seconds_orig_px)

        if not self.waveforms_scaled:
            f_channels = len(self.painter_paths)
            f_i_inc = 1.0 / f_channels
            f_i = f_i_inc
            f_y_inc = 0.0
            # Kludge to fix the problem, there must be a better way...
            if f_channels == 1:
                f_y_offset = \
                    (1.0 - self.vol_linear) * (AUDIO_ITEM_HEIGHT * 0.5)
            else:
                f_y_offset = (1.0 - self.vol_linear) * self.y_inc * f_i_inc
            for f_path_item in self.path_items:
                if self.audio_item.reversed:
                    f_path_item.setPos(
                        self.sample_start_offset_px +
                        self.length_seconds_orig_px,
                        self.y_inc + (f_y_offset * -1.0) + (f_y_inc * f_i))
                    f_path_item.setRotation(-180.0)
                else:
                    f_path_item.setPos(
                        self.sample_start_offset_px,
                        f_y_offset + (f_y_inc * f_i))
                f_x_scale, f_y_scale = pydaw_util.scale_to_rect(
                    mk_project.pydaw_audio_item_scene_rect, self.rect_orig)
                f_y_scale *= self.vol_linear
                f_scale_transform = QTransform()
                f_scale_transform.scale(f_x_scale, f_y_scale)
                f_path_item.setTransform(f_scale_transform)
                f_i += f_i_inc
                f_y_inc += self.y_inc
        self.waveforms_scaled = True

        self.length_handle.setPos(
            f_length - AUDIO_ITEM_HANDLE_SIZE,
            AUDIO_ITEM_HEIGHT - AUDIO_ITEM_HANDLE_HEIGHT)
        self.start_handle.setPos(
            0.0, AUDIO_ITEM_HEIGHT - AUDIO_ITEM_HANDLE_HEIGHT)
        if self.audio_item.time_stretch_mode >= 2 and \
        (((self.audio_item.time_stretch_mode != 5) and \
        (self.audio_item.time_stretch_mode != 2)) \
        or (self.audio_item.timestretch_amt_end ==
        self.audio_item.timestretch_amt)):
            self.stretch_handle.show()
            self.stretch_handle.setPos(
                f_length - AUDIO_ITEM_HANDLE_SIZE,
                (AUDIO_ITEM_HEIGHT * 0.5) - (AUDIO_ITEM_HANDLE_HEIGHT * 0.5))

    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip(libpydaw.strings.AudioSeqItem)
            self.start_handle.setToolTip(
                _("Use this handle to resize the item by changing "
                "the start point."))
            self.length_handle.setToolTip(
                _("Use this handle to resize the item by "
                "changing the end point."))
            self.fade_in_handle.setToolTip(
                _("Use this handle to change the fade in."))
            self.fade_out_handle.setToolTip(
                _("Use this handle to change the fade out."))
            self.stretch_handle.setToolTip(
                _("Use this handle to resize the item by "
                "time-stretching it."))
        else:
            self.setToolTip("")
            self.start_handle.setToolTip("")
            self.length_handle.setToolTip("")
            self.fade_in_handle.setToolTip("")
            self.fade_out_handle.setToolTip("")
            self.stretch_handle.setToolTip("")

    def clip_at_region_end(self):
        f_max_x = CURRENT_ITEM_LEN * AUDIO_PX_PER_BEAT
        f_pos_x = self.pos().x()
        f_end = f_pos_x + self.rect().width()
        if f_end > f_max_x:
            f_end_px = f_max_x - f_pos_x
            self.setRect(0.0, 0.0, f_end_px, AUDIO_ITEM_HEIGHT)
            self.audio_item.sample_end = \
                ((self.rect().width() + self.length_px_start) /
                self.length_seconds_orig_px) * 1000.0
            self.audio_item.sample_end = pydaw_util.pydaw_clip_value(
                self.audio_item.sample_end, 1.0, 1000.0, True)
            self.draw()
            return True
        else:
            return False

    def set_brush(self, a_index=None):
        if self.isSelected():
            self.setBrush(pydaw_selected_gradient)
            self.start_handle.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.length_handle.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.fade_in_handle.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.fade_out_handle.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.stretch_handle.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.split_line.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)

            self.start_handle_line.setPen(AUDIO_ITEM_LINE_SELECTED_PEN)
            self.length_handle_line.setPen(AUDIO_ITEM_LINE_SELECTED_PEN)
            self.fade_in_handle_line.setPen(AUDIO_ITEM_LINE_SELECTED_PEN)
            self.fade_out_handle_line.setPen(AUDIO_ITEM_LINE_SELECTED_PEN)
            self.stretch_handle_line.setPen(AUDIO_ITEM_LINE_SELECTED_PEN)

            self.label.setBrush(QtCore.Qt.darkGray)
            self.start_handle.setBrush(AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.length_handle.setBrush(AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.fade_in_handle.setBrush(AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.fade_out_handle.setBrush(AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.stretch_handle.setBrush(AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
        else:
            self.start_handle.setPen(AUDIO_ITEM_HANDLE_PEN)
            self.length_handle.setPen(AUDIO_ITEM_HANDLE_PEN)
            self.fade_in_handle.setPen(AUDIO_ITEM_HANDLE_PEN)
            self.fade_out_handle.setPen(AUDIO_ITEM_HANDLE_PEN)
            self.stretch_handle.setPen(AUDIO_ITEM_HANDLE_PEN)
            self.split_line.setPen(AUDIO_ITEM_HANDLE_PEN)

            self.start_handle_line.setPen(AUDIO_ITEM_LINE_PEN)
            self.length_handle_line.setPen(AUDIO_ITEM_LINE_PEN)
            self.fade_in_handle_line.setPen(AUDIO_ITEM_LINE_PEN)
            self.fade_out_handle_line.setPen(AUDIO_ITEM_LINE_PEN)
            self.stretch_handle_line.setPen(AUDIO_ITEM_LINE_PEN)

            self.label.setBrush(QtCore.Qt.white)
            self.start_handle.setBrush(AUDIO_ITEM_HANDLE_BRUSH)
            self.length_handle.setBrush(AUDIO_ITEM_HANDLE_BRUSH)
            self.fade_in_handle.setBrush(AUDIO_ITEM_HANDLE_BRUSH)
            self.fade_out_handle.setBrush(AUDIO_ITEM_HANDLE_BRUSH)
            self.stretch_handle.setBrush(AUDIO_ITEM_HANDLE_BRUSH)
            if a_index is None:
                self.setBrush(pydaw_track_gradients[
                self.audio_item.lane_num % len(pydaw_track_gradients)])
            else:
                self.setBrush(pydaw_track_gradients[
                    a_index % len(pydaw_track_gradients)])

    def pos_to_musical_time(self, a_pos):
        return a_pos / AUDIO_PX_PER_BEAT

    def start_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.length_handle, a_event)
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.min_start = f_item.pos().x() * -1.0
                f_item.is_start_resizing = True
                f_item.setFlag(QGraphicsItem.ItemClipsChildrenToShape,
                               False)

    def length_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.length_handle, a_event)
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.is_resizing = True
                f_item.setFlag(QGraphicsItem.ItemClipsChildrenToShape,
                               False)

    def fade_in_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.fade_in_handle, a_event)
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.is_fading_in = True

    def fade_out_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.fade_out_handle, a_event)
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.is_fading_out = True

    def stretch_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.stretch_handle, a_event)
        f_max_region_pos = AUDIO_PX_PER_BEAT * CURRENT_ITEM_LEN
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected() and \
            f_item.audio_item.time_stretch_mode >= 2:
                f_item.is_stretching = True
                f_item.max_stretch = f_max_region_pos - f_item.pos().x()
                f_item.setFlag(
                    QGraphicsItem.ItemClipsChildrenToShape, False)
                #for f_path in f_item.path_items:
                #    f_path.hide()

    def check_selected_status(self):
        """ If a handle is clicked and not selected, clear the selection
            and select only this item
        """
        if not self.isSelected():
            AUDIO_SEQ.scene.clearSelection()
            self.setSelected(True)

    def show_context_menu(self):
        global CURRENT_AUDIO_ITEM_INDEX
        f_CURRENT_AUDIO_ITEM_INDEX = CURRENT_AUDIO_ITEM_INDEX
        CURRENT_AUDIO_ITEM_INDEX = self.track_num
        f_menu = QMenu(MAIN_WINDOW)

        AUDIO_SEQ.context_menu_enabled = False

        f_file_menu = f_menu.addMenu(_("File"))
        f_save_a_copy_action = f_file_menu.addAction(_("Save a Copy..."))
        f_save_a_copy_action.triggered.connect(self.save_a_copy)
        f_open_folder_action = f_file_menu.addAction(_("Open File in Browser"))
        f_open_folder_action.triggered.connect(self.open_item_folder)
        f_wave_editor_action = f_file_menu.addAction(_("Open in Wave Editor"))
        f_wave_editor_action.triggered.connect(self.open_in_wave_editor)
        f_copy_file_path_action = f_file_menu.addAction(
            _("Copy File Path to Clipboard"))
        f_copy_file_path_action.triggered.connect(
            self.copy_file_path_to_clipboard)
        f_select_instance_action = f_file_menu.addAction(
            _("Select All Instances of This File"))
        f_select_instance_action.triggered.connect(self.select_file_instance)
        f_file_menu.addSeparator()
        f_replace_action = f_file_menu.addAction(
            _("Replace with Path in Clipboard"))
        f_replace_action.triggered.connect(self.replace_with_path_in_clipboard)

        f_properties_menu = f_menu.addMenu(_("Properties"))

        f_ts_mode_menu = f_properties_menu.addMenu("Timestretch Mode")
        f_ts_mode_menu.triggered.connect(self.ts_mode_menu_triggered)

        f_ts_modes = {x.audio_item.time_stretch_mode
            for x in AUDIO_SEQ.get_selected()}

        for f_ts_mode in TIMESTRETCH_MODES:
            f_index = pydaw_util.TIMESTRETCH_INDEXES[f_ts_mode]
            f_action = f_ts_mode_menu.addAction(f_ts_mode)
            f_action.algo_name = f_ts_mode
            if len(f_ts_modes) == 1 and f_index in f_ts_modes:
                f_action.setCheckable(True)
                f_action.setChecked(True)

        if len(f_ts_modes) == 1 and [x for x in (3, 4) if x in f_ts_modes]:
            f_crisp_menu = f_properties_menu.addMenu("Crispness")
            f_crisp_menu.triggered.connect(self.crisp_menu_triggered)
            f_crisp_settings = {x.audio_item.crispness
                for x in AUDIO_SEQ.get_selected()}
            for f_crisp_mode, f_index in zip(
            CRISPNESS_SETTINGS, range(len(CRISPNESS_SETTINGS))):
                f_action = f_crisp_menu.addAction(f_crisp_mode)
                f_action.crisp_mode = f_crisp_mode
                if len(f_crisp_settings) == 1 and \
                f_index in f_crisp_settings:
                    f_action.setCheckable(True)
                    f_action.setChecked(True)

        f_output_modes = {x.audio_item.output_track
            for x in AUDIO_SEQ.get_selected()}

        f_output_menu = f_properties_menu.addMenu(_("Output"))
        f_output_menu.triggered.connect(self.output_mode_triggered)
        for f_i, f_name in zip(
        range(3), [_("Normal"), _("Sidechain"), _("Both")]):
            f_action = f_output_menu.addAction(f_name)
            f_action.output_val = f_i
            if len(f_output_modes) == 1 and f_i in f_output_modes:
                f_action.setCheckable(True)
                f_action.setChecked(True)

        f_volume_action = f_properties_menu.addAction(_("Volume..."))
        f_volume_action.triggered.connect(self.volume_dialog)
        f_normalize_action = f_properties_menu.addAction(_("Normalize..."))
        f_normalize_action.triggered.connect(self.normalize_dialog)
        f_reset_fades_action = f_properties_menu.addAction(_("Reset Fades"))
        f_reset_fades_action.triggered.connect(self.reset_fades)
        f_reset_end_action = f_properties_menu.addAction(_("Reset Ends"))
        f_reset_end_action.triggered.connect(self.reset_end)
        f_move_to_end_action = f_properties_menu.addAction(
            _("Move to Region End"))
        f_move_to_end_action.triggered.connect(self.move_to_region_end)
        f_reverse_action = f_properties_menu.addAction(_("Reverse/Unreverse"))
        f_reverse_action.triggered.connect(self.reverse)
        f_time_pitch_action = f_properties_menu.addAction(_("Time/Pitch..."))
        f_time_pitch_action.triggered.connect(self.time_pitch_dialog)
        f_fade_vol_action = f_properties_menu.addAction(_("Fade Volume..."))
        f_fade_vol_action.triggered.connect(self.fade_vol_dialog)

        f_paif_menu = f_menu.addMenu(_("Per-Item FX"))
        f_edit_paif_action = f_paif_menu.addAction(_("Edit Per-Item Effects"))
        f_edit_paif_action.triggered.connect(self.edit_paif)
        f_paif_menu.addSeparator()
        f_paif_copy = f_paif_menu.addAction(_("Copy"))
        f_paif_copy.triggered.connect(
            AUDIO_SEQ_WIDGET.on_modulex_copy)
        f_paif_paste = f_paif_menu.addAction(_("Paste"))
        f_paif_paste.triggered.connect(
            AUDIO_SEQ_WIDGET.on_modulex_paste)
        f_paif_clear = f_paif_menu.addAction(_("Clear"))
        f_paif_clear.triggered.connect(
            AUDIO_SEQ_WIDGET.on_modulex_clear)

#        f_per_file_menu = f_menu.addMenu("For All Instances of This File Set")
#        f_all_volumes_action = f_per_file_menu.addAction(_("Volume..."))
#        f_all_volumes_action.triggered.connect(self.set_vol_for_all_instances)
#        f_all_fades_action = f_per_file_menu.addAction(_("Fades"))
#        f_all_fades_action.triggered.connect(self.set_fades_for_all_instances)
#        f_all_paif_action = f_per_file_menu.addAction(_("Per-Item FX"))
#        f_all_paif_action.triggered.connect(self.set_paif_for_all_instance)
#
#        f_groove_menu = f_menu.addMenu(_("Groove"))
#        f_copy_as_cc_action = f_groove_menu.addAction(
#            _("Copy Volume Envelope as CC Automation"))
#        f_copy_as_cc_action.triggered.connect(
#            self.copy_as_cc_automation)
#        f_copy_as_pb_action = f_groove_menu.addAction(
#            _("Copy Volume Envelope as Pitchbend Automation"))
#        f_copy_as_pb_action.triggered.connect(
#            self.copy_as_pb_automation)
#        f_copy_as_notes_action = f_groove_menu.addAction(
#            _("Copy Volume Envelope as MIDI Notes"))
#        f_copy_as_notes_action.triggered.connect(self.copy_as_notes)

        f_menu.exec_(QCursor.pos())
        CURRENT_AUDIO_ITEM_INDEX = f_CURRENT_AUDIO_ITEM_INDEX

    def output_mode_triggered(self, a_action):
        f_list = AUDIO_SEQ.get_selected()
        for f_item in f_list:
            f_item.audio_item.output_track = a_action.output_val
        PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
        PROJECT.commit(_("Set audio items output mode"))
        global_open_audio_items(True)


    def time_pitch_dialog(self):
        f_dialog = time_pitch_dialog_widget(self.audio_item)
        f_dialog.widget.exec_()

    def fade_vol_dialog(self):
        f_dialog = fade_vol_dialog_widget(self.audio_item)
        f_dialog.widget.exec_()

    def copy_as_cc_automation(self):
        CC_EDITOR.clipboard = en_project.envelope_to_automation(
            self.graph_object, True, TRANSPORT.tempo_spinbox.value())

    def copy_as_pb_automation(self):
        PB_EDITOR.clipboard = en_project.envelope_to_automation(
            self.graph_object, False, TRANSPORT.tempo_spinbox.value())

    def copy_as_notes(self):
        PIANO_ROLL_EDITOR.clipboard = en_project.envelope_to_notes(
            self.graph_object, TRANSPORT.tempo_spinbox.value())

    def crisp_menu_triggered(self, a_action):
        f_index = CRISPNESS_SETTINGS.index(a_action.crisp_mode)
        f_list = [x.audio_item for x in AUDIO_SEQ.get_selected() if
            x.audio_item.time_stretch_mode in (3, 4)]
        for f_item in f_list:
            f_item.crispness = f_index
        self.timestretch_items(f_list)

    def ts_mode_menu_triggered(self, a_action):
        f_index = TIMESTRETCH_INDEXES[a_action.algo_name]
        f_list = [x.audio_item for x in AUDIO_SEQ.get_selected()]
        for f_item in f_list:
            f_item.time_stretch_mode = f_index
        self.timestretch_items(f_list)

    def timestretch_items(self, a_list):
        f_stretched_items = []
        for f_item in a_list:
            if f_item.time_stretch_mode >= 3:
                f_ts_result = libmk.PROJECT.timestretch_audio_item(f_item)
                if f_ts_result is not None:
                    f_stretched_items.append(f_ts_result)

        libmk.PROJECT.save_stretch_dicts()

        for f_stretch_item in f_stretched_items:
            f_stretch_item[2].wait()
            libmk.PROJECT.get_wav_uid_by_name(
                f_stretch_item[0], a_uid=f_stretch_item[1])
        for f_audio_item in AUDIO_SEQ.get_selected():
            f_new_graph = libmk.PROJECT.get_sample_graph_by_uid(
                f_audio_item.audio_item.uid)
            f_audio_item.audio_item.clip_at_region_end(
                pydaw_get_current_region_length(),
                CURRENT_REGION.get_tempo_at_pos(CURRENT_ITEM_REF.start_beat),
                f_new_graph.length_in_seconds)

        PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
        PROJECT.commit(_("Change timestretch mode for audio item(s)"))
        global_open_audio_items()

    def select_file_instance(self):
        AUDIO_SEQ.scene.clearSelection()
        f_uid = self.audio_item.uid
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.audio_item.uid == f_uid:
                f_item.setSelected(True)

    def set_paif_for_all_instance(self):
        f_paif = PROJECT.get_audio_per_item_fx_region(
            CURRENT_REGION.uid)
        f_paif_row = f_paif.get_row(self.track_num)
        PROJECT.set_paif_for_all_audio_items(
            self.audio_item.uid, f_paif_row)

    def set_fades_for_all_instances(self):
        PROJECT.set_fades_for_all_audio_items(self.audio_item)
        global_open_audio_items()

    def set_vol_for_all_instances(self):
        def ok_handler():
            f_index = f_reverse_combobox.currentIndex()
            f_reverse_val = None
            if f_index == 1:
                f_reverse_val = False
            elif f_index == 2:
                f_reverse_val = True
            PROJECT.set_vol_for_all_audio_items(
                self.audio_item.uid, get_vol(), f_reverse_val,
                f_same_vol_checkbox.isChecked(), self.audio_item.vol)
            f_dialog.close()
            global_open_audio_items()

        def cancel_handler():
            f_dialog.close()

        def vol_changed(a_val=None):
            f_vol_label.setText("{}dB".format(get_vol()))

        def get_vol():
            return round(f_vol_slider.value() * 0.1, 1)

        f_dialog = QDialog(MAIN_WINDOW)
        f_dialog.setWindowTitle(_("Set Volume for all Instance of File"))
        f_layout = QGridLayout(f_dialog)
        f_layout.setAlignment(QtCore.Qt.AlignCenter)
        f_vol_slider = QSlider(QtCore.Qt.Vertical)
        f_vol_slider.setRange(-240, 240)
        f_vol_slider.setMinimumHeight(360)
        f_vol_slider.valueChanged.connect(vol_changed)
        f_layout.addWidget(f_vol_slider, 0, 1, QtCore.Qt.AlignCenter)
        f_vol_label = QLabel("0dB")
        f_layout.addWidget(f_vol_label, 1, 1)
        f_vol_slider.setValue(self.audio_item.vol)
        f_reverse_combobox = QComboBox()
        f_reverse_combobox.addItems(
            [_("Either"), _("Not-Reversed"), _("Reversed")])
        f_reverse_combobox.setMinimumWidth(105)
        f_layout.addWidget(QLabel(_("Reversed Items?")), 2, 0)
        f_layout.addWidget(f_reverse_combobox, 2, 1)
        f_same_vol_checkbox = QCheckBox(
            _("Only items with same volume?"))
        f_layout.addWidget(f_same_vol_checkbox, 3, 1)
        f_ok_cancel_layout = QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout, 10, 1)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_handler)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.exec_()

    def reverse(self):
        f_list = AUDIO_SEQ.get_selected()
        for f_item in f_list:
            f_item.audio_item.reversed = not f_item.audio_item.reversed
        PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
        PROJECT.commit(_("Toggle audio items reversed"))
        global_open_audio_items(True)

    def move_to_region_end(self):
        f_list = AUDIO_SEQ.get_selected()
        if f_list:
            f_current_region_length = pydaw_get_current_region_length()
            f_global_tempo = CURRENT_REGION.get_tempo_at_pos(
                CURRENT_ITEM_REF.start_beat)
            for f_item in f_list:
                f_item.audio_item.clip_at_region_end(
                    f_current_region_length, f_global_tempo,
                    f_item.graph_object.length_in_seconds, False)
            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
            PROJECT.commit(_("Move audio item(s) to region end"))
            global_open_audio_items(True)

    def reset_fades(self):
        f_list = AUDIO_SEQ.get_selected()
        if f_list:
            for f_item in f_list:
                f_item.audio_item.fade_in = 0.0
                f_item.audio_item.fade_out = 999.0
            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
            PROJECT.commit(_("Reset audio item fades"))
            global_open_audio_items(True)

    def reset_end(self):
        f_list = AUDIO_SEQ.get_selected()
        for f_item in f_list:
            f_item.audio_item.sample_start = 0.0
            f_item.audio_item.sample_end = 1000.0
            self.draw()
            self.clip_at_region_end()
        PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
        PROJECT.commit(_("Reset sample ends for audio item(s)"))
        global_open_audio_items()

    def replace_with_path_in_clipboard(self):
        f_path = global_get_audio_file_from_clipboard()
        if f_path is not None:
            self.audio_item.uid = libmk.PROJECT.get_wav_uid_by_name(f_path)
            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
            PROJECT.commit(_("Replace audio item"))
            global_open_audio_items(True)

    def open_in_wave_editor(self):
        f_path = self.get_file_path()
        libmk.MAIN_WINDOW.open_in_wave_editor(f_path)

    def edit_paif(self):
        AUDIO_SEQ.scene.clearSelection()
        self.setSelected(True)
        AUDIO_SEQ_WIDGET.folders_tab_widget.setCurrentIndex(2)

    def normalize(self, a_value):
        f_val = self.graph_object.normalize(a_value)
        self.audio_item.vol = f_val

    def volume_dialog(self):
        def on_ok():
            f_val = round(f_db_spinbox.value(), 1)
            for f_item in AUDIO_SEQ.get_selected():
                f_item.audio_item.vol = f_val
            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
            PROJECT.commit(_("Normalize audio items"))
            global_open_audio_items(True)
            f_window.close()

        def on_cancel():
            f_window.close()

        f_window = QDialog(MAIN_WINDOW)
        f_window.f_result = None
        f_window.setWindowTitle(_("Volume"))
        f_window.setFixedSize(150, 90)
        f_layout = QVBoxLayout()
        f_window.setLayout(f_layout)
        f_hlayout = QHBoxLayout()
        f_layout.addLayout(f_hlayout)
        f_hlayout.addWidget(QLabel("dB"))
        f_db_spinbox = QDoubleSpinBox()
        f_hlayout.addWidget(f_db_spinbox)
        f_db_spinbox.setDecimals(1)
        f_db_spinbox.setRange(-24, 24)
        f_vols = {x.audio_item.vol for x in AUDIO_SEQ.get_selected()}
        if len(f_vols) == 1:
            f_db_spinbox.setValue(f_vols.pop())
        else:
            f_db_spinbox.setValue(0)
        f_ok_button = QPushButton(_("OK"))
        f_ok_cancel_layout = QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_ok_button.pressed.connect(on_ok)
        f_cancel_button = QPushButton(_("Cancel"))
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_cancel_button.pressed.connect(on_cancel)
        f_window.exec_()
        return f_window.f_result


    def normalize_dialog(self):
        f_val = normalize_dialog()
        if f_val is None:
            return
        f_save = False
        for f_item in AUDIO_SEQ.get_selected():
            f_save = True
            f_item.normalize(f_val)
        if f_save:
            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
            PROJECT.commit(_("Normalize audio items"))
            global_open_audio_items(True)

    def get_file_path(self):
        return libmk.PROJECT.get_wav_path_by_uid(self.audio_item.uid)

    def copy_file_path_to_clipboard(self):
        f_path = self.get_file_path()
        f_clipboard = QApplication.clipboard()
        f_clipboard.setText(f_path)

    def save_a_copy(self):
        global LAST_AUDIO_ITEM_DIR
        f_file, f_filter = QFileDialog.getSaveFileName(
            parent=AUDIO_SEQ,
            caption=_('Save audio item as .wav'),
            directory=LAST_AUDIO_ITEM_DIR)
        if not f_file is None and not str(f_file) == "":
            f_file = str(f_file)
            if not f_file.endswith(".wav"):
                f_file += ".wav"
            LAST_AUDIO_ITEM_DIR = os.path.dirname(f_file)
            f_orig_path = libmk.PROJECT.get_wav_name_by_uid(
                self.audio_item.uid)
            shutil.copy(f_orig_path, f_file)

    def open_item_folder(self):
        f_path = libmk.PROJECT.get_wav_name_by_uid(self.audio_item.uid)
        AUDIO_SEQ_WIDGET.open_file_in_browser(f_path)

    def mousePressEvent(self, a_event):
        if libmk.IS_PLAYING:
            return

        if a_event.modifiers() == (QtCore.Qt.AltModifier |
        QtCore.Qt.ShiftModifier):
            self.setSelected((not self.isSelected()))
            return

        if not self.isSelected():
            AUDIO_SEQ.scene.clearSelection()
            self.setSelected(True)

        if a_event.button() == QtCore.Qt.RightButton:
            self.show_context_menu()
            return

        if a_event.modifiers() == QtCore.Qt.ShiftModifier:
            f_item = self.audio_item
            f_item_old = f_item.clone()
            f_item.fade_in = 0.0
            f_item_old.fade_out = 999.0
            f_width_percent = a_event.pos().x() / self.rect().width()
            f_item.fade_out = pydaw_clip_value(
                f_item.fade_out, (f_item.fade_in + 90.0), 999.0, True)
            f_item_old.fade_in /= f_width_percent
            f_item_old.fade_in = pydaw_clip_value(
                f_item_old.fade_in, 0.0, (f_item_old.fade_out - 90.0), True)

            f_index = CURRENT_ITEM.get_next_index()
            if f_index == -1:
                QMessageBox.warning(
                    self, _("Error"),
                    _("No more available audio item slots, max per region "
                    "is {}").format(MAX_AUDIO_ITEM_COUNT))
                return
            else:
                CURRENT_ITEM.add_item(f_index, f_item_old)
                f_per_item_fx = CURRENT_ITEM.get_row(self.track_num)
                if f_per_item_fx is not None:
                    CURRENT_ITEM.set_row(f_index, f_per_item_fx)

            f_event_pos = a_event.pos().x()
            # for items that are not quantized
            f_pos = f_event_pos - (f_event_pos - self.quantize(f_event_pos))
            f_scene_pos = self.quantize(a_event.scenePos().x())
            f_musical_pos = self.pos_to_musical_time(f_scene_pos)
            f_sample_shown = f_item.sample_end - f_item.sample_start
            f_sample_rect_pos = f_pos / self.rect().width()
            f_item.sample_start = \
                (f_sample_rect_pos * f_sample_shown) + f_item.sample_start
            f_item.sample_start = pydaw_clip_value(
                f_item.sample_start, 0.0, 999.0, True)
            f_item.start_beat = f_musical_pos
            f_item_old.sample_end = f_item.sample_start
            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
            PROJECT.commit(_("Split audio item"))
            global_open_audio_items(True)
        elif a_event.modifiers() == \
        QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier:
            self.is_amp_dragging = True
        elif a_event.modifiers() == \
        QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier:
            self.is_amp_curving = True
            f_list = [((x.audio_item.start_bar * 4.0) +
                x.audio_item.start_beat)
                for x in AUDIO_SEQ.audio_items if x.isSelected()]
            f_list.sort()
            self.vc_start = f_list[0]
            self.vc_mid = (self.audio_item.start_bar *
                4.0) + self.audio_item.start_beat
            self.vc_end = f_list[-1]
        else:
            QGraphicsRectItem.mousePressEvent(self, a_event)
            self.event_pos_orig = a_event.pos().x()
            for f_item in AUDIO_SEQ.get_selected():
                f_item.setZValue(2400.0)
                f_item_pos = f_item.pos().x()
                f_item.quantize_offset = \
                    f_item_pos - f_item.quantize_all(f_item_pos)
                if a_event.modifiers() == QtCore.Qt.ControlModifier:
                    f_item.is_copying = True
                    f_item.width_orig = f_item.rect().width()
                    f_item.per_item_fx = CURRENT_ITEM.get_row(
                        f_item.track_num)
                    AUDIO_SEQ.draw_item(
                        f_item.track_num, f_item.audio_item,
                        f_item.graph_object)
                if self.is_fading_out:
                    f_item.fade_orig_pos = f_item.fade_out_handle.pos().x()
                elif self.is_fading_in:
                    f_item.fade_orig_pos = f_item.fade_in_handle.pos().x()
                if self.is_start_resizing:
                    f_item.width_orig = 0.0
                else:
                    f_item.width_orig = f_item.rect().width()
        if self.is_amp_curving or self.is_amp_dragging:
            a_event.setAccepted(True)
            self.setSelected(True)
            self.event_pos_orig = a_event.pos().x()
            QGraphicsRectItem.mousePressEvent(self, a_event)
            self.orig_y = a_event.pos().y()
            QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)
            for f_item in AUDIO_SEQ.get_selected():
                f_item.orig_value = f_item.audio_item.vol
                f_item.add_vol_line()

    def hoverEnterEvent(self, a_event):
        f_item_pos = self.pos().x()
        self.quantize_offset = f_item_pos - self.quantize_all(f_item_pos)

    def hoverMoveEvent(self, a_event):
        if a_event.modifiers() == QtCore.Qt.ShiftModifier:
            if not self.split_line_is_shown:
                self.split_line_is_shown = True
                self.split_line.show()
            f_x = a_event.pos().x()
            f_x = self.quantize_all(f_x)
            f_x -= self.quantize_offset
            self.split_line.setPos(f_x, 0.0)
        else:
            if self.split_line_is_shown:
                self.split_line_is_shown = False
                self.split_line.hide()

    def hoverLeaveEvent(self, a_event):
        if self.split_line_is_shown:
            self.split_line_is_shown = False
            self.split_line.hide()

    def y_pos_to_lane_number(self, a_y_pos):
        f_lane_num = int((a_y_pos - AUDIO_RULER_HEIGHT) / AUDIO_ITEM_HEIGHT)
        f_lane_num = pydaw_clip_value(
            f_lane_num, 0, AUDIO_ITEM_MAX_LANE)
        f_y_pos = (f_lane_num * AUDIO_ITEM_HEIGHT) + AUDIO_RULER_HEIGHT
        return f_lane_num, f_y_pos

    def lane_number_to_y_pos(self, a_lane_num):
        a_lane_num = pydaw_util.pydaw_clip_value(
            a_lane_num, 0, project.TRACK_COUNT_ALL)
        return (a_lane_num * AUDIO_ITEM_HEIGHT) + AUDIO_RULER_HEIGHT

    def quantize_all(self, a_x):
        f_x = a_x
        if AUDIO_QUANTIZE:
            f_x = round(f_x / AUDIO_QUANTIZE_PX) * AUDIO_QUANTIZE_PX
        return f_x

    def quantize(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        if AUDIO_QUANTIZE and f_x < AUDIO_QUANTIZE_PX:
            f_x = AUDIO_QUANTIZE_PX
        return f_x

    def quantize_start(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        if f_x >= self.length_handle.pos().x():
            f_x -= AUDIO_QUANTIZE_PX
        return f_x

    def quantize_scene(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        return f_x

    def update_fade_in_line(self):
        f_pos = self.fade_in_handle.pos()
        self.fade_in_handle_line.setLine(
            f_pos.x(), 0.0, 0.0, AUDIO_ITEM_HEIGHT)

    def update_fade_out_line(self):
        f_pos = self.fade_out_handle.pos()
        self.fade_out_handle_line.setLine(
            f_pos.x() + AUDIO_ITEM_HANDLE_SIZE, 0.0,
            self.rect().width(), AUDIO_ITEM_HEIGHT)

    def add_vol_line(self):
        self.vol_line = QGraphicsLineItem(
            0.0, 0.0, self.rect().width(), 0.0, self)
        self.vol_line.setPen(QPen(QtCore.Qt.red, 2.0))
        self.set_vol_line()

    def set_vol_line(self):
        f_pos = (float(48 - (self.audio_item.vol + 24))
            * 0.020833333) * AUDIO_ITEM_HEIGHT # 1.0 / 48.0
        self.vol_line.setPos(0, f_pos)
        self.label.setText("{}dB".format(self.audio_item.vol))

    def mouseMoveEvent(self, a_event):
        if libmk.IS_PLAYING or self.event_pos_orig is None:
            return
        if self.is_amp_curving or self.is_amp_dragging:
            f_pos = a_event.pos()
            f_y = f_pos.y()
            f_diff_y = self.orig_y - f_y
            f_val = (f_diff_y * 0.05)
        f_event_pos = a_event.pos().x()
        f_event_diff = f_event_pos - self.event_pos_orig
        if self.is_resizing:
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_x = f_item.width_orig + f_event_diff + \
                        f_item.quantize_offset
                    f_x = pydaw_clip_value(
                        f_x, AUDIO_ITEM_HANDLE_SIZE,
                        f_item.length_px_minus_start)
                    if f_x < f_item.length_px_minus_start:
                        f_x = f_item.quantize(f_x)
                        f_x -= f_item.quantize_offset
                    f_item.length_handle.setPos(
                        f_x - AUDIO_ITEM_HANDLE_SIZE,
                        AUDIO_ITEM_HEIGHT - AUDIO_ITEM_HANDLE_HEIGHT)
        elif self.is_start_resizing:
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_x = f_item.width_orig + f_event_diff + \
                        f_item.quantize_offset
                    f_x = pydaw_clip_value(
                        f_x, f_item.sample_start_offset_px,
                        f_item.length_handle.pos().x())
                    f_x = pydaw_clip_min(f_x, f_item.min_start)
                    if f_x > f_item.min_start:
                        f_x = f_item.quantize_start(f_x)
                        f_x -= f_item.quantize_offset
                    f_item.start_handle.setPos(
                        f_x, AUDIO_ITEM_HEIGHT - AUDIO_ITEM_HANDLE_HEIGHT)
        elif self.is_fading_in:
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    #f_x = f_event_pos #f_item.width_orig + f_event_diff
                    f_x = f_item.fade_orig_pos + f_event_diff
                    f_x = pydaw_clip_value(
                        f_x, 0.0, f_item.fade_out_handle.pos().x() - 4.0)
                    f_item.fade_in_handle.setPos(f_x, 0.0)
                    f_item.update_fade_in_line()
        elif self.is_fading_out:
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_x = f_item.fade_orig_pos + f_event_diff
                    f_x = pydaw_clip_value(
                        f_x, f_item.fade_in_handle.pos().x() + 4.0,
                        f_item.width_orig - AUDIO_ITEM_HANDLE_SIZE)
                    f_item.fade_out_handle.setPos(f_x, 0.0)
                    f_item.update_fade_out_line()
        elif self.is_stretching:
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected() and \
                f_item.audio_item.time_stretch_mode >= 2:
                    f_x = f_item.width_orig + f_event_diff + \
                        f_item.quantize_offset
                    f_x = pydaw_clip_value(
                        f_x, f_item.stretch_width_default * 0.1,
                        f_item.stretch_width_default * 200.0)
                    f_x = pydaw_clip_max(f_x, f_item.max_stretch)
                    f_x = f_item.quantize(f_x)
                    f_x -= f_item.quantize_offset
                    f_item.stretch_handle.setPos(
                        f_x - AUDIO_ITEM_HANDLE_SIZE,
                        (AUDIO_ITEM_HEIGHT * 0.5) -
                        (AUDIO_ITEM_HANDLE_HEIGHT * 0.5))
        elif self.is_amp_dragging:
            for f_item in AUDIO_SEQ.get_selected():
                f_new_vel = pydaw_util.pydaw_clip_value(
                    f_val + f_item.orig_value, -24.0, 24.0)
                f_new_vel = round(f_new_vel, 1)
                f_item.audio_item.vol = f_new_vel
                f_item.set_vol_line()
        elif self.is_amp_curving:
            AUDIO_SEQ.setUpdatesEnabled(False)
            for f_item in AUDIO_SEQ.get_selected():
                f_start = ((f_item.audio_item.start_bar * 4.0) +
                    f_item.audio_item.start_beat)
                if f_start == self.vc_mid:
                    f_new_vel = f_val + f_item.orig_value
                else:
                    if f_start > self.vc_mid:
                        f_frac =  (f_start -
                            self.vc_mid) / (self.vc_end - self.vc_mid)
                        f_new_vel = pydaw_util.linear_interpolate(
                            f_val, 0.3 * f_val, f_frac)
                    else:
                        f_frac = (f_start -
                            self.vc_start) / (self.vc_mid - self.vc_start)
                        f_new_vel = pydaw_util.linear_interpolate(
                            0.3 * f_val, f_val, f_frac)
                    f_new_vel += f_item.orig_value
                f_new_vel = pydaw_util.pydaw_clip_value(f_new_vel, -24.0, 24.0)
                f_new_vel = round(f_new_vel, 1)
                f_item.audio_item.vol = f_new_vel
                f_item.set_vol_line()
            AUDIO_SEQ.setUpdatesEnabled(True)
            AUDIO_SEQ.update()
        else:
            QGraphicsRectItem.mouseMoveEvent(self, a_event)
            if AUDIO_QUANTIZE:
                f_max_x = (CURRENT_ITEM_LEN *
                    AUDIO_PX_PER_BEAT) - AUDIO_QUANTIZE_PX
            else:
                f_max_x = (CURRENT_ITEM_LEN *
                    AUDIO_PX_PER_BEAT) - AUDIO_ITEM_HANDLE_SIZE
            f_new_lane, f_ignored = self.y_pos_to_lane_number(
                a_event.scenePos().y())
            f_lane_offset = f_new_lane - self.audio_item.lane_num
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_pos_x = f_item.pos().x()
                    f_pos_x = pydaw_clip_value(f_pos_x, 0.0, f_max_x)
                    f_pos_x = f_item.quantize_scene(f_pos_x)
                    f_pos_y = self.lane_number_to_y_pos(
                        f_lane_offset + f_item.audio_item.lane_num)
                    f_item.setPos(f_pos_x, f_pos_y)
                    if not f_item.is_moving:
                        f_item.setGraphicsEffect(
                            QGraphicsOpacityEffect())
                        f_item.is_moving = True

    def mouseReleaseEvent(self, a_event):
        if libmk.IS_PLAYING or self.event_pos_orig is None:
            return
        QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        QApplication.restoreOverrideCursor()
        f_audio_items = CURRENT_ITEM
        #Set to True when testing, set to False for better UI performance...
        f_reset_selection = True
        f_did_change = False
        f_was_stretching = False
        f_stretched_items = []
        f_event_pos = a_event.pos().x()
        f_event_diff = f_event_pos - self.event_pos_orig

        for f_audio_item in AUDIO_SEQ.get_selected():
            f_item = f_audio_item.audio_item
            f_pos_x = f_audio_item.pos().x()
            if f_audio_item.is_resizing:
                f_x = f_audio_item.width_orig + f_event_diff + \
                    f_audio_item.quantize_offset
                f_x = pydaw_clip_value(
                    f_x, AUDIO_ITEM_HANDLE_SIZE,
                    f_audio_item.length_px_minus_start)
                f_x = f_audio_item.quantize(f_x)
                f_x -= f_audio_item.quantize_offset
                f_audio_item.setRect(0.0, 0.0, f_x, AUDIO_ITEM_HEIGHT)
                f_item.sample_end = ((f_audio_item.rect().width() +
                f_audio_item.length_px_start) /
                f_audio_item.length_seconds_orig_px) * 1000.0
                f_item.sample_end = pydaw_util.pydaw_clip_value(
                    f_item.sample_end, 1.0, 1000.0, True)
            elif f_audio_item.is_start_resizing:
                f_x = f_audio_item.start_handle.scenePos().x()
                f_x = pydaw_clip_min(f_x, 0.0)
                f_x = self.quantize_all(f_x)
                if f_x < f_audio_item.sample_start_offset_px:
                    f_x = f_audio_item.sample_start_offset_px
                f_start_result = self.pos_to_musical_time(f_x)
                f_item.start_beat = f_start_result
                f_item.sample_start = ((f_x -
                    f_audio_item.start_handle_scene_min) /
                    (f_audio_item.start_handle_scene_max -
                    f_audio_item.start_handle_scene_min)) * 1000.0
                f_item.sample_start = pydaw_clip_value(
                    f_item.sample_start, 0.0, 999.0, True)
            elif f_audio_item.is_fading_in:
                f_pos = f_audio_item.fade_in_handle.pos().x()
                f_val = (f_pos / f_audio_item.rect().width()) * 1000.0
                f_item.fade_in = pydaw_clip_value(f_val, 0.0, 997.0, True)
            elif f_audio_item.is_fading_out:
                f_pos = f_audio_item.fade_out_handle.pos().x()
                f_val = ((f_pos + AUDIO_ITEM_HANDLE_SIZE) /
                    (f_audio_item.rect().width())) * 1000.0
                f_item.fade_out = pydaw_clip_value(f_val, 1.0, 998.0, True)
            elif f_audio_item.is_stretching and f_item.time_stretch_mode >= 2:
                f_reset_selection = True
                f_x = f_audio_item.width_orig + f_event_diff + \
                    f_audio_item.quantize_offset
                f_x = pydaw_clip_value(
                    f_x, f_audio_item.stretch_width_default * 0.1,
                    f_audio_item.stretch_width_default * 200.0)
                f_x = pydaw_clip_max(f_x, f_audio_item.max_stretch)
                f_x = f_audio_item.quantize(f_x)
                f_x -= f_audio_item.quantize_offset
                f_item.timestretch_amt = \
                    f_x / f_audio_item.stretch_width_default
                f_item.timestretch_amt_end = f_item.timestretch_amt
                if f_item.time_stretch_mode >= 3 and \
                f_audio_item.orig_string != str(f_item):
                    f_was_stretching = True
                    f_ts_result = libmk.PROJECT.timestretch_audio_item(f_item)
                    if f_ts_result is not None:
                        f_stretched_items.append(f_ts_result)
                f_audio_item.setRect(0.0, 0.0, f_x, AUDIO_ITEM_HEIGHT)
            elif self.is_amp_curving or self.is_amp_dragging:
                f_did_change = True
            else:
                f_pos_y = f_audio_item.pos().y()
                if f_audio_item.is_copying:
                    f_reset_selection = True
                    f_item_old = f_item.clone()
                    f_index = f_audio_items.get_next_index()
                    if f_index == -1:
                        QMessageBox.warning(self, _("Error"),
                        _("No more available audio item slots, max per "
                        "region is {}").format(MAX_AUDIO_ITEM_COUNT))
                        break
                    else:
                        f_audio_items.add_item(f_index, f_item_old)
                        if f_audio_item.per_item_fx is not None:
                            CURRENT_ITEM.set_row(
                                f_index, f_audio_item.per_item_fx)
                else:
                    f_audio_item.set_brush(f_item.lane_num)
                f_pos_x = self.quantize_all(f_pos_x)
                f_item.lane_num, f_pos_y = self.y_pos_to_lane_number(f_pos_y)
                f_audio_item.setPos(f_pos_x, f_pos_y)
                f_start_result = f_audio_item.pos_to_musical_time(f_pos_x)
                f_item.set_pos(0, f_start_result)
            f_audio_item.clip_at_region_end()
            f_item_str = str(f_item)
            if f_item_str != f_audio_item.orig_string:
                f_audio_item.orig_string = f_item_str
                f_did_change = True
                if not f_reset_selection:
                    f_audio_item.draw()
            f_audio_item.is_moving = False
            f_audio_item.is_resizing = False
            f_audio_item.is_start_resizing = False
            f_audio_item.is_copying = False
            f_audio_item.is_fading_in = False
            f_audio_item.is_fading_out = False
            f_audio_item.is_stretching = False
            f_audio_item.setGraphicsEffect(None)
            f_audio_item.setFlag(QGraphicsItem.ItemClipsChildrenToShape)
        if f_did_change:
            f_audio_items.deduplicate_items()
            if f_was_stretching:
                libmk.PROJECT.save_stretch_dicts()
                for f_stretch_item in f_stretched_items:
                    f_stretch_item[2].wait()
                    libmk.PROJECT.get_wav_uid_by_name(
                        f_stretch_item[0], a_uid=f_stretch_item[1])
#                for f_audio_item in AUDIO_SEQ.get_selected():
#                    f_new_graph = libmk.PROJECT.get_sample_graph_by_uid(
#                        f_audio_item.audio_item.uid)
#                    f_audio_item.audio_item.clip_at_region_end(
#                        pydaw_get_current_region_length(),
#                        TRANSPORT.tempo_spinbox.value(),
#                        f_new_graph.length_in_seconds)
            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
            PROJECT.commit(_("Update audio items"))
        global_open_audio_items(f_reset_selection)

AUDIO_ITEMS_HEADER_GRADIENT = QLinearGradient(
    0.0, 0.0, 0.0, AUDIO_RULER_HEIGHT)
AUDIO_ITEMS_HEADER_GRADIENT.setColorAt(0.0, QColor.fromRgb(61, 61, 61))
AUDIO_ITEMS_HEADER_GRADIENT.setColorAt(0.5, QColor.fromRgb(50,50, 50))
AUDIO_ITEMS_HEADER_GRADIENT.setColorAt(0.6, QColor.fromRgb(43, 43, 43))
AUDIO_ITEMS_HEADER_GRADIENT.setColorAt(1.0, QColor.fromRgb(65, 65, 65))


class AudioItemSeq(AbstractItemEditor):
    """ This is the QGraphicsView and QGraphicsScene for editing audio
        items within a SequencerItem on the "Items" tab.
    """
    def __init__(self):
        AbstractItemEditor.__init__(self)
        self.reset_line_lists()
        self.h_zoom = 1.0
        self.v_zoom = 1.0
        self.scene = QGraphicsScene(self)
        self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.scene.dropEvent = self.sceneDropEvent
        self.scene.dragEnterEvent = self.sceneDragEnterEvent
        self.scene.dragMoveEvent = self.sceneDragMoveEvent
        self.scene.contextMenuEvent = self.sceneContextMenuEvent
        self.scene.setBackgroundBrush(QColor(90, 90, 90))
        self.scene.selectionChanged.connect(self.scene_selection_changed)
        self.setAcceptDrops(True)
        self.setScene(self.scene)
        self.audio_items = []
        self.track = 0
        self.gradient_index = 0
        self.playback_px = 0.0
        self.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.is_playing = False
        self.reselect_on_stop = []
        #Somewhat slow on my AMD 5450 using the FOSS driver
        #self.setRenderHint(QPainter.Antialiasing)
        self.context_menu_enabled = True

    def reset_line_lists(self):
        self.text_list = []
        self.beat_line_list = []

    def prepare_to_quit(self):
        self.scene.clearSelection()
        self.scene.clear()

    def keyPressEvent(self, a_event):
        #Done this way to prevent the region editor from grabbing the key
        if a_event.key() == QtCore.Qt.Key_Delete:
            self.delete_selected()
        else:
            QGraphicsView.keyPressEvent(self, a_event)
        QApplication.restoreOverrideCursor()

    def scrollContentsBy(self, x, y):
        QGraphicsView.scrollContentsBy(self, x, y)
        self.set_header_y_pos()

    def set_header_y_pos(self):
        f_point = self.get_scene_pos()
        self.header.setPos(0.0, f_point.y())
        self.verticalScrollBar().setMinimum(0)

    def get_scene_pos(self):
        return QtCore.QPointF(
            self.horizontalScrollBar().value(),
            self.verticalScrollBar().value())

    def get_selected(self):
        return [x for x in self.audio_items if x.isSelected()]

    def delete_selected(self):
        if self.check_running():
            return
        f_items = CURRENT_ITEM
        f_paif = CURRENT_ITEM
        for f_item in self.get_selected():
            f_items.remove_item(f_item.track_num)
            f_paif.clear_row_if_exists(f_item.track_num)
        PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
        PROJECT.commit(_("Delete audio item(s)"))
        global_open_audio_items(True)

    def crossfade_selected(self):
        f_list = self.get_selected()
        if len(f_list) < 2:
            QMessageBox.warning(
                MAIN_WINDOW, _("Error"),
                _("You must have at least 2 items selected to crossfade"))
            return

        f_tempo = CURRENT_REGION.get_tempo_at_pos(CURRENT_ITEM_REF.start_beat)
        f_changed = False

        for f_item in f_list:
            f_start_sec = pydaw_util.musical_time_to_seconds(
                f_tempo, f_item.audio_item.start_bar,
                f_item.audio_item.start_beat)
            f_time_frac = f_item.audio_item.sample_end - \
                f_item.audio_item.sample_start
            f_time_frac *= 0.001
            f_time = f_item.graph_object.length_in_seconds * f_time_frac
            f_end_sec = f_start_sec + f_time
            f_list2 = [x for x in f_list if x.audio_item != f_item.audio_item]

            for f_item2 in f_list2:
                f_start_sec2 = pydaw_util.musical_time_to_seconds(
                    f_tempo, f_item2.audio_item.start_bar,
                    f_item2.audio_item.start_beat)
                f_time_frac2 = f_item2.audio_item.sample_end - \
                    f_item2.audio_item.sample_start
                f_time_frac2 *= 0.001
                f_time2 = f_item2.graph_object.length_in_seconds * f_time_frac2
                f_end_sec2 = f_start_sec2 + f_time2

                if f_start_sec > f_start_sec2 and \
                f_end_sec > f_end_sec2 and \
                f_end_sec2 > f_start_sec:  # item1 is after item2
                    f_changed = True
                    f_diff_sec = f_end_sec2 - f_start_sec
                    f_val = (f_diff_sec / f_time) * 1000.0
                    f_item.audio_item.set_fade_in(f_val)
                elif f_start_sec < f_start_sec2 and \
                f_end_sec < f_end_sec2 and \
                f_end_sec > f_start_sec2: # item1 is before item2
                    f_changed = True
                    f_diff_sec = f_start_sec2 - f_start_sec
                    f_val = (f_diff_sec / f_time) * 1000.0
                    f_item.audio_item.set_fade_out(f_val)

        if f_changed:
            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
            PROJECT.commit(_("Crossfade audio items"))
            global_open_audio_items(True)


    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip(libpydaw.strings.AudioItemSeq)
        else:
            self.setToolTip("")
        for f_item in self.audio_items:
            f_item.set_tooltips(a_on)

    def resizeEvent(self, a_event):
        QGraphicsView.resizeEvent(self, a_event)
        pydaw_set_audio_seq_zoom(self.h_zoom, self.v_zoom)
        global_open_audio_items(a_reload=False)

    def sceneContextMenuEvent(self, a_event):
        if self.check_running():
            return
        if not self.context_menu_enabled:
            self.context_menu_enabled = True
            return
        QGraphicsScene.contextMenuEvent(self.scene, a_event)
        self.context_menu_pos = a_event.scenePos()
        f_menu = QMenu(MAIN_WINDOW)
        f_paste_action = QAction(
            _("Paste file path from clipboard"), self)
        f_paste_action.triggered.connect(self.on_scene_paste_paths)
        f_menu.addAction(f_paste_action)
        f_menu.exec_(a_event.screenPos())

    def on_scene_paste_paths(self):
        f_path = global_get_audio_file_from_clipboard()
        if f_path:
            self.add_items(
                self.context_menu_pos.x(), self.context_menu_pos.y(),
                [f_path])

    def scene_selection_changed(self):
        f_selected_items = []
        global CURRENT_AUDIO_ITEM_INDEX
        for f_item in self.audio_items:
            f_item.set_brush()
            if f_item.isSelected():
                f_selected_items.append(f_item)
        if len(f_selected_items) == 1:
            CURRENT_AUDIO_ITEM_INDEX = f_selected_items[0].track_num
            AUDIO_SEQ_WIDGET.modulex.widget.setEnabled(True)
            AUDIO_SEQ_WIDGET.modulex.set_from_list(
                CURRENT_ITEM.get_row(CURRENT_AUDIO_ITEM_INDEX))
        elif len(f_selected_items) == 0:
            CURRENT_AUDIO_ITEM_INDEX = None
            AUDIO_SEQ_WIDGET.modulex.widget.setDisabled(True)
        else:
            AUDIO_SEQ_WIDGET.modulex.widget.setDisabled(True)

    def sceneDragEnterEvent(self, a_event):
        a_event.setAccepted(True)

    def sceneDragMoveEvent(self, a_event):
        a_event.setDropAction(QtCore.Qt.CopyAction)

    def check_running(self):
        if not CURRENT_ITEM or libmk.IS_PLAYING:
            return True
        return False

    def sceneDropEvent(self, a_event):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return
        if AUDIO_ITEMS_TO_DROP:
            f_x = a_event.scenePos().x()
            f_y = a_event.scenePos().y()
            self.add_items(f_x, f_y, AUDIO_ITEMS_TO_DROP)

    def add_items(self, f_x, f_y, a_item_list):
        if self.check_running():
            return

        f_beat_frac = f_x / AUDIO_PX_PER_BEAT
        f_beat_frac = pydaw_clip_min(f_beat_frac, 0.0)
        print("f_beat_frac: {}".format(f_beat_frac))
        if AUDIO_QUANTIZE:
            f_beat_frac = int(
                f_beat_frac * AUDIO_QUANTIZE_AMT) / AUDIO_QUANTIZE_AMT

        f_lane_num = int((f_y - AUDIO_RULER_HEIGHT) / AUDIO_ITEM_HEIGHT)
        f_lane_num = pydaw_clip_value(f_lane_num, 0, AUDIO_ITEM_MAX_LANE)

        f_items = CURRENT_ITEM

        for f_file_name in a_item_list:
            f_file_name_str = str(f_file_name)
            if not f_file_name_str is None and not f_file_name_str == "":
                f_index = f_items.get_next_index()
                if f_index == -1:
                    QMessageBox.warning(self, _("Error"),
                    _("No more available audio item slots, "
                    "max per region is {}").format(MAX_AUDIO_ITEM_COUNT))
                    break
                else:
                    f_uid = libmk.PROJECT.get_wav_uid_by_name(f_file_name_str)
                    f_item = pydaw_audio_item(
                        f_uid, a_start_bar=0, a_start_beat=f_beat_frac,
                        a_lane_num=f_lane_num)
                    f_items.add_item(f_index, f_item)
                    f_graph = libmk.PROJECT.get_sample_graph_by_uid(f_uid)
                    f_audio_item = AUDIO_SEQ.draw_item(
                        f_index, f_item, f_graph)
                    f_audio_item.clip_at_region_end()
        PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
        PROJECT.commit(
            _("Added audio items to item {}").format(CURRENT_ITEM.uid))
        global_open_audio_items()
        self.last_open_dir = os.path.dirname(f_file_name_str)

    def reset_selection(self):
        for f_item in self.audio_items:
            if str(f_item.audio_item) in self.reselect_on_stop:
                f_item.setSelected(True)

    def set_zoom(self, a_scale):
        self.h_zoom = a_scale
        self.update_zoom()

    def set_v_zoom(self, a_scale):
        self.v_zoom = a_scale
        self.update_zoom()

    def update_zoom(self):
        pydaw_set_audio_seq_zoom(self.h_zoom, self.v_zoom)

    def check_line_count(self):
        """ Check that there are not too many vertical
            lines on the screen
        """
        return

        f_num_count = len(self.text_list)
        if f_num_count == 0:
            return
        f_num_visible_count = int(f_num_count /
            pydaw_clip_min(self.h_zoom, 1))

        if f_num_visible_count > 24:
            for f_line in self.beat_line_list:
                f_line.setVisible(False)
            f_factor = f_num_visible_count // 24
            if f_factor == 1:
                for f_num in self.text_list:
                    f_num.setVisible(True)
            else:
                f_factor = int(round(f_factor / 2.0) * 2)
                for f_num in self.text_list:
                    f_num.setVisible(False)
                for f_num in self.text_list[::f_factor]:
                    f_num.setVisible(True)
        else:
            for f_line in self.beat_line_list:
                f_line.setVisible(True)
            for f_num in self.text_list:
                f_num.setVisible(True)


    def draw_header(self):
        f_region_length = CURRENT_ITEM_LEN
        f_size = AUDIO_PX_PER_BEAT * f_region_length
        self.total_height = (AUDIO_ITEM_LANE_COUNT *
            (AUDIO_ITEM_HEIGHT)) + AUDIO_RULER_HEIGHT
        AbstractItemEditor.draw_header(self, f_size, AUDIO_RULER_HEIGHT)
        self.header.setZValue(1500.0)
        self.header.setBrush(AUDIO_ITEMS_HEADER_GRADIENT)
        self.scene.addItem(self.header)
        if ITEM_REF_POS:
            f_start, f_end = ITEM_REF_POS
            f_start_x = f_start * AUDIO_PX_PER_BEAT
            f_end_x = f_end * AUDIO_PX_PER_BEAT
            f_start_line = QGraphicsLineItem(
                f_start_x, 0.0, f_start_x, AUDIO_RULER_HEIGHT, self.header)
            f_start_line.setPen(START_PEN)
            f_end_line = QGraphicsLineItem(
                f_end_x, 0.0, f_end_x, AUDIO_RULER_HEIGHT, self.header)
            f_end_line.setPen(END_PEN)
        f_v_pen = QPen(QtCore.Qt.black)
        #f_beat_pen = QPen(QColor(210, 210, 210))
        f_16th_pen = QPen(QColor(120, 120, 120))
        f_reg_pen = QPen(QtCore.Qt.white)
        i3 = 0.0
        for i in range(int(f_region_length)):
            f_number = QGraphicsSimpleTextItem(
                "{}".format(i + 1), self.header)
            f_number.setFlag(QGraphicsItem.ItemIgnoresTransformations)
            f_number.setBrush(QtCore.Qt.white)
            f_number.setZValue(1000.0)
            self.text_list.append(f_number)
            self.scene.addLine(i3, 0.0, i3, self.total_height, f_v_pen)
            f_number.setPos(i3 + 3.0, 2)
            if AUDIO_LINES_ENABLED:
                for f_i4 in range(1, AUDIO_SNAP_RANGE):
                    f_sub_x = i3 + (AUDIO_QUANTIZE_PX * f_i4)
                    f_line = self.scene.addLine(
                        f_sub_x, AUDIO_RULER_HEIGHT,
                        f_sub_x, self.total_height, f_16th_pen)
                    self.beat_line_list.append(f_line)
#            for f_beat_i in range(1, 4):
#                f_beat_x = i3 + (AUDIO_PX_PER_BEAT * f_beat_i)
#                f_line = self.scene.addLine(
#                    f_beat_x, 0.0, f_beat_x, self.total_height, f_beat_pen)
#                self.beat_line_list.append(f_line)
#                if AUDIO_LINES_ENABLED:
#                    for f_i4 in range(1, AUDIO_SNAP_RANGE):
#                        f_sub_x = f_beat_x + (AUDIO_QUANTIZE_PX * f_i4)
#                        f_line = self.scene.addLine(
#                            f_sub_x, AUDIO_RULER_HEIGHT,
#                            f_sub_x, self.total_height, f_16th_pen)
#                        self.beat_line_list.append(f_line)
            i3 += AUDIO_PX_PER_BEAT
        self.scene.addLine(
            i3, AUDIO_RULER_HEIGHT, i3, self.total_height, f_reg_pen)
        for i2 in range(AUDIO_ITEM_LANE_COUNT):
            f_y = ((AUDIO_ITEM_HEIGHT) * (i2 + 1)) + AUDIO_RULER_HEIGHT
            self.scene.addLine(0, f_y, f_size, f_y)
        self.check_line_count()
        self.set_header_y_pos()

    def clear_drawn_items(self):
        if self.is_playing:
            f_was_playing = True
            self.is_playing = False
        else:
            f_was_playing = False
        self.reset_line_lists()
        self.audio_items = []
        self.scene.clear()
        self.draw_header()
        if f_was_playing:
            self.is_playing = True

    def draw_item(self, a_audio_item_index, a_audio_item, a_graph):
        """a_start in seconds, a_length in seconds"""
        f_audio_item = AudioSeqItem(
            a_audio_item_index, a_audio_item, a_graph)
        self.audio_items.append(f_audio_item)
        self.scene.addItem(f_audio_item)
        return f_audio_item


class time_pitch_dialog_widget:
    def __init__(self, a_audio_item):
        self.widget = QDialog()
        self.widget.setWindowTitle(_("Time/Pitch..."))
        self.widget.setMaximumWidth(480)
        self.main_vlayout = QVBoxLayout(self.widget)

        self.layout = QGridLayout()
        self.main_vlayout.addLayout(self.layout)

        self.vlayout2 = QVBoxLayout()
        self.layout.addLayout(self.vlayout2, 1, 1)
        self.start_hlayout = QHBoxLayout()
        self.vlayout2.addLayout(self.start_hlayout)

        self.timestretch_hlayout = QHBoxLayout()
        self.time_pitch_gridlayout = QGridLayout()
        self.vlayout2.addLayout(self.timestretch_hlayout)
        self.vlayout2.addLayout(self.time_pitch_gridlayout)
        self.timestretch_hlayout.addWidget(QLabel(_("Mode:")))
        self.timestretch_mode = QComboBox()

        self.timestretch_mode.setMinimumWidth(240)
        self.timestretch_hlayout.addWidget(self.timestretch_mode)
        self.timestretch_mode.addItems(TIMESTRETCH_MODES)
        self.timestretch_mode.setCurrentIndex(a_audio_item.time_stretch_mode)
        self.timestretch_mode.currentIndexChanged.connect(
            self.timestretch_mode_changed)
        self.time_pitch_gridlayout.addWidget(QLabel(_("Pitch:")), 0, 0)
        self.pitch_shift = QDoubleSpinBox()
        self.pitch_shift.setRange(-36, 36)
        self.pitch_shift.setValue(a_audio_item.pitch_shift)
        self.pitch_shift.setDecimals(6)
        self.time_pitch_gridlayout.addWidget(self.pitch_shift, 0, 1)

        self.pitch_shift_end_checkbox = QCheckBox(_("End:"))
        self.pitch_shift_end_checkbox.setChecked(
            a_audio_item.pitch_shift != a_audio_item.pitch_shift_end)
        self.pitch_shift_end_checkbox.toggled.connect(
            self.pitch_end_mode_changed)
        self.time_pitch_gridlayout.addWidget(
            self.pitch_shift_end_checkbox, 0, 2)
        self.pitch_shift_end = QDoubleSpinBox()
        self.pitch_shift_end.setRange(-36, 36)
        self.pitch_shift_end.setValue(a_audio_item.pitch_shift_end)
        self.pitch_shift_end.setDecimals(6)
        self.time_pitch_gridlayout.addWidget(self.pitch_shift_end, 0, 3)

        self.time_pitch_gridlayout.addWidget(QLabel(_("Time:")), 1, 0)
        self.timestretch_amt = QDoubleSpinBox()
        self.timestretch_amt.setRange(0.1, 200.0)
        self.timestretch_amt.setDecimals(6)
        self.timestretch_amt.setSingleStep(0.1)
        self.timestretch_amt.setValue(a_audio_item.timestretch_amt)
        self.time_pitch_gridlayout.addWidget(self.timestretch_amt, 1, 1)

        self.crispness_layout = QHBoxLayout()
        self.vlayout2.addLayout(self.crispness_layout)
        self.crispness_layout.addWidget(QLabel(_("Crispness")))
        self.crispness_combobox = QComboBox()
        self.crispness_combobox.addItems(CRISPNESS_SETTINGS)
        self.crispness_combobox.setCurrentIndex(a_audio_item.crispness)
        self.crispness_layout.addWidget(self.crispness_combobox)

        self.timestretch_amt_end_checkbox = QCheckBox(_("End:"))
        self.timestretch_amt_end_checkbox.toggled.connect(
            self.timestretch_end_mode_changed)
        self.time_pitch_gridlayout.addWidget(
            self.timestretch_amt_end_checkbox, 1, 2)
        self.timestretch_amt_end = QDoubleSpinBox()
        self.timestretch_amt_end.setRange(0.2, 4.0)
        self.timestretch_amt_end.setDecimals(6)
        self.timestretch_amt_end.setSingleStep(0.1)
        self.timestretch_amt_end.setValue(a_audio_item.timestretch_amt_end)
        self.time_pitch_gridlayout.addWidget(self.timestretch_amt_end, 1, 3)

        self.timestretch_mode_changed(0)

        self.timestretch_mode.currentIndexChanged.connect(
            self.timestretch_changed)
        self.pitch_shift.valueChanged.connect(self.timestretch_changed)
        self.pitch_shift_end.valueChanged.connect(self.timestretch_changed)
        self.timestretch_amt.valueChanged.connect(self.timestretch_changed)
        self.timestretch_amt_end.valueChanged.connect(self.timestretch_changed)
        self.crispness_combobox.currentIndexChanged.connect(
            self.timestretch_changed)

        self.ok_layout = QHBoxLayout()
        self.ok = QPushButton(_("OK"))
        self.ok.pressed.connect(self.ok_handler)
        self.ok_layout.addWidget(self.ok)
        self.cancel = QPushButton(_("Cancel"))
        self.cancel.pressed.connect(self.widget.close)
        self.ok_layout.addWidget(self.cancel)
        self.vlayout2.addLayout(self.ok_layout)

        self.last_open_dir = global_home

    def timestretch_end_mode_changed(self, a_val=None):
        if not self.timestretch_amt_end_checkbox.isChecked():
            self.timestretch_amt_end.setValue(self.timestretch_amt.value())

    def pitch_end_mode_changed(self, a_val=None):
        if not self.pitch_shift_end_checkbox.isChecked():
            self.pitch_shift_end.setValue(self.pitch_shift.value())

    def end_mode_changed(self, a_val=None):
        self.end_mode_checkbox.setChecked(True)

    def timestretch_changed(self, a_val=None):
        if not self.pitch_shift_end_checkbox.isChecked():
            self.pitch_shift_end.setValue(self.pitch_shift.value())
        if not self.timestretch_amt_end_checkbox.isChecked():
            self.timestretch_amt_end.setValue(self.timestretch_amt.value())

    def timestretch_mode_changed(self, a_val=None):
        a_val = pydaw_util.TIMESTRETCH_INDEXES[
            str(self.timestretch_mode.currentText())]
        if a_val == 0:
            self.pitch_shift.setEnabled(False)
            self.timestretch_amt.setEnabled(False)
            self.pitch_shift.setValue(0.0)
            self.pitch_shift_end.setValue(0.0)
            self.timestretch_amt.setValue(1.0)
            self.timestretch_amt_end.setValue(1.0)
            self.timestretch_amt_end_checkbox.setEnabled(False)
            self.timestretch_amt_end_checkbox.setChecked(False)
            self.pitch_shift_end_checkbox.setEnabled(False)
            self.pitch_shift_end_checkbox.setChecked(False)
            self.crispness_combobox.setCurrentIndex(5)
            self.crispness_combobox.setEnabled(False)
        elif a_val == 1:
            self.pitch_shift.setEnabled(True)
            self.timestretch_amt.setEnabled(False)
            self.timestretch_amt.setValue(1.0)
            self.timestretch_amt_end.setValue(1.0)
            self.timestretch_amt_end.setEnabled(False)
            self.timestretch_amt_end_checkbox.setEnabled(False)
            self.timestretch_amt_end_checkbox.setChecked(False)
            self.pitch_shift_end_checkbox.setEnabled(True)
            self.pitch_shift_end.setEnabled(True)
            self.crispness_combobox.setCurrentIndex(5)
            self.crispness_combobox.setEnabled(False)
        elif a_val == 2:
            self.pitch_shift.setEnabled(False)
            self.timestretch_amt.setEnabled(True)
            self.pitch_shift.setValue(0.0)
            self.pitch_shift_end.setValue(0.0)
            self.pitch_shift_end.setEnabled(False)
            self.timestretch_amt_end.setEnabled(True)
            self.timestretch_amt_end_checkbox.setEnabled(True)
            self.pitch_shift_end_checkbox.setEnabled(False)
            self.pitch_shift_end_checkbox.setChecked(False)
            self.crispness_combobox.setCurrentIndex(5)
            self.crispness_combobox.setEnabled(False)
        elif a_val == 3 or a_val == 4:
            self.pitch_shift.setEnabled(True)
            self.pitch_shift_end.setEnabled(False)
            self.timestretch_amt.setEnabled(True)
            self.timestretch_amt_end_checkbox.setEnabled(False)
            self.timestretch_amt_end_checkbox.setChecked(False)
            self.pitch_shift_end_checkbox.setEnabled(False)
            self.pitch_shift_end_checkbox.setChecked(False)
            self.crispness_combobox.setEnabled(True)
        elif a_val == 5:
            self.pitch_shift.setEnabled(True)
            self.pitch_shift_end.setEnabled(True)
            self.timestretch_amt.setEnabled(True)
            self.timestretch_amt_end.setEnabled(True)
            self.timestretch_amt_end_checkbox.setEnabled(True)
            self.pitch_shift_end_checkbox.setEnabled(True)
            self.crispness_combobox.setCurrentIndex(5)
            self.crispness_combobox.setEnabled(False)
        elif a_val == 6:
            self.pitch_shift.setEnabled(True)
            self.timestretch_amt.setEnabled(True)
            self.timestretch_amt_end.setEnabled(False)
            self.pitch_shift_end.setEnabled(False)
            self.timestretch_amt_end_checkbox.setEnabled(False)
            self.timestretch_amt_end_checkbox.setChecked(False)
            self.pitch_shift_end_checkbox.setEnabled(False)
            self.pitch_shift_end_checkbox.setChecked(False)
            self.crispness_combobox.setCurrentIndex(5)
            self.crispness_combobox.setEnabled(False)


    def ok_handler(self):
        if libmk.IS_PLAYING:
            QMessageBox.warning(
                self.widget, _("Error"),
                _("Cannot edit audio items during playback"))
            return

        self.end_mode = 0

        f_selected_count = 0

        f_was_stretching = False
        f_stretched_items = []

        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_new_ts_mode = self.timestretch_mode.currentIndex()
                f_new_ts = round(self.timestretch_amt.value(), 6)
                f_new_ps = round(self.pitch_shift.value(), 6)
                if self.timestretch_amt_end_checkbox.isChecked():
                    f_new_ts_end = round(
                        self.timestretch_amt_end.value(), 6)
                else:
                    f_new_ts_end = f_new_ts
                if self.pitch_shift_end_checkbox.isChecked():
                    f_new_ps_end = round(self.pitch_shift_end.value(), 6)
                else:
                    f_new_ps_end = f_new_ps
                f_item.audio_item.crispness = \
                    self.crispness_combobox.currentIndex()

                if ((f_item.audio_item.time_stretch_mode >= 3) or
                (f_item.audio_item.time_stretch_mode == 1 and \
                (f_item.audio_item.pitch_shift_end !=
                    f_item.audio_item.pitch_shift)) or \
                (f_item.audio_item.time_stretch_mode == 2 and \
                (f_item.audio_item.timestretch_amt_end !=
                    f_item.audio_item.timestretch_amt))) and \
                ((f_new_ts_mode == 0) or \
                (f_new_ts_mode == 1 and f_new_ps == f_new_ps_end) or \
                (f_new_ts_mode == 2 and f_new_ts == f_new_ts_end)):
                    f_item.audio_item.uid = \
                        libmk.PROJECT.timestretch_get_orig_file_uid(
                            f_item.audio_item.uid)

                f_item.audio_item.time_stretch_mode = f_new_ts_mode
                f_item.audio_item.pitch_shift = f_new_ps
                f_item.audio_item.timestretch_amt = f_new_ts
                f_item.audio_item.pitch_shift_end = f_new_ps_end
                f_item.audio_item.timestretch_amt_end = f_new_ts_end
                f_item.draw()
                f_item.clip_at_region_end()
                if (f_new_ts_mode >= 3) or \
                (f_new_ts_mode == 1 and f_new_ps != f_new_ps_end) or \
                (f_new_ts_mode == 2 and f_new_ts != f_new_ts_end) and \
                (f_item.orig_string != str(f_item.audio_item)):
                    f_was_stretching = True
                    f_ts_result = libmk.PROJECT.timestretch_audio_item(
                        f_item.audio_item)
                    if f_ts_result is not None:
                        f_stretched_items.append(
                            (f_ts_result, f_item.audio_item))
                f_item.draw()
                f_selected_count += 1
        if f_selected_count == 0:
            QMessageBox.warning(
                self.widget, _("Error"), _("No items selected"))
        else:
            if f_was_stretching:
#                f_current_region_length = pydaw_get_current_region_length()
#                f_global_tempo = float(TRANSPORT.tempo_spinbox.value())
                libmk.PROJECT.save_stretch_dicts()
                for f_stretch_item, f_audio_item in f_stretched_items:
                    f_stretch_item[2].wait()
#                    f_new_uid = libmk.PROJECT.get_wav_uid_by_name(
#                        f_stretch_item[0], a_uid=f_stretch_item[1])
#                    f_graph = libmk.PROJECT.get_sample_graph_by_uid(f_new_uid)
#                    f_audio_item.clip_at_region_end(
#                        f_current_region_length, f_global_tempo,
#                        f_graph.length_in_seconds)
            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
            global_open_audio_items(True)
            PROJECT.commit(_("Update audio items"))
        self.widget.close()


class fade_vol_dialog_widget:
    def __init__(self, a_audio_item):
        self.widget = QDialog()
        self.widget.setWindowTitle(_("Fade Volume..."))
        self.widget.setMaximumWidth(480)
        self.main_vlayout = QVBoxLayout(self.widget)

        self.layout = QGridLayout()
        self.main_vlayout.addLayout(self.layout)

        self.fadein_vol_layout = QHBoxLayout()
        self.fadein_vol_checkbox = QCheckBox(_("Fade-In:"))
        self.fadein_vol_layout.addWidget(self.fadein_vol_checkbox)
        self.fadein_vol_spinbox = QSpinBox()
        self.fadein_vol_spinbox.setRange(-50, -6)
        self.fadein_vol_spinbox.setValue(a_audio_item.fadein_vol)
        self.fadein_vol_spinbox.valueChanged.connect(self.fadein_vol_changed)
        self.fadein_vol_layout.addWidget(self.fadein_vol_spinbox)
        self.fadein_vol_layout.addItem(
            QSpacerItem(5, 5, QSizePolicy.Expanding))
        self.main_vlayout.addLayout(self.fadein_vol_layout)

        self.fadeout_vol_checkbox = QCheckBox(_("Fade-Out:"))
        self.fadein_vol_layout.addWidget(self.fadeout_vol_checkbox)
        self.fadeout_vol_spinbox = QSpinBox()
        self.fadeout_vol_spinbox.setRange(-50, -6)
        self.fadeout_vol_spinbox.setValue(a_audio_item.fadeout_vol)
        self.fadeout_vol_spinbox.valueChanged.connect(self.fadeout_vol_changed)
        self.fadein_vol_layout.addWidget(self.fadeout_vol_spinbox)

        self.ok_layout = QHBoxLayout()
        self.ok = QPushButton(_("OK"))
        self.ok.pressed.connect(self.ok_handler)
        self.ok_layout.addWidget(self.ok)
        self.cancel = QPushButton(_("Cancel"))
        self.cancel.pressed.connect(self.widget.close)
        self.ok_layout.addWidget(self.cancel)
        self.main_vlayout.addLayout(self.ok_layout)

        self.last_open_dir = global_home

    def fadein_vol_changed(self, a_val=None):
        self.fadein_vol_checkbox.setChecked(True)

    def fadeout_vol_changed(self, a_val=None):
        self.fadeout_vol_checkbox.setChecked(True)

    def ok_handler(self):
        if libmk.IS_PLAYING:
            QMessageBox.warning(
                self.widget, _("Error"),
                _("Cannot edit audio items during playback"))
            return

        self.end_mode = 0

        f_selected_count = 0

        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                if self.fadein_vol_checkbox.isChecked():
                    f_item.audio_item.fadein_vol = \
                        self.fadein_vol_spinbox.value()
                if self.fadeout_vol_checkbox.isChecked():
                    f_item.audio_item.fadeout_vol = \
                        self.fadeout_vol_spinbox.value()
                f_item.draw()
                f_selected_count += 1
        if f_selected_count == 0:
            QMessageBox.warning(
                self.widget, _("Error"), _("No items selected"))
        else:
            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
            global_open_audio_items(True)
            PROJECT.commit(_("Update audio items"))
        self.widget.close()


AUDIO_ITEMS_TO_DROP = []
MIDI_FILES_TO_DROP = []

CURRENT_AUDIO_ITEM_INDEX = None

def global_paif_val_callback(a_port, a_val):
    if CURRENT_ITEM is not None and \
    CURRENT_AUDIO_ITEM_INDEX is not None:
        PROJECT.IPC.pydaw_audio_per_item_fx(
            CURRENT_ITEM.uid, CURRENT_AUDIO_ITEM_INDEX, a_port, a_val)

def global_paif_rel_callback(a_port, a_val):
    if CURRENT_ITEM is not None and \
    CURRENT_AUDIO_ITEM_INDEX is not None:
        f_index_list = AUDIO_SEQ_WIDGET.modulex.get_list()
        CURRENT_ITEM.set_row(CURRENT_AUDIO_ITEM_INDEX, f_index_list)
        PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)

class FileDragDropper(pydaw_widgets.AbstractFileBrowserWidget):
    def __init__(self, a_filter_func=pydaw_util.is_audio_file):
        pydaw_widgets.AbstractFileBrowserWidget.__init__(
            self, a_filter_func=a_filter_func)
        self.list_file.setDragEnabled(True)
        self.list_file.mousePressEvent = self.file_mouse_press_event
        self.preview_button.pressed.connect(self.on_preview)
        self.stop_preview_button.pressed.connect(self.on_stop_preview)

    def on_preview(self):
        f_list = self.list_file.selectedItems()
        if f_list:
            libmk.IPC.pydaw_preview_audio(
                os.path.join(
                *(str(x) for x in (self.last_open_dir, f_list[0].text()))))

    def on_stop_preview(self):
        libmk.IPC.pydaw_stop_preview()

    def file_mouse_press_event(self, a_event):
        QListWidget.mousePressEvent(self.list_file, a_event)
        global AUDIO_ITEMS_TO_DROP, MIDI_FILES_TO_DROP
        AUDIO_ITEMS_TO_DROP = []
        MIDI_FILES_TO_DROP = []
        for f_item in self.list_file.selectedItems():
            f_path = os.path.join(
                *(str(x) for x in (self.last_open_dir, f_item.text())))
            if pydaw_util.is_midi_file(f_path):
                MIDI_FILES_TO_DROP.append(f_path)
            else:
                AUDIO_ITEMS_TO_DROP.append(f_path)

class AudioItemSeqWidget(FileDragDropper):
    """ The parent widget (including the file browser dialog) for the
        AudioItemSeq
    """
    def __init__(self):
        FileDragDropper.__init__(self, pydaw_util.is_audio_file)

        self.modulex = pydaw_widgets.pydaw_per_audio_item_fx_widget(
            global_paif_rel_callback, global_paif_val_callback)

        self.modulex_widget = QWidget()
        self.modulex_widget.setObjectName("plugin_ui")
        self.modulex_vlayout = QVBoxLayout(self.modulex_widget)
        self.folders_tab_widget.addTab(self.modulex_widget, _("Per-Item FX"))
        self.modulex.widget.setDisabled(True)
        self.modulex_vlayout.addWidget(self.modulex.scroll_area)

        self.widget = QWidget()
        self.vlayout = QVBoxLayout()
        self.widget.setLayout(self.vlayout)
        self.controls_grid_layout = QGridLayout()
        self.controls_grid_layout.addItem(
            QSpacerItem(10, 10, QSizePolicy.Expanding), 0, 30)
        self.vlayout.addLayout(self.controls_grid_layout)
        self.vlayout.addWidget(AUDIO_SEQ)

        self.menu_button = QPushButton(_("Menu"))
        self.controls_grid_layout.addWidget(self.menu_button, 0, 3)
        self.action_menu = QMenu(self.widget)
        self.menu_button.setMenu(self.action_menu)
        self.copy_action = self.action_menu.addAction(_("Copy"))
        self.copy_action.triggered.connect(self.on_copy)
        self.copy_action.setShortcut(QKeySequence.Copy)
        self.cut_action = self.action_menu.addAction(_("Cut"))
        self.cut_action.triggered.connect(self.on_cut)
        self.cut_action.setShortcut(QKeySequence.Cut)
        self.paste_action = self.action_menu.addAction(_("Paste"))
        self.paste_action.triggered.connect(self.on_paste)
        self.paste_action.setShortcut(QKeySequence.Paste)
        self.select_all_action = self.action_menu.addAction(_("Select All"))
        self.select_all_action.triggered.connect(self.on_select_all)
        self.select_all_action.setShortcut(QKeySequence.SelectAll)
        self.clear_selection_action = self.action_menu.addAction(
            _("Clear Selection"))
        self.clear_selection_action.triggered.connect(
            AUDIO_SEQ.scene.clearSelection)
        self.clear_selection_action.setShortcut(
            QKeySequence.fromString("Esc"))
        self.action_menu.addSeparator()
        self.delete_selected_action = self.action_menu.addAction(_("Delete"))
        self.delete_selected_action.triggered.connect(self.on_delete_selected)
        self.delete_selected_action.setShortcut(QKeySequence.Delete)
        self.action_menu.addSeparator()
        self.crossfade_action = self.action_menu.addAction(
            _("Crossfade Selected"))
        self.crossfade_action.triggered.connect(AUDIO_SEQ.crossfade_selected)
        self.crossfade_action.setShortcut(
            QKeySequence.fromString("CTRL+F"))

        self.v_zoom_slider = QSlider(QtCore.Qt.Horizontal)
        self.v_zoom_slider.setObjectName("zoom_slider")
        self.v_zoom_slider.setRange(10, 100)
        self.v_zoom_slider.setValue(10)
        self.v_zoom_slider.setSingleStep(1)
        self.v_zoom_slider.setMaximumWidth(150)
        self.v_zoom_slider.valueChanged.connect(self.set_v_zoom)
        self.controls_grid_layout.addWidget(QLabel(_("V")), 0, 45)
        self.controls_grid_layout.addWidget(self.v_zoom_slider, 0, 46)

        self.audio_items_clipboard = []
        self.disable_on_play = (self.menu_button,)
        self.set_multiselect(False)

    def on_play(self):
        for f_item in self.disable_on_play:
            f_item.setEnabled(False)

    def on_stop(self):
        for f_item in self.disable_on_play:
            f_item.setEnabled(True)

    def set_tooltips(self, a_on):
        if a_on:
            self.folders_widget.setToolTip(
                libpydaw.strings.audio_viewer_widget_folders)
            self.modulex.widget.setToolTip(
                libpydaw.strings.audio_viewer_widget_modulex)
        else:
            self.folders_widget.setToolTip("")
            self.modulex.widget.setToolTip("")

    def on_select_all(self):
        if CURRENT_REGION is None or libmk.IS_PLAYING:
            return
        for f_item in AUDIO_SEQ.audio_items:
            f_item.setSelected(True)

    def on_glue_selected(self):
        if CURRENT_REGION is None or libmk.IS_PLAYING:
            return
        AUDIO_SEQ.glue_selected()

    def on_delete_selected(self):
        if CURRENT_REGION is None or libmk.IS_PLAYING:
            return
        AUDIO_SEQ.delete_selected()

    def on_modulex_copy(self):
        if CURRENT_AUDIO_ITEM_INDEX is not None and CURRENT_ITEM:
            f_paif = CURRENT_ITEM
            self.modulex_clipboard = f_paif.get_row(CURRENT_AUDIO_ITEM_INDEX)

    def on_modulex_paste(self):
        if self.modulex_clipboard is not None and CURRENT_ITEM:
            f_paif = CURRENT_ITEM
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_paif.set_row(f_item.track_num, self.modulex_clipboard)
            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
            AUDIO_SEQ_WIDGET.modulex.set_from_list(self.modulex_clipboard)

    def on_modulex_clear(self):
        if CURRENT_ITEM:
            f_paif = CURRENT_ITEM
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_paif.clear_row(f_item.track_num)
            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
            self.modulex.clear_effects()

    def on_copy(self):
        if not CURRENT_ITEM or libmk.IS_PLAYING:
            return 0
        self.audio_items_clipboard = []
        f_per_item_fx_dict = CURRENT_ITEM
        f_count = False
        for f_item in AUDIO_SEQ.get_selected():
            f_count = True
            self.audio_items_clipboard.append(
                (str(f_item.audio_item),
                 f_per_item_fx_dict.get_row(f_item.track_num, True)))
        if not f_count:
            QMessageBox.warning(
                self.widget, _("Error"), _("Nothing selected."))
        return f_count

    def on_cut(self):
        if self.on_copy():
            self.on_delete_selected()

    def on_paste(self):
        if not CURRENT_ITEM or libmk.IS_PLAYING:
            return
        if not self.audio_items_clipboard:
            QMessageBox.warning(
                self.widget, _("Error"),
                _("Nothing copied to the clipboard."))
        AUDIO_SEQ.reselect_on_stop = []
        f_per_item_fx_dict = CURRENT_ITEM
#        f_global_tempo = float(TRANSPORT.tempo_spinbox.value())
        for f_str, f_list in self.audio_items_clipboard:
            AUDIO_SEQ.reselect_on_stop.append(f_str)
            f_index = CURRENT_ITEM.get_next_index()
            if f_index == -1:
                break
            f_item = pydaw_audio_item.from_str(f_str)
            f_start = f_item.start_beat
            if f_start < CURRENT_ITEM_LEN:
#                f_graph = libmk.PROJECT.get_sample_graph_by_uid(f_item.uid)
#                f_item.clip_at_region_end(
#                    CURRENT_ITEM_LEN, f_global_tempo,
#                    f_graph.length_in_seconds)
                CURRENT_ITEM.add_item(f_index, f_item)
                if f_list is not None:
                    f_per_item_fx_dict.set_row(f_index, f_list)
        CURRENT_ITEM.deduplicate_items()
        PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
        PROJECT.commit(_("Paste audio items"))
        global_open_audio_items(True)
        AUDIO_SEQ.scene.clearSelection()
        AUDIO_SEQ.reset_selection()

    def set_v_zoom(self, a_val=None):
        AUDIO_SEQ.set_v_zoom(float(a_val) * 0.1)
        global_open_audio_items(a_reload=False)


def global_open_audio_items(a_update_viewer=True, a_reload=True):
    if a_update_viewer:
        f_selected_list = []
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_selected_list.append(str(f_item.audio_item))
        AUDIO_SEQ.setUpdatesEnabled(False)
        AUDIO_SEQ.update_zoom()
        AUDIO_SEQ.clear_drawn_items()
        if CURRENT_ITEM:
            for k, v in CURRENT_ITEM.items.items():
#                try:
                    f_graph = libmk.PROJECT.get_sample_graph_by_uid(v.uid)
                    if f_graph is None:
                        print(_("Error drawing item for {}, could not get "
                        "sample graph object").format(v.uid))
                        continue
                    AUDIO_SEQ.draw_item(k, v, f_graph)
#                except:
#                    if libmk.IS_PLAYING:
#                        print(_("Exception while loading {}".format(v.uid)))
#                    else:
#                        f_path = libmk.PROJECT.get_wav_path_by_uid(v.uid)
#                        if os.path.isfile(f_path):
#                            f_error_msg = _(
#                                "Unknown error loading sample f_path {}, "
#                                "\n\n{}").format(f_path, locals())
#                        else:
#                            f_error_msg = _(
#                                "Error loading '{}', file does not "
#                                "exist.").format(f_path)
#                        QMessageBox.warning(
#                            MAIN_WINDOW, _("Error"), f_error_msg)
        for f_item in AUDIO_SEQ.audio_items:
            if str(f_item.audio_item) in f_selected_list:
                f_item.setSelected(True)
        AUDIO_SEQ.setUpdatesEnabled(True)
        AUDIO_SEQ.update()
        AUDIO_SEQ.horizontalScrollBar().setMinimum(0)


PIANO_ROLL_SNAP = False
PIANO_ROLL_GRID_WIDTH = 1000.0
PIANO_KEYS_WIDTH = 34  #Width of the piano keys in px
PIANO_ROLL_GRID_MAX_START_TIME = 999.0 + PIANO_KEYS_WIDTH
PIANO_ROLL_NOTE_HEIGHT = pydaw_util.get_file_setting("PIANO_VZOOM", int, 21)
PIANO_ROLL_SNAP_DIVISOR = 4.0
PIANO_ROLL_SNAP_BEATS = 1.0
PIANO_ROLL_SNAP_VALUE = PIANO_ROLL_GRID_WIDTH / PIANO_ROLL_SNAP_DIVISOR
PIANO_ROLL_NOTE_COUNT = 120
PIANO_ROLL_HEADER_HEIGHT = 45
#gets updated by the piano roll to it's real value:
PIANO_ROLL_TOTAL_HEIGHT = 1000
PIANO_ROLL_QUANTIZE_INDEX = 4
PIANO_ROLL_MIN_NOTE_LENGTH = PIANO_ROLL_GRID_WIDTH / 128.0

SELECTED_NOTE_GRADIENT = QLinearGradient(
    QtCore.QPointF(0, 0), QtCore.QPointF(0, 12))
SELECTED_NOTE_GRADIENT.setColorAt(0, QColor(180, 172, 100))
SELECTED_NOTE_GRADIENT.setColorAt(1, QColor(240, 240, 240))

SELECTED_PIANO_NOTE = None   #Used for mouse click hackery

ITEM_SNAP_DIVISORS = {
    0:4.0, 1:1.0, 2:2.0, 3:3.0, 4:4.0, 5:8.0, 6:16.0, 7:32.0
    }

LAST_NOTE_RESIZE = 0.25

def pydaw_set_piano_roll_quantize(a_index=None):
    global PIANO_ROLL_SNAP, PIANO_ROLL_SNAP_VALUE, PIANO_ROLL_SNAP_DIVISOR, \
        PIANO_ROLL_SNAP_BEATS, LAST_NOTE_RESIZE, PIANO_ROLL_QUANTIZE_INDEX, \
        PIANO_ROLL_MIN_NOTE_LENGTH, PIANO_ROLL_GRID_WIDTH

    if a_index is not None:
        PIANO_ROLL_QUANTIZE_INDEX = a_index

    f_width = float(PIANO_ROLL_EDITOR.rect().width()) - \
        float(PIANO_ROLL_EDITOR.verticalScrollBar().width()) - 6.0 - \
        PIANO_KEYS_WIDTH
    f_region_scale = f_width / 1000.0

    PIANO_ROLL_GRID_WIDTH = 1000.0 * MIDI_SCALE * f_region_scale

    if PIANO_ROLL_QUANTIZE_INDEX == 0:
        PIANO_ROLL_SNAP = False
    else:
        PIANO_ROLL_SNAP = True

    PIANO_ROLL_SNAP_DIVISOR = ITEM_SNAP_DIVISORS[PIANO_ROLL_QUANTIZE_INDEX]

    PIANO_ROLL_SNAP_BEATS = 1.0 / PIANO_ROLL_SNAP_DIVISOR
    LAST_NOTE_RESIZE = pydaw_clip_min(LAST_NOTE_RESIZE, PIANO_ROLL_SNAP_BEATS)
    PIANO_ROLL_EDITOR.set_grid_div(PIANO_ROLL_SNAP_DIVISOR)
    PIANO_ROLL_SNAP_VALUE = (PIANO_ROLL_GRID_WIDTH / CURRENT_ITEM_LEN /
        PIANO_ROLL_SNAP_DIVISOR)
    PIANO_ROLL_MIN_NOTE_LENGTH = (PIANO_ROLL_GRID_WIDTH /
        CURRENT_ITEM_LEN / 32.0)

PIANO_ROLL_NOTE_LABELS = [
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

PIANO_NOTE_GRADIENT_TUPLE = \
    ((255, 0, 0), (255, 123, 0), (255, 255, 0), (123, 255, 0), (0, 255, 0),
     (0, 255, 123), (0, 255, 255), (0, 123, 255), (0, 0, 255), (0, 0, 255))

PIANO_ROLL_DELETE_MODE = False
PIANO_ROLL_DELETED_NOTES = []

PIANO_ROLL_HEADER_GRADIENT = QLinearGradient(
    0.0, 0.0, 0.0, PIANO_ROLL_HEADER_HEIGHT)
PIANO_ROLL_HEADER_GRADIENT.setColorAt(0.0, QColor.fromRgb(61, 61, 61))
PIANO_ROLL_HEADER_GRADIENT.setColorAt(0.5, QColor.fromRgb(50,50, 50))
PIANO_ROLL_HEADER_GRADIENT.setColorAt(0.6, QColor.fromRgb(43, 43, 43))
PIANO_ROLL_HEADER_GRADIENT.setColorAt(1.0, QColor.fromRgb(65, 65, 65))

def piano_roll_set_delete_mode(a_enabled):
    global PIANO_ROLL_DELETE_MODE, PIANO_ROLL_DELETED_NOTES
    if a_enabled:
        PIANO_ROLL_EDITOR.setDragMode(QGraphicsView.NoDrag)
        PIANO_ROLL_DELETED_NOTES = []
        PIANO_ROLL_DELETE_MODE = True
        QApplication.setOverrideCursor(
            QCursor(QtCore.Qt.ForbiddenCursor))
    else:
        PIANO_ROLL_EDITOR.setDragMode(QGraphicsView.RubberBandDrag)
        PIANO_ROLL_DELETE_MODE = False
        for f_item in PIANO_ROLL_DELETED_NOTES:
            f_item.delete()
        PIANO_ROLL_EDITOR.selected_note_strings = []
        global_save_and_reload_items()
        QApplication.restoreOverrideCursor()


class PianoRollNoteItem(QGraphicsRectItem):
    """ An individual note in the PianoRollEditor """
    def __init__(
            self, a_length, a_note_height, a_note,
            a_note_item, a_enabled=True):
        QGraphicsRectItem.__init__(self, 0, 0, a_length, a_note_height)
        if a_enabled:
            self.setFlag(QGraphicsItem.ItemIsMovable)
            self.setFlag(QGraphicsItem.ItemIsSelectable)
            self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
            self.setZValue(1002.0)
        else:
            self.setZValue(1001.0)
            self.setEnabled(False)
            self.setOpacity(0.3)
        self.note_height = a_note_height
        self.current_note_text = None
        self.note_item = a_note_item
        self.setAcceptHoverEvents(True)
        self.resize_start_pos = self.note_item.start
        self.is_copying = False
        self.is_velocity_dragging = False
        self.is_velocity_curving = False
        if SELECTED_PIANO_NOTE is not None and \
        a_note_item == SELECTED_PIANO_NOTE:
            self.is_resizing = True
            PIANO_ROLL_EDITOR.click_enabled = True
        else:
            self.is_resizing = False
        self.showing_resize_cursor = False
        self.resize_rect = self.rect()
        self.mouse_y_pos = QCursor.pos().y()
        self.note_text = QGraphicsSimpleTextItem(self)
        self.note_text.setPen(QPen(QtCore.Qt.black))
        self.update_note_text()
        self.vel_line = QGraphicsLineItem(self)
        self.set_vel_line()
        self.set_brush()

    def set_vel_line(self):
        f_vel = self.note_item.velocity
        f_rect = self.rect()
        f_y = (1.0 - (f_vel * 0.007874016)) * f_rect.height()
        f_width = f_rect.width()
        self.vel_line.setLine(0.0, f_y, f_width, f_y)

    def set_brush(self):
        f_val = (1.0 - (self.note_item.velocity / 127.0)) * 9.0
        f_val = pydaw_util.pydaw_clip_value(f_val, 0.0, 9.0)
        f_int = int(f_val)
        f_frac = f_val - f_int
        f_vals = []
        for f_i in range(3):
            f_val = (((PIANO_NOTE_GRADIENT_TUPLE[f_int + 1][f_i] -
                PIANO_NOTE_GRADIENT_TUPLE[f_int][f_i]) * f_frac) +
                PIANO_NOTE_GRADIENT_TUPLE[f_int][f_i])
            f_vals.append(int(f_val))
        f_vals_m1 = pydaw_rgb_minus(f_vals, 90)
        f_vals_m2 = pydaw_rgb_minus(f_vals, 120)
        f_gradient = QLinearGradient(0.0, 0.0, 0.0, self.note_height)
        f_gradient.setColorAt(0.0, QColor(*f_vals_m1))
        f_gradient.setColorAt(0.4, QColor(*f_vals))
        f_gradient.setColorAt(0.6, QColor(*f_vals))
        f_gradient.setColorAt(1.0, QColor(*f_vals_m2))
        self.setBrush(f_gradient)

    def update_note_text(self, a_note_num=None):
        f_note_num = a_note_num if a_note_num is not None \
            else self.note_item.note_num
        f_octave = (f_note_num // 12) - 2
        f_note = PIANO_ROLL_NOTE_LABELS[f_note_num % 12]
        f_text = "{}{}".format(f_note, f_octave)
        if f_text != self.current_note_text:
            self.current_note_text = f_text
            self.note_text.setText(f_text)

    def mouse_is_at_end(self, a_pos):
        f_width = self.rect().width()
        if f_width >= 30.0:
            return a_pos.x() > (f_width - 15.0)
        else:
            return a_pos.x() > (f_width * 0.72)

    def hoverMoveEvent(self, a_event):
        #QGraphicsRectItem.hoverMoveEvent(self, a_event)
        if not self.is_resizing:
            PIANO_ROLL_EDITOR.click_enabled = False
            self.show_resize_cursor(a_event)

    def delete_later(self):
        global PIANO_ROLL_DELETED_NOTES
        if self.isEnabled() and self not in PIANO_ROLL_DELETED_NOTES:
            PIANO_ROLL_DELETED_NOTES.append(self)
            self.hide()

    def delete(self):
        CURRENT_ITEM.remove_note(self.note_item)

    def show_resize_cursor(self, a_event):
        f_is_at_end = self.mouse_is_at_end(a_event.pos())
        if f_is_at_end and not self.showing_resize_cursor:
            QApplication.setOverrideCursor(
                QCursor(QtCore.Qt.SizeHorCursor))
            self.showing_resize_cursor = True
        elif not f_is_at_end and self.showing_resize_cursor:
            QApplication.restoreOverrideCursor()
            self.showing_resize_cursor = False

    def get_selected_string(self):
        return str(self.note_item)

    def hoverEnterEvent(self, a_event):
        QGraphicsRectItem.hoverEnterEvent(self, a_event)
        PIANO_ROLL_EDITOR.click_enabled = False

    def hoverLeaveEvent(self, a_event):
        QGraphicsRectItem.hoverLeaveEvent(self, a_event)
        PIANO_ROLL_EDITOR.click_enabled = True
        QApplication.restoreOverrideCursor()
        self.showing_resize_cursor = False

    def mouseDoubleClickEvent(self, a_event):
        QGraphicsRectItem.mouseDoubleClickEvent(self, a_event)
        QApplication.restoreOverrideCursor()

    def mousePressEvent(self, a_event):
        if not self.isSelected():
            PIANO_ROLL_EDITOR.scene.clearSelection()
            self.setSelected(True)
        if a_event.modifiers() == QtCore.Qt.ShiftModifier:
            piano_roll_set_delete_mode(True)
            self.delete_later()
        elif a_event.modifiers() == \
        QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier:
            self.is_velocity_dragging = True
        elif a_event.modifiers() == \
        QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier:
            f_list = [x.note_item.start
                for x in PIANO_ROLL_EDITOR.get_selected_items()]
            if len(f_list) > 1:
                f_list.sort()
                self.is_velocity_curving = True
                self.vc_start = f_list[0]
                self.vc_mid = self.note_item.start
                self.vc_end = f_list[-1]
            elif len(f_list) <= 1:
                self.is_velocity_dragging = True
        else:
            a_event.setAccepted(True)
            QGraphicsRectItem.mousePressEvent(self, a_event)
            self.setBrush(SELECTED_NOTE_GRADIENT)
            self.o_pos = self.pos()
            if self.mouse_is_at_end(a_event.pos()):
                self.is_resizing = True
                self.mouse_y_pos = QCursor.pos().y()
                self.resize_last_mouse_pos = a_event.pos().x()
                for f_item in PIANO_ROLL_EDITOR.get_selected_items():
                    f_item.resize_start_pos = f_item.note_item.start
                    f_item.resize_pos = f_item.pos()
                    f_item.resize_rect = f_item.rect()
            elif a_event.modifiers() == QtCore.Qt.ControlModifier:
                self.is_copying = True
                for f_item in PIANO_ROLL_EDITOR.get_selected_items():
                    PIANO_ROLL_EDITOR.draw_note(f_item.note_item)
        if self.is_velocity_curving or self.is_velocity_dragging:
            a_event.setAccepted(True)
            QGraphicsRectItem.mousePressEvent(self, a_event)
            self.orig_y = a_event.pos().y()
            QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)
            for f_item in PIANO_ROLL_EDITOR.get_selected_items():
                f_item.orig_value = f_item.note_item.velocity
                f_item.set_brush()
            for f_item in PIANO_ROLL_EDITOR.note_items:
                f_item.note_text.setText(str(f_item.note_item.velocity))
        PIANO_ROLL_EDITOR.click_enabled = True

    def mouseMoveEvent(self, a_event):
        if self.is_velocity_dragging or self.is_velocity_curving:
            f_pos = a_event.pos()
            f_y = f_pos.y()
            f_diff_y = self.orig_y - f_y
            f_val = (f_diff_y * 0.5)
        else:
            QGraphicsRectItem.mouseMoveEvent(self, a_event)

        if self.is_resizing:
            f_pos_x = a_event.pos().x()
            self.resize_last_mouse_pos = a_event.pos().x()
        for f_item in PIANO_ROLL_EDITOR.get_selected_items():
            if self.is_resizing:
                if PIANO_ROLL_SNAP:
                    f_adjusted_width = round(
                        f_pos_x / PIANO_ROLL_SNAP_VALUE) * \
                        PIANO_ROLL_SNAP_VALUE
                    if f_adjusted_width == 0.0:
                        f_adjusted_width = PIANO_ROLL_SNAP_VALUE
                else:
                    f_adjusted_width = pydaw_clip_min(
                        f_pos_x, PIANO_ROLL_MIN_NOTE_LENGTH)
                f_item.resize_rect.setWidth(f_adjusted_width)
                f_item.setRect(f_item.resize_rect)
                f_item.setPos(f_item.resize_pos.x(), f_item.resize_pos.y())
                QCursor.setPos(QCursor.pos().x(), self.mouse_y_pos)
            elif self.is_velocity_dragging:
                f_new_vel = pydaw_util.pydaw_clip_value(
                    f_val + f_item.orig_value, 1, 127)
                f_new_vel = int(f_new_vel)
                f_item.note_item.velocity = f_new_vel
                f_item.note_text.setText(str(f_new_vel))
                f_item.set_brush()
                f_item.set_vel_line()
            elif self.is_velocity_curving:
                f_start = f_item.note_item.start
                if f_start == self.vc_mid:
                    f_new_vel = f_val + f_item.orig_value
                else:
                    if f_start > self.vc_mid:
                        f_frac = (f_start -
                            self.vc_mid) / (self.vc_end - self.vc_mid)
                        f_new_vel = pydaw_util.linear_interpolate(
                            f_val, 0.3 * f_val, f_frac)
                    else:
                        f_frac = (f_start -
                            self.vc_start) / (self.vc_mid - self.vc_start)
                        f_new_vel = pydaw_util.linear_interpolate(
                            0.3 * f_val, f_val, f_frac)
                    f_new_vel += f_item.orig_value
                f_new_vel = pydaw_util.pydaw_clip_value(f_new_vel, 1, 127)
                f_new_vel = int(f_new_vel)
                f_item.note_item.velocity = f_new_vel
                f_item.note_text.setText(str(f_new_vel))
                f_item.set_brush()
                f_item.set_vel_line()
            else:
                f_pos_x = f_item.pos().x()
                f_pos_y = f_item.pos().y()
                if f_pos_x < PIANO_KEYS_WIDTH:
                    f_pos_x = PIANO_KEYS_WIDTH
                elif f_pos_x > PIANO_ROLL_GRID_MAX_START_TIME:
                    f_pos_x = PIANO_ROLL_GRID_MAX_START_TIME
                if f_pos_y < PIANO_ROLL_HEADER_HEIGHT:
                    f_pos_y = PIANO_ROLL_HEADER_HEIGHT
                elif f_pos_y > PIANO_ROLL_TOTAL_HEIGHT:
                    f_pos_y = PIANO_ROLL_TOTAL_HEIGHT
                f_pos_y = \
                    (int((f_pos_y - PIANO_ROLL_HEADER_HEIGHT) /
                    self.note_height) * self.note_height) + \
                    PIANO_ROLL_HEADER_HEIGHT
                if PIANO_ROLL_SNAP:
                    f_pos_x = (int((f_pos_x - PIANO_KEYS_WIDTH) /
                    PIANO_ROLL_SNAP_VALUE) *
                    PIANO_ROLL_SNAP_VALUE) + PIANO_KEYS_WIDTH
                f_item.setPos(f_pos_x, f_pos_y)
                f_new_note = self.y_pos_to_note(f_pos_y)
                f_item.update_note_text(f_new_note)

    def y_pos_to_note(self, a_y):
        return int(PIANO_ROLL_NOTE_COUNT -
            ((a_y - PIANO_ROLL_HEADER_HEIGHT) /
            PIANO_ROLL_NOTE_HEIGHT))

    def mouseReleaseEvent(self, a_event):
        if PIANO_ROLL_DELETE_MODE:
            piano_roll_set_delete_mode(False)
            return
        a_event.setAccepted(True)
        f_recip = 1.0 / PIANO_ROLL_GRID_WIDTH
        QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        global SELECTED_PIANO_NOTE
        if self.is_copying:
            f_new_selection = []
        for f_item in PIANO_ROLL_EDITOR.get_selected_items():
            f_pos_x = f_item.pos().x()
            f_pos_y = f_item.pos().y()
            if self.is_resizing:
                f_new_note_length = ((f_pos_x + f_item.rect().width() -
                    PIANO_KEYS_WIDTH) * f_recip *
                    CURRENT_ITEM_LEN) - f_item.resize_start_pos
                if PIANO_ROLL_SNAP and \
                f_new_note_length < PIANO_ROLL_SNAP_BEATS:
                    f_new_note_length = PIANO_ROLL_SNAP_BEATS
                elif f_new_note_length < pydaw_min_note_length:
                    f_new_note_length = pydaw_min_note_length
                f_item.note_item.set_length(f_new_note_length)
            elif self.is_velocity_dragging or self.is_velocity_curving:
                pass
            else:
                f_new_note_start = (f_pos_x -
                    PIANO_KEYS_WIDTH) * CURRENT_ITEM_LEN * f_recip
                f_new_note_num = self.y_pos_to_note(f_pos_y)
                if self.is_copying:
                    f_new_note = pydaw_note(
                        f_new_note_start, f_item.note_item.length,
                        f_new_note_num, f_item.note_item.velocity)
                    CURRENT_ITEM.add_note(f_new_note, False)
                    # pass a ref instead of a str in case
                    # fix_overlaps() modifies it.
                    f_item.note_item = f_new_note
                    f_new_selection.append(f_item)
                else:
                    CURRENT_ITEM.notes.remove(f_item.note_item)
                    f_item.note_item.set_start(f_new_note_start)
                    f_item.note_item.note_num = f_new_note_num
                    CURRENT_ITEM.notes.append(f_item.note_item)
                    CURRENT_ITEM.notes.sort()
        if self.is_resizing:
            global LAST_NOTE_RESIZE
            LAST_NOTE_RESIZE = self.note_item.length
        CURRENT_ITEM.fix_overlaps()
        SELECTED_PIANO_NOTE = None
        PIANO_ROLL_EDITOR.selected_note_strings = []
        if self.is_copying:
            for f_new_item in f_new_selection:
                PIANO_ROLL_EDITOR.selected_note_strings.append(
                    f_new_item.get_selected_string())
        else:
            for f_item in PIANO_ROLL_EDITOR.get_selected_items():
                PIANO_ROLL_EDITOR.selected_note_strings.append(
                    f_item.get_selected_string())
        for f_item in PIANO_ROLL_EDITOR.note_items:
            f_item.is_resizing = False
            f_item.is_copying = False
            f_item.is_velocity_dragging = False
            f_item.is_velocity_curving = False
        global_save_and_reload_items()
        self.showing_resize_cursor = False
        QApplication.restoreOverrideCursor()
        PIANO_ROLL_EDITOR.click_enabled = True

class PianoKeyItem(QGraphicsRectItem):
    """ This is a piano key on the PianoRollEditor
    """
    def __init__(self, a_piano_width, a_note_height, a_parent):
        QGraphicsRectItem.__init__(
            self, 0, 0, a_piano_width, a_note_height, a_parent)
        self.setAcceptHoverEvents(True)
        self.hover_brush = QColor(200, 200, 200)

    def hoverEnterEvent(self, a_event):
        QGraphicsRectItem.hoverEnterEvent(self, a_event)
        self.o_brush = self.brush()
        self.setBrush(self.hover_brush)
        QApplication.restoreOverrideCursor()

    def hoverLeaveEvent(self, a_event):
        QGraphicsRectItem.hoverLeaveEvent(self, a_event)
        self.setBrush(self.o_brush)

class PianoRollEditor(AbstractItemEditor):
    """ This is the QGraphicsView and QGraphicsScene where notes are drawn
    """
    def __init__(self):
        self.viewer_width = 1000
        self.grid_div = 16

        self.end_octave = 8
        self.start_octave = -2
        self.notes_in_octave = 12
        self.piano_width = 32
        self.padding = 2

        self.update_note_height()

        AbstractItemEditor.__init__(self, PIANO_KEYS_WIDTH)
        self.scene = QGraphicsScene(self)
        self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.scene.setBackgroundBrush(QColor(100, 100, 100))
        self.scene.mousePressEvent = self.sceneMousePressEvent
        self.scene.mouseReleaseEvent = self.sceneMouseReleaseEvent
        self.setAlignment(QtCore.Qt.AlignLeft)
        self.setScene(self.scene)
        self.first_open = True

        self.has_selected = False

        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.note_items = []

        self.right_click = False
        self.left_click = False
        self.click_enabled = True
        self.last_scale = 1.0
        self.last_x_scale = 1.0
        self.scene.selectionChanged.connect(self.highlight_selected)
        self.selected_note_strings = []
        self.piano_keys = None
        self.vel_rand = 0
        self.vel_emphasis = 0
        self.clipboard = []

    def update_note_height(self):
        self.note_height = PIANO_ROLL_NOTE_HEIGHT
        self.octave_height = self.notes_in_octave * self.note_height

        self.piano_height = self.note_height * PIANO_ROLL_NOTE_COUNT

        self.piano_height = self.note_height * PIANO_ROLL_NOTE_COUNT
        global PIANO_ROLL_TOTAL_HEIGHT
        PIANO_ROLL_TOTAL_HEIGHT = self.piano_height + PIANO_ROLL_HEADER_HEIGHT

    def get_selected_items(self):
        return (x for x in self.note_items if x.isSelected())

    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip(libpydaw.strings.PianoRollEditor)
        else:
            self.setToolTip("")

    def prepare_to_quit(self):
        self.scene.clearSelection()
        self.scene.clear()

    def highlight_keys(self, a_state, a_note):
        f_note = int(a_note)
        f_state = int(a_state)
        if self.piano_keys is not None and f_note in self.piano_keys:
            if f_state == 0:
                if self.piano_keys[f_note].is_black:
                    self.piano_keys[f_note].setBrush(QColor(0, 0, 0))
                else:
                    self.piano_keys[f_note].setBrush(
                        QColor(255, 255, 255))
            elif f_state == 1:
                self.piano_keys[f_note].setBrush(QColor(237, 150, 150))
            else:
                assert False, "Invalid state"

    def set_grid_div(self, a_div):
        self.grid_div = int(a_div)

    def scrollContentsBy(self, x, y):
        QGraphicsView.scrollContentsBy(self, x, y)
        self.set_header_and_keys()

    def set_header_and_keys(self):
        f_point = self.get_scene_pos()
        self.piano.setPos(f_point.x(), PIANO_ROLL_HEADER_HEIGHT)
        self.header.setPos(self.piano_width + self.padding, f_point.y())

    def get_scene_pos(self):
        return QtCore.QPointF(
            self.horizontalScrollBar().value(),
            self.verticalScrollBar().value())

    def highlight_selected(self):
        self.has_selected = False
        for f_item in self.note_items:
            if f_item.isSelected():
                f_item.setBrush(SELECTED_NOTE_GRADIENT)
                f_item.note_item.is_selected = True
                self.has_selected = True
            else:
                f_item.note_item.is_selected = False
                f_item.set_brush()

    def set_selected_strings(self):
        self.selected_note_strings = [x.get_selected_string()
            for x in self.note_items if x.isSelected()]

    def keyPressEvent(self, a_event):
        QGraphicsView.keyPressEvent(self, a_event)
        QApplication.restoreOverrideCursor()

    def half_selected(self):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return

        self.selected_note_strings = []

        min_split_size = 4.0 / 64.0

        f_selected = [x for x in self.note_items if x.isSelected()]
        if not f_selected:
            QMessageBox.warning(self, _("Error"), _("Nothing selected"))
            return

        for f_note in f_selected:
            if f_note.note_item.length < min_split_size:
                continue
            f_half = f_note.note_item.length * 0.5
            f_note.note_item.set_length(f_half)
            f_new_start = f_note.note_item.start + f_half
            f_note_num = f_note.note_item.note_num
            f_velocity = f_note.note_item.velocity
            self.selected_note_strings.append(str(f_note.note_item))
            f_new_note_item = pydaw_note(
                f_new_start, f_half, f_note_num, f_velocity)
            CURRENT_ITEM.add_note(f_new_note_item, False)
            self.selected_note_strings.append(str(f_new_note_item))

        global_save_and_reload_items()

    def glue_selected(self):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return

        f_selected = [x for x in self.note_items if x.isSelected()]
        if not f_selected:
            QMessageBox.warning(self, _("Error"), _("Nothing selected"))
            return

        f_dict = {}
        for f_note in f_selected:
            f_note_num = f_note.note_item.note_num
            if not f_note_num in f_dict:
                f_dict[f_note_num] = []
            f_dict[f_note_num].append(f_note)

        f_result = []

        for k in sorted(f_dict.keys()):
            v = f_dict[k]
            if len(v) == 1:
                v[0].setSelected(False)
                f_dict.pop(k)
            else:
                f_max = -1.0
                f_min = 99999999.9
                for f_note in f_dict[k]:
                    f_start = f_note.note_item.start
                    if f_start < f_min:
                        f_min = f_start
                    f_end = f_note.note_item.length + f_start
                    if f_end > f_max:
                        f_max = f_end
                f_vels = [x.note_item.velocity for x in f_dict[k]]
                f_vel = int(sum(f_vels) // len(f_vels))

                print(str(f_max))
                print(str(f_min))
                f_length = f_max - f_min
                print(str(f_length))
                f_start = f_min
                print(str(f_start))
                f_new_note = pydaw_note(f_start, f_length, k, f_vel)
                print(str(f_new_note))
                f_result.append(f_new_note)

        self.delete_selected(False)
        for f_new_note in f_result:
            CURRENT_ITEM.add_note(f_new_note, False)
        global_save_and_reload_items()


    def copy_selected(self):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return 0
        self.clipboard = [
            str(x.note_item) for x in self.note_items if x.isSelected()]
        return len(self.clipboard)

    def paste(self):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return
        if not self.clipboard:
            QMessageBox.warning(
                self, _("Error"), _("Nothing copied to the clipboard"))
            return
        for f_item in self.clipboard:
            CURRENT_ITEM.add_note(pydaw_note.from_str(f_item))
        global_save_and_reload_items()
        self.scene.clearSelection()
        for f_item in self.note_items:
            f_tuple = str(f_item.note_item)
            if f_tuple in self.clipboard:
                f_item.setSelected(True)

    def delete_selected(self, a_save_and_reload=True):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return
        self.selected_note_strings = []
        for f_item in self.get_selected_items():
            CURRENT_ITEM.remove_note(f_item.note_item)
        if a_save_and_reload:
            global_save_and_reload_items()

    def transpose_selected(self, a_amt):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return

        f_list = [x for x in self.note_items if x.isSelected()]
        if not f_list:
            QMessageBox.warning(self, _("Error"), _("No notes selected"))
            return
        self.selected_note_strings = []
        for f_item in f_list:
            f_item.note_item.note_num = pydaw_clip_value(
                f_item.note_item.note_num + a_amt, 0, 120)
            self.selected_note_strings.append(f_item.get_selected_string())
        global_save_and_reload_items()

    def focusOutEvent(self, a_event):
        QGraphicsView.focusOutEvent(self, a_event)
        QApplication.restoreOverrideCursor()

    def sceneMouseReleaseEvent(self, a_event):
        if PIANO_ROLL_DELETE_MODE:
            piano_roll_set_delete_mode(False)
        else:
            QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        self.click_enabled = True

    def sceneMousePressEvent(self, a_event):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
        elif a_event.button() == QtCore.Qt.RightButton:
            return
        elif a_event.modifiers() == QtCore.Qt.ControlModifier:
            if self.click_enabled:
                self.scene.clearSelection()
            self.hover_restore_cursor_event()
        elif a_event.modifiers() == QtCore.Qt.ShiftModifier:
            piano_roll_set_delete_mode(True)
            return
        elif a_event.modifiers() == (
        QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier) or \
        a_event.modifiers() == (
        QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
            pass
        elif self.click_enabled and ITEM_EDITOR.enabled:
            self.scene.clearSelection()
            f_pos_x = a_event.scenePos().x()
            f_pos_y = a_event.scenePos().y()
            if f_pos_x > PIANO_KEYS_WIDTH and \
            f_pos_x < PIANO_ROLL_GRID_MAX_START_TIME and \
            f_pos_y > PIANO_ROLL_HEADER_HEIGHT and \
            f_pos_y < PIANO_ROLL_TOTAL_HEIGHT:
                f_recip = 1.0 / PIANO_ROLL_GRID_WIDTH
                if self.vel_rand == 1:
                    pass
                elif self.vel_rand == 2:
                    pass
                f_note = int(
                    PIANO_ROLL_NOTE_COUNT - ((f_pos_y -
                    PIANO_ROLL_HEADER_HEIGHT) / self.note_height)) + 1
                if PIANO_ROLL_SNAP:
                    f_beat = (int((f_pos_x - PIANO_KEYS_WIDTH) /
                        PIANO_ROLL_SNAP_VALUE) *
                        PIANO_ROLL_SNAP_VALUE) * f_recip * CURRENT_ITEM_LEN
                    f_note_item = pydaw_note(
                        f_beat, LAST_NOTE_RESIZE, f_note, self.get_vel(f_beat))
                else:
                    f_beat = (f_pos_x -
                        PIANO_KEYS_WIDTH) * f_recip * CURRENT_ITEM_LEN
                    f_note_item = pydaw_note(
                        f_beat, 0.25, f_note, self.get_vel(f_beat))
                ITEM_EDITOR.add_note(f_note_item)
                global SELECTED_PIANO_NOTE
                SELECTED_PIANO_NOTE = f_note_item
                f_drawn_note = self.draw_note(f_note_item)
                f_drawn_note.setSelected(True)
                f_drawn_note.resize_start_pos = f_drawn_note.note_item.start
                f_drawn_note.resize_pos = f_drawn_note.pos()
                f_drawn_note.resize_rect = f_drawn_note.rect()
                f_drawn_note.is_resizing = True
                f_cursor_pos = QCursor.pos()
                f_drawn_note.mouse_y_pos = f_cursor_pos.y()
                f_drawn_note.resize_last_mouse_pos = \
                    f_pos_x - f_drawn_note.pos().x()

        a_event.setAccepted(True)
        QGraphicsScene.mousePressEvent(self.scene, a_event)
        QApplication.restoreOverrideCursor()

    def mouseMoveEvent(self, a_event):
        QGraphicsView.mouseMoveEvent(self, a_event)
        if PIANO_ROLL_DELETE_MODE:
            for f_item in self.items(a_event.pos()):
                if isinstance(f_item, PianoRollNoteItem):
                    f_item.delete_later()

    def hover_restore_cursor_event(self, a_event=None):
        QApplication.restoreOverrideCursor()

    def draw_header(self):
        AbstractItemEditor.draw_header(
            self, self.viewer_width, PIANO_ROLL_HEADER_HEIGHT)
        self.header.hoverEnterEvent = self.hover_restore_cursor_event
        self.header.setBrush(PIANO_ROLL_HEADER_GRADIENT)
        self.scene.addItem(self.header)
        #self.header.mapToScene(self.piano_width + self.padding, 0.0)
        self.px_per_beat = self.viewer_width / CURRENT_ITEM_LEN
        self.value_width = self.px_per_beat / self.grid_div
        self.header.setZValue(1003.0)
        if ITEM_REF_POS:
            f_start, f_end = ITEM_REF_POS
            f_start_x = f_start * self.px_per_beat
            f_end_x = f_end * self.px_per_beat
            f_start_line = QGraphicsLineItem(
                f_start_x, 0.0, f_start_x,
                PIANO_ROLL_HEADER_HEIGHT, self.header)
            f_start_line.setPen(START_PEN)
            f_end_line = QGraphicsLineItem(
                f_end_x, 0.0, f_end_x, PIANO_ROLL_HEADER_HEIGHT, self.header)
            f_end_line.setPen(END_PEN)

    def draw_piano(self):
        self.piano_keys = {}
        f_black_notes = [2, 4, 6, 9, 11]
        f_piano_label = QFont()
        f_piano_label.setPointSize(8)
        self.piano = QGraphicsRectItem(
            0, 0, self.piano_width, self.piano_height)
        self.scene.addItem(self.piano)
        self.piano.mapToScene(0.0, PIANO_ROLL_HEADER_HEIGHT)
        f_key = PianoKeyItem(self.piano_width, self.note_height, self.piano)
        f_label = QGraphicsSimpleTextItem("C8", f_key)
        f_label.setPen(QtCore.Qt.black)
        f_label.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        f_label.setPos(4, 0)
        f_label.setFont(f_piano_label)
        f_key.setBrush(QColor(255, 255, 255))
        f_note_index = 0
        f_note_num = 0

        for i in range(self.end_octave - self.start_octave,
                       self.start_octave - self.start_octave, -1):
            for j in range(self.notes_in_octave, 0, -1):
                f_key = PianoKeyItem(
                    self.piano_width, self.note_height, self.piano)
                self.piano_keys[f_note_index] = f_key
                f_note_index += 1
                f_key.setPos(
                    0, (self.note_height * j) + (self.octave_height * (i - 1)))

                f_key.setToolTip("{} - {}hz - MIDI note #{}".format(
                    pydaw_util.note_num_to_string(f_note_num),
                    round(pydaw_pitch_to_hz(f_note_num)), f_note_num))
                f_note_num += 1
                if j == 12:
                    f_label = QGraphicsSimpleTextItem("C{}".format(
                        self.end_octave - i), f_key)
                    f_label.setFlag(
                        QGraphicsItem.ItemIgnoresTransformations)
                    f_label.setPos(4, 0)
                    f_label.setFont(f_piano_label)
                    f_label.setPen(QtCore.Qt.black)
                if j in f_black_notes:
                    f_key.setBrush(QColor(0, 0, 0))
                    f_key.is_black = True
                else:
                    f_key.setBrush(QColor(255, 255, 255))
                    f_key.is_black = False
        self.piano.setZValue(1000.0)

    def draw_grid(self):
        f_black_key_brush = QBrush(QColor(30, 30, 30, 90))
        f_white_key_brush = QBrush(QColor(210, 210, 210, 90))
        f_base_brush = QBrush(QColor(255, 255, 255, 120))
        try:
            f_index = PIANO_ROLL_EDITOR_WIDGET.scale_combobox.currentIndex()
        except NameError:
            f_index = 0
        if self.first_open:
            f_index = 0

        f_octave_brushes = scales.scale_to_value_list(
            f_index, [f_base_brush, f_white_key_brush, f_black_key_brush])

        f_current_key = 0
        if not self.first_open:
            f_index = \
                12 - PIANO_ROLL_EDITOR_WIDGET.scale_key_combobox.currentIndex()
            f_octave_brushes = \
                f_octave_brushes[f_index:] + f_octave_brushes[:f_index]
        self.first_open = False
        f_note_bar = QGraphicsRectItem(
            0, 0, self.viewer_width, self.note_height)
        f_note_bar.hoverMoveEvent = self.hover_restore_cursor_event
        f_note_bar.setBrush(f_base_brush)
        self.scene.addItem(f_note_bar)
        f_note_bar.setPos(
            self.piano_width + self.padding, PIANO_ROLL_HEADER_HEIGHT)
        for i in range(self.end_octave - self.start_octave,
                       self.start_octave - self.start_octave, -1):
            for j in range(self.notes_in_octave, 0, -1):
                f_note_bar = QGraphicsRectItem(
                    0, 0, self.viewer_width, self.note_height)
                f_note_bar.setZValue(60.0)
                self.scene.addItem(f_note_bar)
                f_note_bar.setBrush(f_octave_brushes[f_current_key])
                f_current_key += 1
                if f_current_key >= len(f_octave_brushes):
                    f_current_key = 0
                f_note_bar_y = (self.note_height * j) + (self.octave_height *
                    (i - 1)) + PIANO_ROLL_HEADER_HEIGHT
                f_note_bar.setPos(
                    self.piano_width + self.padding, f_note_bar_y)
        f_beat_pen = QPen()
        f_beat_pen.setWidth(2)
        f_line_pen = QPen(QColor(0, 0, 0))
        self.total_height = \
            self.piano_height + PIANO_ROLL_HEADER_HEIGHT + self.note_height
        for i in range(0, int(CURRENT_ITEM_LEN) + 1):
            f_beat_x = (self.px_per_beat * i) + self.piano_width
            f_beat = self.scene.addLine(
                f_beat_x, 0, f_beat_x, self.total_height)
            f_beat_number = i
            f_beat.setPen(f_beat_pen)
            if i < CURRENT_ITEM_LEN:
                f_number = QGraphicsSimpleTextItem(
                    str(f_beat_number + 1), self.header)
                f_number.setFlag(
                    QGraphicsItem.ItemIgnoresTransformations)
                f_number.setPos((self.px_per_beat * i), 24)
                f_number.setBrush(QtCore.Qt.white)
                for j in range(0, self.grid_div):
                    f_x = (self.px_per_beat * i) + (self.value_width *
                        j) + self.piano_width
                    f_line = self.scene.addLine(
                        f_x, PIANO_ROLL_HEADER_HEIGHT, f_x, self.total_height)
                    if float(j) != self.grid_div * 0.5:
                        f_line.setPen(f_line_pen)

    def resizeEvent(self, a_event):
        QGraphicsView.resizeEvent(self, a_event)
        ITEM_EDITOR.tab_changed()

    def clear_drawn_items(self):
        self.note_items = []
        self.scene.clear()
        self.update_note_height()
        self.draw_header()
        self.draw_piano()
        self.draw_grid()
        self.set_header_and_keys()

    def draw_item(self):
        self.has_selected = False #Reset the selected-ness state...
        self.viewer_width = PIANO_ROLL_GRID_WIDTH
        self.setSceneRect(
            0.0, 0.0, self.viewer_width + 200.0,
            self.piano_height + PIANO_ROLL_HEADER_HEIGHT + 24.0)
        global PIANO_ROLL_GRID_MAX_START_TIME
        PIANO_ROLL_GRID_MAX_START_TIME = (PIANO_ROLL_GRID_WIDTH -
            1.0) + PIANO_KEYS_WIDTH
        self.setUpdatesEnabled(False)
        self.clear_drawn_items()
        if CURRENT_ITEM:
            for f_note in CURRENT_ITEM.notes:
                f_note_item = self.draw_note(f_note)
                f_note_item.resize_last_mouse_pos = \
                    f_note_item.scenePos().x()
                f_note_item.resize_pos = f_note_item.scenePos()
                if f_note_item.get_selected_string() in \
                self.selected_note_strings:
                    f_note_item.setSelected(True)
            if DRAW_LAST_ITEMS and LAST_ITEM:
                f_offset = LAST_ITEM_REF.start_offset - ITEM_REF_POS[0]
                for f_note in LAST_ITEM.notes:
                    f_note_item = self.draw_note(
                        f_note, False, a_offset=f_offset)
            self.scrollContentsBy(0, 0)
#            f_text = QGraphicsSimpleTextItem(f_name, self.header)
#            f_text.setFlag(QGraphicsItem.ItemIgnoresTransformations)
#            f_text.setBrush(QtCore.Qt.yellow)
#            f_text.setPos((f_i * PIANO_ROLL_GRID_WIDTH), 2.0)
        self.setUpdatesEnabled(True)
        self.update()

    def draw_note(self, a_note, a_enabled=True, a_offset=0.0):
        """ a_note is an instance of the pydaw_note class"""
        f_start = (self.piano_width + self.padding +
            self.px_per_beat * (a_note.start - a_offset))
        f_length = self.px_per_beat * a_note.length
        f_note = PIANO_ROLL_HEADER_HEIGHT + self.note_height * \
            (PIANO_ROLL_NOTE_COUNT - a_note.note_num)
        f_note_item = PianoRollNoteItem(
            f_length, self.note_height, a_note.note_num,
            a_note, a_enabled)
        f_note_item.setPos(f_start, f_note)
        self.scene.addItem(f_note_item)
        if a_enabled:
            self.note_items.append(f_note_item)
            return f_note_item

    def set_vel_rand(self, a_rand, a_emphasis):
        self.vel_rand = int(a_rand)
        self.vel_emphasis = int(a_emphasis)

    def get_vel(self, a_beat):
        if self.vel_rand == 0:
            return 100
        f_emph = self.get_beat_emphasis(a_beat)
        if self.vel_rand == 1:
            return random.randint(75 - f_emph, 100 - f_emph)
        elif self.vel_rand == 2:
            return random.randint(75 - f_emph, 100 - f_emph)
        else:
            assert False, "Invalid velocity randomization value"

    def get_beat_emphasis(self, a_beat, a_amt=25.0):
        if self.vel_emphasis == 0:
            return 0
        f_beat = a_beat
        if self.vel_emphasis == 2:
            f_beat += 0.5
        f_beat = f_beat % 1.0
        if f_beat > 0.5:
            f_beat = 0.5 - (f_beat - 0.5)
            f_beat = 0.5 - f_beat
        return int(f_beat * 2.0 * a_amt)


class PianoRollEditorWidget:
    """ This is the parent widget that contains the PianoRollEditor """
    def __init__(self):
        self.widget = QWidget()
        self.vlayout = QVBoxLayout()
        self.widget.setLayout(self.vlayout)

        self.controls_grid_layout = QGridLayout()
        self.scale_key_combobox = QComboBox()
        self.scale_key_combobox.setMinimumWidth(60)
        self.scale_key_combobox.addItems(PIANO_ROLL_NOTE_LABELS)
        self.scale_key_combobox.currentIndexChanged.connect(
            self.reload_handler)
        self.controls_grid_layout.addWidget(QLabel("Key:"), 0, 3)
        self.controls_grid_layout.addWidget(self.scale_key_combobox, 0, 4)
        self.scale_combobox = QComboBox()
        self.scale_combobox.setMinimumWidth(172)
        self.scale_combobox.addItems(scales.SCALE_NAMES)
        self.scale_combobox.currentIndexChanged.connect(self.reload_handler)
        self.controls_grid_layout.addWidget(QLabel(_("Scale:")), 0, 5)
        self.controls_grid_layout.addWidget(self.scale_combobox, 0, 6)

        self.controls_grid_layout.addWidget(QLabel("V"), 0, 45)
        self.vzoom_slider = QSlider(QtCore.Qt.Horizontal)
        self.controls_grid_layout.addWidget(self.vzoom_slider, 0, 46)
        self.vzoom_slider.setObjectName("zoom_slider")
        self.vzoom_slider.setMaximumWidth(72)
        self.vzoom_slider.setRange(9, 24)
        self.vzoom_slider.setValue(PIANO_ROLL_NOTE_HEIGHT)
        self.vzoom_slider.valueChanged.connect(self.set_midi_vzoom)
        self.vzoom_slider.sliderReleased.connect(self.save_vzoom)

        self.controls_grid_layout.addItem(
            QSpacerItem(10, 10, QSizePolicy.Expanding), 0, 30)

        self.edit_menu_button = QPushButton(_("Menu"))
        self.edit_menu_button.setFixedWidth(60)
        self.edit_menu = QMenu(self.widget)
        self.edit_menu_button.setMenu(self.edit_menu)
        self.controls_grid_layout.addWidget(self.edit_menu_button, 0, 30)

        self.edit_actions_menu = self.edit_menu.addMenu(_("Edit"))

        self.copy_action = self.edit_actions_menu.addAction(_("Copy"))
        self.copy_action.triggered.connect(PIANO_ROLL_EDITOR.copy_selected)
        self.copy_action.setShortcut(QKeySequence.Copy)

        self.cut_action = self.edit_actions_menu.addAction(_("Cut"))
        self.cut_action.triggered.connect(self.on_cut)
        self.cut_action.setShortcut(QKeySequence.Cut)

        self.paste_action = self.edit_actions_menu.addAction(_("Paste"))
        self.paste_action.triggered.connect(PIANO_ROLL_EDITOR.paste)
        self.paste_action.setShortcut(QKeySequence.Paste)

        self.select_all_action = self.edit_actions_menu.addAction(
            _("Select All"))
        self.select_all_action.triggered.connect(self.select_all)
        self.select_all_action.setShortcut(QKeySequence.SelectAll)

        self.clear_selection_action = self.edit_actions_menu.addAction(
            _("Clear Selection"))
        self.clear_selection_action.triggered.connect(
            PIANO_ROLL_EDITOR.scene.clearSelection)
        self.clear_selection_action.setShortcut(
            QKeySequence.fromString("Esc"))

        self.edit_actions_menu.addSeparator()

        self.delete_selected_action = self.edit_actions_menu.addAction(
            _("Delete"))
        self.delete_selected_action.triggered.connect(self.on_delete_selected)
        self.delete_selected_action.setShortcut(QKeySequence.Delete)

        self.quantize_action = self.edit_menu.addAction(_("Quantize..."))
        self.quantize_action.triggered.connect(self.quantize_dialog)

        self.transpose_menu = self.edit_menu.addMenu(_("Transpose"))

        self.transpose_action = self.transpose_menu.addAction(_("Dialog..."))
        self.transpose_action.triggered.connect(self.transpose_dialog)

        self.transpose_menu.addSeparator()

        self.up_semitone_action = self.transpose_menu.addAction(
            _("Up Semitone"))
        self.up_semitone_action.triggered.connect(self.transpose_up_semitone)
        self.up_semitone_action.setShortcut(
            QKeySequence.fromString("SHIFT+UP"))

        self.down_semitone_action = self.transpose_menu.addAction(
            _("Down Semitone"))
        self.down_semitone_action.triggered.connect(
            self.transpose_down_semitone)
        self.down_semitone_action.setShortcut(
            QKeySequence.fromString("SHIFT+DOWN"))

        self.up_octave_action = self.transpose_menu.addAction(_("Up Octave"))
        self.up_octave_action.triggered.connect(self.transpose_up_octave)
        self.up_octave_action.setShortcut(
            QKeySequence.fromString("ALT+UP"))

        self.down_octave_action = self.transpose_menu.addAction(
            _("Down Octave"))
        self.down_octave_action.triggered.connect(self.transpose_down_octave)
        self.down_octave_action.setShortcut(
            QKeySequence.fromString("ALT+DOWN"))

        self.velocity_menu = self.edit_menu.addMenu(_("Velocity"))

        self.velocity_menu.addSeparator()

        self.vel_random_index = 0
        self.velocity_random_menu = self.velocity_menu.addMenu(_("Randomness"))
        self.random_types = [_("None"), _("Tight"), _("Loose")]
        self.vel_rand_action_group = QActionGroup(
            self.velocity_random_menu)
        self.velocity_random_menu.triggered.connect(self.vel_rand_triggered)

        for f_i, f_type in zip(
        range(len(self.random_types)), self.random_types):
            f_action = self.velocity_random_menu.addAction(f_type)
            f_action.setActionGroup(self.vel_rand_action_group)
            f_action.setCheckable(True)
            f_action.my_index = f_i
            if f_i == 0:
                f_action.setChecked(True)

        self.vel_emphasis_index = 0
        self.velocity_emphasis_menu = self.velocity_menu.addMenu(_("Emphasis"))
        self.emphasis_types = [_("None"), _("On-beat"), _("Off-beat")]
        self.vel_emphasis_action_group = QActionGroup(
            self.velocity_random_menu)
        self.velocity_emphasis_menu.triggered.connect(
            self.vel_emphasis_triggered)

        for f_i, f_type in zip(
        range(len(self.emphasis_types)), self.emphasis_types):
            f_action = self.velocity_emphasis_menu.addAction(f_type)
            f_action.setActionGroup(self.vel_emphasis_action_group)
            f_action.setCheckable(True)
            f_action.my_index = f_i
            if f_i == 0:
                f_action.setChecked(True)

        self.edit_menu.addSeparator()

        self.glue_selected_action = self.edit_menu.addAction(
            _("Glue Selected"))
        self.glue_selected_action.triggered.connect(
            PIANO_ROLL_EDITOR.glue_selected)
        self.glue_selected_action.setShortcut(
            QKeySequence.fromString("CTRL+G"))

        self.half_selected_action = self.edit_menu.addAction(
            _("Split Selected in Half"))
        self.half_selected_action.triggered.connect(
            PIANO_ROLL_EDITOR.half_selected)
        self.half_selected_action.setShortcut(
            QKeySequence.fromString("CTRL+H"))


        self.edit_menu.addSeparator()

        self.draw_last_action = self.edit_menu.addAction(
            _("Draw Last Item(s)"))
        self.draw_last_action.triggered.connect(self.draw_last)
        self.draw_last_action.setCheckable(True)
        self.draw_last_action.setShortcut(
            QKeySequence.fromString("CTRL+F"))

        self.open_last_action = self.edit_menu.addAction(
            _("Open Last Item(s)"))
        self.open_last_action.triggered.connect(self.open_last)
        self.open_last_action.setShortcut(
            QKeySequence.fromString("ALT+F"))

        self.controls_grid_layout.addItem(
            QSpacerItem(10, 10, QSizePolicy.Expanding), 0, 31)

        self.vlayout.addLayout(self.controls_grid_layout)
        self.vlayout.addWidget(PIANO_ROLL_EDITOR)

    def set_midi_vzoom(self, a_val):
        global PIANO_ROLL_NOTE_HEIGHT
        PIANO_ROLL_NOTE_HEIGHT = a_val
        PIANO_ROLL_EDITOR.draw_item()

    def save_vzoom(self):
        pydaw_util.set_file_setting("PIANO_VZOOM", self.vzoom_slider.value())

    def quantize_dialog(self):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return
        ITEM_EDITOR.quantize_dialog(PIANO_ROLL_EDITOR.has_selected)

    def transpose_dialog(self):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return
        ITEM_EDITOR.transpose_dialog(PIANO_ROLL_EDITOR.has_selected)

    def select_all(self):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return
        for f_note in PIANO_ROLL_EDITOR.note_items:
            f_note.setSelected(True)

    def open_last(self):
        if LAST_ITEM_NAME:
            global_open_items(LAST_ITEM_NAME, a_new_ref=LAST_ITEM_REF)
            PIANO_ROLL_EDITOR.draw_item()

    def draw_last(self):
        global DRAW_LAST_ITEMS
        DRAW_LAST_ITEMS = not DRAW_LAST_ITEMS
        self.draw_last_action.setChecked(DRAW_LAST_ITEMS)
        PIANO_ROLL_EDITOR.draw_item()
        #global_open_items()

    def vel_rand_triggered(self, a_action):
        self.vel_random_index = a_action.my_index
        self.set_vel_rand()

    def vel_emphasis_triggered(self, a_action):
        self.vel_emphasis_index = a_action.my_index
        self.set_vel_rand()

    def transpose_up_semitone(self):
        PIANO_ROLL_EDITOR.transpose_selected(1)

    def transpose_down_semitone(self):
        PIANO_ROLL_EDITOR.transpose_selected(-1)

    def transpose_up_octave(self):
        PIANO_ROLL_EDITOR.transpose_selected(12)

    def transpose_down_octave(self):
        PIANO_ROLL_EDITOR.transpose_selected(-12)

    def set_vel_rand(self, a_val=None):
        PIANO_ROLL_EDITOR.set_vel_rand(
            self.vel_random_index, self.vel_emphasis_index)

    def on_delete_selected(self):
        PIANO_ROLL_EDITOR.delete_selected()

    def on_cut(self):
        if PIANO_ROLL_EDITOR.copy_selected():
            self.on_delete_selected()

    def reload_handler(self, a_val=None):
        PROJECT.set_midi_scale(
            self.scale_key_combobox.currentIndex(),
            self.scale_combobox.currentIndex())
        if CURRENT_ITEM:
            PIANO_ROLL_EDITOR.set_selected_strings()
            global_open_items()
            PIANO_ROLL_EDITOR.draw_item()
        else:
            PIANO_ROLL_EDITOR.clear_drawn_items()


AUTOMATION_POINT_DIAMETER = 15.0
AUTOMATION_POINT_RADIUS = AUTOMATION_POINT_DIAMETER * 0.5
AUTOMATION_RULER_WIDTH = 36.0

AUTOMATION_MIN_HEIGHT = AUTOMATION_RULER_WIDTH - AUTOMATION_POINT_RADIUS

global_automation_gradient = QLinearGradient(
    0, 0, AUTOMATION_POINT_DIAMETER, AUTOMATION_POINT_DIAMETER)
global_automation_gradient.setColorAt(0, QColor(240, 10, 10))
global_automation_gradient.setColorAt(1, QColor(250, 90, 90))

global_automation_selected_gradient = QLinearGradient(
    0, 0, AUTOMATION_POINT_DIAMETER, AUTOMATION_POINT_DIAMETER)
global_automation_selected_gradient.setColorAt(0, QColor(255, 255, 255))
global_automation_selected_gradient.setColorAt(1, QColor(240, 240, 240))

class AutomationItem(QGraphicsEllipseItem):
    """ This is a CC or pitchbend event in an AutomationEditor
    """
    def __init__(self, a_time, a_value, a_cc, a_view, a_is_cc):
        QGraphicsEllipseItem.__init__(
            self, 0, 0, AUTOMATION_POINT_DIAMETER, AUTOMATION_POINT_DIAMETER)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setPos(
            a_time - AUTOMATION_POINT_RADIUS,
            a_value - AUTOMATION_POINT_RADIUS)
        self.setBrush(global_automation_gradient)
        f_pen = QPen(QColor(170, 0, 0), 2.0)
        self.setPen(f_pen)
        self.cc_item = a_cc
        self.parent_view = a_view
        self.is_cc = a_is_cc

    def set_brush(self):
        if self.isSelected():
            self.setBrush(global_automation_selected_gradient)
        else:
            self.setBrush(global_automation_gradient)

    def mouseMoveEvent(self, a_event):
        QGraphicsEllipseItem.mouseMoveEvent(self, a_event)
        for f_point in self.parent_view.automation_points:
            if f_point.isSelected():
                if f_point.pos().x() < AUTOMATION_MIN_HEIGHT:
                    f_point.setPos(
                        AUTOMATION_MIN_HEIGHT, f_point.pos().y())
                elif f_point.pos().x() > self.parent_view.grid_max_start_time:
                    f_point.setPos(
                        self.parent_view.grid_max_start_time,
                        f_point.pos().y())
                if f_point.pos().y() < AUTOMATION_MIN_HEIGHT:
                    f_point.setPos(f_point.pos().x(), AUTOMATION_MIN_HEIGHT)
                elif f_point.pos().y() > self.parent_view.total_height:
                    f_point.setPos(
                        f_point.pos().x(), self.parent_view.total_height)

    def mouseReleaseEvent(self, a_event):
        QGraphicsEllipseItem.mouseReleaseEvent(self, a_event)
        self.parent_view.selected_str = []
        for f_point in self.parent_view.automation_points:
            if f_point.isSelected():
                f_pos_x = f_point.pos().x()
                f_cc_start = (f_pos_x -
                    AUTOMATION_MIN_HEIGHT) / self.parent_view.beat_width
                f_cc_start = pydaw_clip_min(f_cc_start, 0.0)
                f_cc_start = round(f_cc_start, 6)
                if self.is_cc:
                    CURRENT_ITEM.ccs.remove(f_point.cc_item)
                    f_cc_val = (127.0 - (((f_point.pos().y() -
                        AUTOMATION_MIN_HEIGHT) /
                        self.parent_view.viewer_height) * 127.0))

                    f_point.cc_item.start = f_cc_start
                    f_point.cc_item.set_val(f_cc_val)
                    CURRENT_ITEM.ccs.append(f_point.cc_item)
                    CURRENT_ITEM.ccs.sort()
                else:
                    #try:
                    CURRENT_ITEM.pitchbends.remove(f_point.cc_item)
                    #except ValueError:
                    #print("Exception removing {} from list".format(
                        #f_point.cc_item))
                    f_cc_val = (1.0 - (((f_point.pos().y() -
                        AUTOMATION_MIN_HEIGHT) /
                        self.parent_view.viewer_height) * 2.0))

                    f_point.cc_item.start = f_cc_start
                    f_point.cc_item.set_val(f_cc_val)
                    CURRENT_ITEM.pitchbends.append(f_point.cc_item)
                    CURRENT_ITEM.pitchbends.sort()
                self.parent_view.selected_str.append(
                    hash(str(f_point.cc_item)))
        global_save_and_reload_items()

AUTOMATION_EDITORS = []

class AutomationEditor(AbstractItemEditor):
    """ This is the class for both the pitchbend and CC
        QGraphicsView and QGraphicsScene editors on the "Items" tab.
    """
    def __init__(self, a_is_cc=True):
        """ @a_is_cc: True to make self a CC editor, False for a pitchbend
                      editor
        """
        AbstractItemEditor.__init__(self, AUTOMATION_RULER_WIDTH)
        self.is_cc = a_is_cc
        self.set_width()
        self.set_scale()
        self.grid_max_start_time = self.automation_width + \
            AUTOMATION_RULER_WIDTH - AUTOMATION_POINT_RADIUS
        self.automation_points = []
        self.clipboard = []
        self.selected_str = []

        self.axis_size = AUTOMATION_RULER_WIDTH

        self.px_per_beat = self.automation_width / CURRENT_ITEM_LEN
        self.value_width = self.px_per_beat / 16.0
        self.lines = []

        self.setMinimumHeight(370)
        self.scene = QGraphicsScene(self)
        self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.scene.setBackgroundBrush(QColor(100, 100, 100))
        self.scene.mouseDoubleClickEvent = self.sceneMouseDoubleClickEvent
        self.setAlignment(QtCore.Qt.AlignLeft)
        self.setScene(self.scene)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.cc_num = 1
        self.last_scale = 1.0
        self.last_x_scale = 1.0
        AUTOMATION_EDITORS.append(self)
        self.selection_enabled = True
        self.scene.selectionChanged.connect(self.selection_changed)

    def set_width(self):
        self.automation_width = MIDI_SCALE * (self.width() - 60.0)

    def selection_changed(self, a_event=None):
        if self.selection_enabled:
            for f_item in self.automation_points:
                f_item.set_brush()

    def set_tooltips(self, a_enabled=False):
        if a_enabled:
            if self.is_cc:
                f_start = _("Select the CC you wish to "
                    "automate using the comboboxes below\n")
            else:
                f_start = ""
            self.setToolTip(
                _("{}Draw points by double-clicking, then click "
                "the 'smooth' button to "
                "draw extra points between them.\nClick+drag "
                "to select points\n"
                "Press the 'delete' button to delete selected "
                "points.").format(f_start))
        else:
            self.setToolTip("")

    def prepare_to_quit(self):
        self.selection_enabled = False
        self.scene.clearSelection()
        self.scene.clear()

    def copy_selected(self):
        if not ITEM_EDITOR.enabled:
            return
        self.clipboard = [x.cc_item.clone()
            for x in self.automation_points if x.isSelected()]
        self.clipboard.sort()

    def cut(self):
        self.copy_selected()
        self.delete_selected()

    def paste(self):
        if not ITEM_EDITOR.enabled:
            return
        self.selected_str = []
        if self.clipboard:
            self.clear_range(
                self.clipboard[0].start, self.clipboard[-1].start)
            for f_item in self.clipboard:
                f_item2 = f_item.clone()
                if self.is_cc:
                    f_item2.cc_num = self.cc_num
                    CURRENT_ITEM.add_cc(f_item2)
                else:
                    CURRENT_ITEM.add_pb(f_item2)
                self.selected_str.append(hash(str(f_item2)))
            global_save_and_reload_items()

    def clear_range(self, a_start_beat, a_end_beat, a_save=False):
        for f_point in self.automation_points:
            f_pt_start = f_point.cc_item.start
            if f_pt_start >= a_start_beat and \
            f_pt_start <= a_end_beat:
                if self.is_cc:
                    CURRENT_ITEM.remove_cc(f_point.cc_item)
                else:
                    CURRENT_ITEM.remove_pb(f_point.cc_item)
        if a_save:
            self.selected_str = []
            global_save_and_reload_items()

    def delete_selected(self):
        if not ITEM_EDITOR.enabled:
            return
        self.selection_enabled = False
        for f_point in self.automation_points:
            if f_point.isSelected():
                if self.is_cc:
                    CURRENT_ITEM.remove_cc(f_point.cc_item)
                else:
                    CURRENT_ITEM.remove_pb(f_point.cc_item)
        self.selected_str = []
        global_save_and_reload_items()
        self.selection_enabled = True

    def clear_current_item(self):
        """ If this is a CC editor, it only clears the selected CC.  """
        self.selection_enabled = False
        if not self.automation_points:
            return
        for f_point in self.automation_points:
            if self.is_cc:
                CURRENT_ITEM.remove_cc(f_point.cc_item)
            else:
                CURRENT_ITEM.remove_pb(f_point.cc_item)
        self.selected_str = []
        global_save_and_reload_items()
        self.selection_enabled = True

    def sceneMouseDoubleClickEvent(self, a_event):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return
        f_pos_x = a_event.scenePos().x() - AUTOMATION_POINT_RADIUS
        f_pos_y = a_event.scenePos().y() - AUTOMATION_POINT_RADIUS
        f_cc_start = (f_pos_x - AUTOMATION_MIN_HEIGHT) / self.px_per_beat
        f_cc_start = pydaw_clip_min(f_cc_start, 0.0)
        if self.is_cc:
            f_cc_val = int(127.0 - (((f_pos_y - AUTOMATION_MIN_HEIGHT) /
                self.viewer_height) * 127.0))
            f_cc_val = pydaw_clip_value(f_cc_val, 0, 127)
            ITEM_EDITOR.add_cc(pydaw_cc(f_cc_start, self.cc_num, f_cc_val))
        else:
            f_cc_val = 1.0 - (((f_pos_y - AUTOMATION_MIN_HEIGHT) /
                self.viewer_height) * 2.0)
            f_cc_val = pydaw_clip_value(f_cc_val, -1.0, 1.0)
            ITEM_EDITOR.add_pb(pydaw_pitchbend(f_cc_start, f_cc_val))
        QGraphicsScene.mouseDoubleClickEvent(self.scene, a_event)
        self.selected_str = []
        global_save_and_reload_items()

    def draw_header(self):
        AbstractItemEditor.draw_header(
            self, self.automation_width, self.axis_size)
        self.header.setPos(self.axis_size, 0)
        self.scene.addItem(self.header)
        self.y_axis = QGraphicsRectItem(
            0, 0, self.axis_size, self.viewer_height)
        self.y_axis.setPos(0, self.axis_size)
        self.scene.addItem(self.y_axis)
        if ITEM_REF_POS:
            f_start, f_end = ITEM_REF_POS
            f_start_x = f_start * self.px_per_beat
            f_end_x = f_end * self.px_per_beat
            f_start_line = QGraphicsLineItem(
                f_start_x, 0.0, f_start_x, self.axis_size, self.header)
            f_start_line.setPen(START_PEN)
            f_end_line = QGraphicsLineItem(
                f_end_x, 0.0, f_end_x, self.axis_size, self.header)
            f_end_line.setPen(END_PEN)


    def draw_grid(self):
        self.set_width()
        f_beat_pen = QPen()
        f_beat_pen.setWidth(2)

        if self.is_cc:
            f_labels = [0, '127', 0, '64', 0, '0']
        else:
            f_labels = [0, '1.0', 0, '0', 0, '-1.0']
        for i in range(1, 6):
            f_line = QGraphicsLineItem(
                0, 0, self.automation_width, 0, self.y_axis)
            f_line.setPos(self.axis_size, self.viewer_height * (i - 1) / 4)
            if i % 2:
                f_label = QGraphicsSimpleTextItem(
                    f_labels[i], self.y_axis)
                f_label.setPos(1, self.viewer_height * (i - 1) / 4)
                f_label.setBrush(QtCore.Qt.white)
            if i == 3:
                f_line.setPen(f_beat_pen)

        for i in range(0, int(CURRENT_ITEM_LEN) + 1):
            f_beat = QGraphicsLineItem(
                0, 0, 0,
                self.viewer_height + self.axis_size - f_beat_pen.width(),
                self.header)
            f_beat.setPos(self.px_per_beat * i, 0.5 * f_beat_pen.width())
            f_beat.setFlag(QGraphicsItem.ItemIgnoresTransformations)

            f_beat.setPen(f_beat_pen)
            f_beat.setFlag(QGraphicsItem.ItemIgnoresTransformations)

            f_number = QGraphicsSimpleTextItem(
                str(i + 1), self.header)
            f_number.setFlag(
                QGraphicsItem.ItemIgnoresTransformations)
            f_number.setPos(self.px_per_beat * i + 5, 2)
            f_number.setBrush(QtCore.Qt.white)
#                for j in range(0, 16):
#                    f_line = QGraphicsLineItem(
#                        0, 0, 0, self.viewer_height, self.header)
#                    if float(j) == 8:
#                        f_line.setLine(0, 0, 0, self.viewer_height)
#                        f_line.setPos(
#                            (self.px_per_beat * i) + (self.value_width * j),
#                            self.axis_size)
#                    else:
#                        f_line.setPos((self.px_per_beat * i) +
#                            (self.value_width * j), self.axis_size)
#                        f_line.setPen(f_line_pen)

    def clear_drawn_items(self):
        self.selection_enabled = False
        self.scene.clear()
        self.automation_points = []
        self.lines = []
        self.draw_header()
        self.draw_grid()
        self.selection_enabled = True

    def resizeEvent(self, a_event):
        QGraphicsView.resizeEvent(self, a_event)
        ITEM_EDITOR.tab_changed()

    def set_scale(self):
        f_rect = self.rect()
        self.viewer_height = float(f_rect.height()) - \
            self.horizontalScrollBar().height() - \
            30.0 - AUTOMATION_RULER_WIDTH
        self.total_height = AUTOMATION_RULER_WIDTH + \
            self.viewer_height - AUTOMATION_POINT_RADIUS

    def set_cc_num(self, a_cc_num):
        self.cc_num = a_cc_num
        self.clear_drawn_items()
        self.draw_item()

    def draw_item(self):
        self.set_width()
        self.setUpdatesEnabled(False)
        self.set_scale()
        self.px_per_beat = self.automation_width / CURRENT_ITEM_LEN
        self.value_width = self.px_per_beat / 16.0
        self.grid_max_start_time = (self.automation_width +
            AUTOMATION_RULER_WIDTH - AUTOMATION_POINT_DIAMETER)
        self.clear_drawn_items()
        if not ITEM_EDITOR.enabled:
            self.setUpdatesEnabled(True)
            return
        f_pen = QPen(pydaw_note_gradient, 2.0)
        f_note_height = (self.viewer_height / 127.0)

        if self.is_cc:
            for f_cc in CURRENT_ITEM.ccs:
                if f_cc.cc_num == self.cc_num:
                    self.draw_point(f_cc)
        else:
            for f_pb in CURRENT_ITEM.pitchbends:
                self.draw_point(f_pb)
        for f_note in CURRENT_ITEM.notes:
            f_note_start = (f_note.start *
                self.px_per_beat) + AUTOMATION_RULER_WIDTH
            f_note_end = f_note_start + (f_note.length * self.px_per_beat)
            f_note_y = AUTOMATION_RULER_WIDTH + (127.0 -
                f_note.note_num) * f_note_height
            f_note_item = QGraphicsLineItem(
                f_note_start, f_note_y, f_note_end, f_note_y)
            f_note_item.setPen(f_pen)
            self.scene.addItem(f_note_item)

        self.setSceneRect(
            0.0, 0.0, self.grid_max_start_time + 20.0, self.height())
        self.setUpdatesEnabled(True)
        self.update()

    def draw_point(self, a_cc, a_select=True):
        """ a_cc is an instance of the pydaw_cc class"""
        f_time = self.axis_size + (a_cc.start * self.px_per_beat)
        if self.is_cc:
            f_value = self.axis_size +  self.viewer_height / 127.0 * (127.0 -
                a_cc.cc_val)
        else:
            f_value = self.axis_size +  self.viewer_height / 2.0 * (1.0 -
                a_cc.pb_val)
        f_point = AutomationItem(
            f_time, f_value, a_cc, self, self.is_cc)
        self.automation_points.append(f_point)
        self.scene.addItem(f_point)
        if a_select and hash(str(a_cc)) in self.selected_str:
            f_point.setSelected(True)

    def select_all(self):
        self.setUpdatesEnabled(False)
        for f_item in self.automation_points:
            f_item.setSelected(True)
        self.setUpdatesEnabled(True)
        self.update()

LAST_IPB_VALUE = 18  #For the 'add point' dialog to remember settings

class AutomationEditorWidget:
    def __init__(self, a_viewer, a_is_cc=True):
        self.is_cc = a_is_cc
        self.widget = QWidget()
        self.vlayout = QVBoxLayout()
        self.widget.setLayout(self.vlayout)
        self.automation_viewer = a_viewer
        self.vlayout.addWidget(self.automation_viewer)
        self.hlayout = QHBoxLayout()

        if a_is_cc:
            self.control_combobox = QComboBox()
            self.control_combobox.addItems([str(x) for x in range(1, 128)])
            self.control_combobox.setMinimumWidth(90)
            self.hlayout.addWidget(QLabel(_("CC")))
            self.hlayout.addWidget(self.control_combobox)
            self.control_combobox.currentIndexChanged.connect(
                self.control_changed)
            self.ccs_in_use_combobox = QComboBox()
            self.ccs_in_use_combobox.setMinimumWidth(90)
            self.suppress_ccs_in_use = False
            self.ccs_in_use_combobox.currentIndexChanged.connect(
                self.ccs_in_use_combobox_changed)
            self.hlayout.addWidget(QLabel(_("In Use:")))
            self.hlayout.addWidget(self.ccs_in_use_combobox)

        self.vlayout.addLayout(self.hlayout)
        self.smooth_button = QPushButton(_("Smooth"))
        self.smooth_button.setToolTip(
            _("By default, the control points are steppy, "
            "this button draws extra points between the exisiting points."))
        self.smooth_button.pressed.connect(self.smooth_pressed)
        self.hlayout.addWidget(self.smooth_button)
        self.hlayout.addItem(QSpacerItem(10, 10))
        self.edit_button = QPushButton(_("Menu"))
        self.hlayout.addWidget(self.edit_button)
        self.edit_menu = QMenu(self.widget)
        self.copy_action = self.edit_menu.addAction(_("Copy"))
        self.copy_action.triggered.connect(
            self.automation_viewer.copy_selected)
        self.copy_action.setShortcut(QKeySequence.Copy)
        self.cut_action = self.edit_menu.addAction(_("Cut"))
        self.cut_action.triggered.connect(self.automation_viewer.cut)
        self.cut_action.setShortcut(QKeySequence.Cut)
        self.paste_action = self.edit_menu.addAction(_("Paste"))
        self.paste_action.triggered.connect(self.automation_viewer.paste)
        self.paste_action.setShortcut(QKeySequence.Paste)
        self.select_all_action = self.edit_menu.addAction(_("Select All"))
        self.select_all_action.triggered.connect(self.select_all)
        self.select_all_action.setShortcut(QKeySequence.SelectAll)
        self.delete_action = self.edit_menu.addAction(_("Delete"))
        self.delete_action.triggered.connect(
            self.automation_viewer.delete_selected)
        self.delete_action.setShortcut(QKeySequence.Delete)

        self.edit_menu.addSeparator()
        self.add_point_action = self.edit_menu.addAction(_("Add Point..."))
        if self.is_cc:
            self.add_point_action.triggered.connect(self.add_cc_point)
            self.paste_point_action = self.edit_menu.addAction(
                _("Paste Point from Plugin..."))
            self.paste_point_action.triggered.connect(self.paste_cc_point)
        else:
            self.add_point_action.triggered.connect(self.add_pb_point)
        self.edit_menu.addSeparator()
        self.clear_action = self.edit_menu.addAction(_("Clear"))
        self.clear_action.triggered.connect(self.clear)
        self.edit_button.setMenu(self.edit_menu)
        self.hlayout.addItem(
            QSpacerItem(10, 10, QSizePolicy.Expanding))

    def control_changed(self, a_val=None):
        self.set_cc_num()
        self.ccs_in_use_combobox.setCurrentIndex(0)

    def set_cc_num(self, a_val=None):
        f_cc_num = int(str(self.control_combobox.currentText()))
        self.automation_viewer.set_cc_num(f_cc_num)

    def ccs_in_use_combobox_changed(self, a_val=None):
        if not self.suppress_ccs_in_use:
            f_str = str(self.ccs_in_use_combobox.currentText())
            if f_str != "":
                self.control_combobox.setCurrentIndex(
                    self.control_combobox.findText(f_str))

    def update_ccs_in_use(self, a_ccs):
        self.suppress_ccs_in_use = True
        self.ccs_in_use_combobox.clear()
        self.ccs_in_use_combobox.addItem("")
        for f_cc in sorted(a_ccs):
            self.ccs_in_use_combobox.addItem(str(f_cc))
        self.suppress_ccs_in_use = False

    def smooth_pressed(self):
        if self.is_cc:
            f_cc_num = int(str(self.control_combobox.currentText()))
            CURRENT_ITEM.smooth_automation_points(self.is_cc, f_cc_num)
        else:
            CURRENT_ITEM.smooth_automation_points(self.is_cc)
        self.automation_viewer.selected_str = []
        global_save_and_reload_items()

    def select_all(self):
        self.automation_viewer.select_all()

    def clear(self):
        self.automation_viewer.clear_current_item()

    def paste_cc_point(self):
        if pydaw_widgets.CC_CLIPBOARD is None:
            QMessageBox.warning(
                self.widget, _("Error"),
                _("Nothing copied to the clipboard.\n"
                "Right-click->'Copy' on any knob on any plugin."))
            return
        self.add_cc_point(pydaw_widgets.CC_CLIPBOARD)

    def add_cc_point(self, a_value=None):
        if not ITEM_EDITOR.enabled:  #TODO:  Make this global...
            ITEM_EDITOR.show_not_enabled_warning()
            return

        def ok_handler():
            f_cc = pydaw_cc(
                f_pos_spinbox.value() - 1.0, self.automation_viewer.cc_num,
                f_value_spinbox.value())
            CURRENT_ITEM.add_cc(f_cc)

            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
            global_open_items(CURRENT_ITEM_NAME)
            PROJECT.commit(_("Add automation point"))
            self.automation_viewer.draw_item()

        def goto_start():
            f_pos_spinbox.setValue(f_pos_spinbox.minimum())

        def goto_end():
            f_pos_spinbox.setValue(f_pos_spinbox.maximum())

        def cancel_handler():
            f_window.close()

        f_window = QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Add automation point"))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)

        f_layout.addWidget(QLabel(_("Position (beats)")), 5, 0)
        f_pos_spinbox = QDoubleSpinBox()
        f_pos_spinbox.setRange(1.0, CURRENT_ITEM_LEN + 0.98)
        f_pos_spinbox.setDecimals(2)
        f_pos_spinbox.setSingleStep(0.25)
        f_layout.addWidget(f_pos_spinbox, 5, 1)

        f_begin_end_layout = QHBoxLayout()
        f_layout.addLayout(f_begin_end_layout, 6, 1)
        f_start_button = QPushButton("<<")
        f_start_button.pressed.connect(goto_start)
        f_begin_end_layout.addWidget(f_start_button)
        f_begin_end_layout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding))
        f_end_button = QPushButton(">>")
        f_end_button.pressed.connect(goto_end)
        f_begin_end_layout.addWidget(f_end_button)

        f_layout.addWidget(QLabel(_("Value")), 10, 0)
        f_value_spinbox = QDoubleSpinBox()
        f_value_spinbox.setRange(0.0, 127.0)
        f_value_spinbox.setDecimals(4)
        if a_value is not None:
            f_value_spinbox.setValue(a_value)
        f_layout.addWidget(f_value_spinbox, 10, 1)

        f_ok = QPushButton(_("Add"))
        f_ok.pressed.connect(ok_handler)
        f_ok_cancel_layout = QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok)

        f_layout.addLayout(f_ok_cancel_layout, 40, 1)
        f_cancel = QPushButton(_("Close"))
        f_cancel.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec_()

    def add_pb_point(self):
        if not ITEM_EDITOR.enabled:  #TODO:  Make this global...
            ITEM_EDITOR.show_not_enabled_warning()
            return

        def ok_handler():
            f_value = pydaw_clip_value(
                f_epb_spinbox.value() / f_ipb_spinbox.value(),
                -1.0, 1.0, a_round=True)
            f_pb = pydaw_pitchbend(f_pos_spinbox.value() - 1.0, f_value)
            CURRENT_ITEM.add_pb(f_pb)

            global LAST_IPB_VALUE
            LAST_IPB_VALUE = f_ipb_spinbox.value()

            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
            global_open_items(CURRENT_ITEM_NAME)
            PROJECT.commit(_("Add pitchbend automation point"))
            self.automation_viewer.draw_item()

        def cancel_handler():
            f_window.close()

        def ipb_changed(a_self=None, a_event=None):
            f_epb_spinbox.setRange(
                f_ipb_spinbox.value() * -1, f_ipb_spinbox.value())

        def goto_start():
            f_pos_spinbox.setValue(f_pos_spinbox.minimum())

        def goto_end():
            f_pos_spinbox.setValue(f_pos_spinbox.maximum())

        f_window = QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Add automation point"))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)

        f_layout.addWidget(QLabel(_("Position (beats)")), 5, 0)
        f_pos_spinbox = QDoubleSpinBox()
        f_pos_spinbox.setRange(1.0, CURRENT_ITEM_LEN + 0.98)
        f_pos_spinbox.setDecimals(2)
        f_pos_spinbox.setSingleStep(0.25)
        f_layout.addWidget(f_pos_spinbox, 5, 1)

        f_begin_end_layout = QHBoxLayout()
        f_layout.addLayout(f_begin_end_layout, 6, 1)
        f_start_button = QPushButton("<<")
        f_start_button.pressed.connect(goto_start)
        f_begin_end_layout.addWidget(f_start_button)
        f_begin_end_layout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding))
        f_end_button = QPushButton(">>")
        f_end_button.pressed.connect(goto_end)
        f_begin_end_layout.addWidget(f_end_button)

        f_layout.addWidget(QLabel(_("Instrument Pitchbend")), 10, 0)
        f_ipb_spinbox = QSpinBox()
        f_ipb_spinbox.setToolTip(
            _("Set this to the same setting that your instrument plugin uses"))
        f_ipb_spinbox.setRange(2, 36)
        f_ipb_spinbox.setValue(LAST_IPB_VALUE)
        f_layout.addWidget(f_ipb_spinbox, 10, 1)
        f_ipb_spinbox.valueChanged.connect(ipb_changed)

        f_layout.addWidget(QLabel(_("Effective Pitchbend")), 20, 0)
        f_epb_spinbox = QSpinBox()
        f_epb_spinbox.setToolTip("")
        f_epb_spinbox.setRange(-18, 18)
        f_layout.addWidget(f_epb_spinbox, 20, 1)

        f_layout.addWidget(QLabel(
            libpydaw.strings.pitchbend_dialog), 30, 1)

        f_ok = QPushButton(_("Add"))
        f_ok.pressed.connect(ok_handler)
        f_ok_cancel_layout = QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok)

        f_layout.addLayout(f_ok_cancel_layout, 40, 1)
        f_cancel = QPushButton(_("Close"))
        f_cancel.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec_()


DRAW_LAST_ITEMS = False
MIDI_SCALE = 1.0
ITEM_REF_POS = None

def global_set_midi_zoom(a_val):
    global MIDI_SCALE
    MIDI_SCALE = a_val
    pydaw_set_piano_roll_quantize()


def global_open_items(a_items=None, a_reset_scrollbar=False, a_new_ref=None):
    """ a_items is a str which is the name of the item.
        Leave blank to open the existing list
    """
    global CURRENT_ITEM, CURRENT_ITEM_NAME, CURRENT_ITEM_LEN, ITEM_REF_POS, \
        LAST_ITEM, LAST_ITEM_NAME, LAST_ITEM_REF, CURRENT_ITEM_REF

    if a_new_ref:
        LAST_ITEM_REF = CURRENT_ITEM_REF
        CURRENT_ITEM_REF = a_new_ref

    if CURRENT_ITEM_REF:
        f_ref_end = \
            CURRENT_ITEM_REF.length_beats + CURRENT_ITEM_REF.start_offset
        ITEM_REF_POS = (CURRENT_ITEM_REF.start_offset, f_ref_end)
    else:
        ITEM_REF_POS = (0.0, 4.0)

    if a_items is not None:
        ITEM_EDITOR.enabled = True
        PIANO_ROLL_EDITOR.selected_note_strings = []
        pydaw_set_piano_roll_quantize()
        if a_reset_scrollbar:
            for f_editor in MIDI_EDITORS:
                f_editor.horizontalScrollBar().setSliderPosition(0)
        f_items_dict = PROJECT.get_items_dict()
        LAST_ITEM_NAME = CURRENT_ITEM_NAME
        LAST_ITEM = CURRENT_ITEM
        f_uid = f_items_dict.get_uid_by_name(a_items)
        CURRENT_ITEM = PROJECT.get_item_by_uid(f_uid)
        CURRENT_ITEM_NAME = a_items
        ITEM_EDITOR.item_name_lineedit.setText(a_items)

    if CURRENT_ITEM:
        CURRENT_ITEM_LEN = CURRENT_ITEM.get_length(
            CURRENT_REGION.get_tempo_at_pos(CURRENT_ITEM_REF.start_beat))
        CURRENT_ITEM_LEN = max(
            (CURRENT_ITEM_LEN,
            CURRENT_ITEM_REF.length_beats + CURRENT_ITEM_REF.start_offset))
    else:
        CURRENT_ITEM_LEN = 4

    CC_EDITOR.clear_drawn_items()
    PB_EDITOR.clear_drawn_items()
    ITEM_EDITOR.items = []
    f_cc_set = set()

    if CURRENT_ITEM:
        for cc in CURRENT_ITEM.ccs:
            f_cc_set.add(cc.cc_num)

        CC_EDITOR_WIDGET.update_ccs_in_use(list(f_cc_set))

        if a_items is not None and f_cc_set:
            CC_EDITOR_WIDGET.set_cc_num(sorted(f_cc_set)[0])

    #ITEM_EDITOR.tab_changed()


def global_save_and_reload_items():
    PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)
    global_open_items()
    PROJECT.commit(_("Edit item"))
    ITEM_EDITOR.tab_changed()

CURRENT_ITEM_NAME = None
LAST_ITEM_NAME = None
CURRENT_ITEM = None
CURRENT_ITEM_REF = None
LAST_ITEM = None
LAST_ITEM_REF = None
CURRENT_ITEM_LEN = 4

class ItemListViewer:
    """ This is the "Items" tab in MainWindow
    """
    def __init__(self):
        self.enabled = False
        self.events_follow_default = True

        self.widget = QWidget()
        self.master_vlayout = QVBoxLayout()
        self.widget.setLayout(self.master_vlayout)

        self.tab_widget = QTabWidget()

        AUDIO_SEQ_WIDGET.hsplitter.insertWidget(0, AUDIO_SEQ_WIDGET.widget)
        self.tab_widget.addTab(AUDIO_SEQ_WIDGET.hsplitter, _("Audio"))

        self.piano_roll_tab = QWidget()
        self.tab_widget.addTab(self.piano_roll_tab, _("Piano Roll"))
        self.notes_tab = QWidget()
        self.cc_tab = QWidget()
        self.tab_widget.addTab(self.cc_tab, _("CC"))

        self.pitchbend_tab = QWidget()
        self.tab_widget.addTab(self.pitchbend_tab, _("Pitchbend"))

        self.editing_hboxlayout = QHBoxLayout()
        self.master_vlayout.addWidget(self.tab_widget)

        self.notes_groupbox = QGroupBox(_("Notes"))
        self.notes_vlayout = QVBoxLayout(self.notes_groupbox)

        self.cc_vlayout = QVBoxLayout()
        self.cc_tab.setLayout(self.cc_vlayout)

        self.notes_table_widget = QTableWidget()
        self.notes_table_widget.setVerticalScrollMode(
            QAbstractItemView.ScrollPerPixel)
        self.notes_table_widget.setColumnCount(5)
        self.notes_table_widget.setSortingEnabled(True)
        self.notes_table_widget.sortItems(0)
        self.notes_table_widget.setEditTriggers(
            QAbstractItemView.NoEditTriggers)
        self.notes_table_widget.setSelectionBehavior(
            QAbstractItemView.SelectRows)
        self.notes_vlayout.addWidget(self.notes_table_widget)
        self.notes_table_widget.resizeColumnsToContents()

        self.notes_hlayout = QHBoxLayout()
        self.list_tab_vlayout = QVBoxLayout()
        self.notes_tab.setLayout(self.list_tab_vlayout)
        self.list_tab_vlayout.addLayout(self.editing_hboxlayout)
        self.list_tab_vlayout.addLayout(self.notes_hlayout)
        self.notes_hlayout.addWidget(self.notes_groupbox)

        self.piano_roll_hlayout = QHBoxLayout(self.piano_roll_tab)
        self.piano_roll_hlayout.setContentsMargins(2, 2, 2, 2)
        self.piano_roll_hlayout.addWidget(PIANO_ROLL_EDITOR_WIDGET.widget)

        self.ccs_groupbox = QGroupBox(_("CCs"))
        self.ccs_vlayout = QVBoxLayout(self.ccs_groupbox)

        self.ccs_table_widget = QTableWidget()
        self.ccs_table_widget.setVerticalScrollMode(
            QAbstractItemView.ScrollPerPixel)
        self.ccs_table_widget.setColumnCount(3)
        self.ccs_table_widget.setSortingEnabled(True)
        self.ccs_table_widget.sortItems(0)
        self.ccs_table_widget.setEditTriggers(
            QAbstractItemView.NoEditTriggers)
        self.ccs_table_widget.setSelectionBehavior(
            QAbstractItemView.SelectRows)
        self.ccs_table_widget.resizeColumnsToContents()
        self.ccs_vlayout.addWidget(self.ccs_table_widget)
        self.notes_hlayout.addWidget(self.ccs_groupbox)

        self.cc_vlayout.addWidget(CC_EDITOR_WIDGET.widget)

        self.pb_hlayout = QHBoxLayout()
        self.pitchbend_tab.setLayout(self.pb_hlayout)
        self.pb_groupbox = QGroupBox(_("Pitchbend"))
        self.pb_groupbox.setFixedWidth(240)
        self.pb_vlayout = QVBoxLayout(self.pb_groupbox)

        self.pitchbend_table_widget = QTableWidget()
        self.pitchbend_table_widget.setVerticalScrollMode(
            QAbstractItemView.ScrollPerPixel)
        self.pitchbend_table_widget.setColumnCount(2)
        self.pitchbend_table_widget.setSortingEnabled(True)
        self.pitchbend_table_widget.sortItems(0)
        self.pitchbend_table_widget.setEditTriggers(
            QAbstractItemView.NoEditTriggers)
        self.pitchbend_table_widget.setSelectionBehavior(
            QAbstractItemView.SelectRows)
        self.pitchbend_table_widget.resizeColumnsToContents()
        self.pb_vlayout.addWidget(self.pitchbend_table_widget)
        self.notes_hlayout.addWidget(self.pb_groupbox)
        self.pb_auto_vlayout = QVBoxLayout()
        self.pb_hlayout.addLayout(self.pb_auto_vlayout)
        self.pb_viewer_widget = AutomationEditorWidget(PB_EDITOR, False)
        self.pb_auto_vlayout.addWidget(self.pb_viewer_widget.widget)

        self.tab_widget.addTab(self.notes_tab, _("List Viewers"))

        self.zoom_widget = QWidget()
        #self.zoom_widget.setContentsMargins(0, 0, 2, 0)
        self.zoom_hlayout = QHBoxLayout(self.zoom_widget)
        self.zoom_hlayout.setContentsMargins(2, 0, 2, 0)
        #self.zoom_hlayout.setSpacing(0)

        self.snap_combobox = QComboBox()
        self.snap_combobox.setMinimumWidth(90)
        self.snap_combobox.addItems(
            [_("None"), "1/4", "1/8", "1/12", "1/16",
            "1/32", "1/64", "1/128"])
        self.zoom_hlayout.addWidget(QLabel(_("Snap:")))
        self.zoom_hlayout.addWidget(self.snap_combobox)
        self.snap_combobox.currentIndexChanged.connect(self.set_snap)

        self.item_name_lineedit = QLineEdit()
        self.item_name_lineedit.setReadOnly(True)
        self.item_name_lineedit.setMinimumWidth(150)
        self.zoom_hlayout.addWidget(self.item_name_lineedit)

        self.zoom_hlayout.addWidget(QLabel("H"))
        self.zoom_slider = QSlider(QtCore.Qt.Horizontal)
        self.zoom_hlayout.addWidget(self.zoom_slider)
        self.zoom_slider.setObjectName("zoom_slider")
        self.zoom_slider.setRange(10, 100)
        self.zoom_slider.valueChanged.connect(self.set_midi_zoom)
        self.tab_widget.setCornerWidget(self.zoom_widget)
        self.tab_widget.currentChanged.connect(self.tab_changed)

        self.set_headers()
        self.default_note_start = 0.0
        self.default_note_length = 1.0
        self.default_note_note = 0
        self.default_note_octave = 3
        self.default_note_velocity = 100
        self.default_cc_num = 0
        self.default_cc_start = 0.0
        self.default_cc_val = 0
        self.default_quantize = 5
        self.default_pb_start = 0
        self.default_pb_val = 0
        self.default_pb_quantize = 0

    def set_snap(self, a_val=None):
        f_index = self.snap_combobox.currentIndex()
        pydaw_set_piano_roll_quantize(f_index)
        pydaw_set_audio_snap(f_index)
        if CURRENT_ITEM:
            PIANO_ROLL_EDITOR.set_selected_strings()
            global_open_items()
            self.tab_changed()
        else:
            PIANO_ROLL_EDITOR.clear_drawn_items()

    def clear_new(self):
        self.enabled = False
        self.ccs_table_widget.clearContents()
        self.notes_table_widget.clearContents()
        self.pitchbend_table_widget.clearContents()
        PIANO_ROLL_EDITOR.clear_drawn_items()
        self.item = None

    def quantize_dialog(self, a_selected_only=False):
        if not self.enabled:
            self.show_not_enabled_warning()
            return

        def quantize_ok_handler():
            f_quantize_text = f_quantize_combobox.currentText()
            self.events_follow_default = f_events_follow_notes.isChecked()
            f_clip = CURRENT_ITEM.quantize(f_quantize_text,
                f_events_follow_notes.isChecked(),
                a_selected_only=f_selected_only.isChecked())
            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)

            if f_selected_only.isChecked():
                PIANO_ROLL_EDITOR.selected_note_strings = f_clip
            else:
                PIANO_ROLL_EDITOR.selected_note_strings = []

            global_open_items()
            PIANO_ROLL_EDITOR.draw_item()
            PROJECT.commit(_("Quantize item(s)"))
            f_window.close()

        def quantize_cancel_handler():
            f_window.close()

        f_window = QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Quantize"))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)

        f_layout.addWidget(QLabel(_("Quantize")), 0, 0)
        f_quantize_combobox = QComboBox()
        f_quantize_combobox.addItems(bar_fracs)
        f_layout.addWidget(f_quantize_combobox, 0, 1)
        f_events_follow_notes = QCheckBox(
            _("CCs and pitchbend follow notes?"))
        f_events_follow_notes.setChecked(self.events_follow_default)
        f_layout.addWidget(f_events_follow_notes, 1, 1)
        f_ok = QPushButton(_("OK"))
        f_ok.pressed.connect(quantize_ok_handler)
        f_ok_cancel_layout = QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok)

        f_selected_only = QCheckBox(_("Selected Notes Only?"))
        f_selected_only.setChecked(a_selected_only)
        f_layout.addWidget(f_selected_only, 2, 1)

        f_layout.addLayout(f_ok_cancel_layout, 3, 1)
        f_cancel = QPushButton(_("Cancel"))
        f_cancel.pressed.connect(quantize_cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec_()

    def transpose_dialog(self, a_selected_only=False):
        if not self.enabled:
            self.show_not_enabled_warning()
            return

        def transpose_ok_handler():
            f_clip = CURRENT_ITEM.transpose(
                f_semitone.value(), f_octave.value(),
                a_selected_only=f_selected_only.isChecked(),
                a_duplicate=f_duplicate_notes.isChecked())
            PROJECT.save_item(CURRENT_ITEM_NAME, CURRENT_ITEM)

            if f_selected_only.isChecked():
                PIANO_ROLL_EDITOR.selected_note_strings = f_clip
            else:
                PIANO_ROLL_EDITOR.selected_note_strings = []

            global_open_items()
            PIANO_ROLL_EDITOR.draw_item()
            PROJECT.commit(_("Transpose item(s)"))
            f_window.close()

        def transpose_cancel_handler():
            f_window.close()

        f_window = QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Transpose"))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)

        f_semitone = QSpinBox()
        f_semitone.setRange(-12, 12)
        f_layout.addWidget(QLabel(_("Semitones")), 0, 0)
        f_layout.addWidget(f_semitone, 0, 1)
        f_octave = QSpinBox()
        f_octave.setRange(-5, 5)
        f_layout.addWidget(QLabel(_("Octaves")), 1, 0)
        f_layout.addWidget(f_octave, 1, 1)
        f_duplicate_notes = QCheckBox(_("Duplicate notes?"))
        f_duplicate_notes.setToolTip(
            _("Checking this box causes the transposed notes "
            "to be added rather than moving the existing notes."))
        f_layout.addWidget(f_duplicate_notes, 2, 1)
        f_selected_only = QCheckBox(_("Selected Notes Only?"))
        f_selected_only.setChecked(a_selected_only)
        f_layout.addWidget(f_selected_only, 4, 1)
        f_ok_cancel_layout = QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout, 6, 1)
        f_ok = QPushButton(_("OK"))
        f_ok.pressed.connect(transpose_ok_handler)
        f_ok_cancel_layout.addWidget(f_ok)
        f_cancel = QPushButton(_("Cancel"))
        f_cancel.pressed.connect(transpose_cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec_()

    def tab_changed(self, a_val=None):
        f_list = [AUDIO_SEQ, PIANO_ROLL_EDITOR, CC_EDITOR, PB_EDITOR]
        f_index = self.tab_widget.currentIndex()
        if f_index == 0:
            global_open_audio_items()
        else:
            if f_index == 1:
                pydaw_set_piano_roll_quantize()
            elif f_index == 4:
                ITEM_EDITOR.open_item_list()
            if f_index < len(f_list):
                f_list[f_index].draw_item()
            PIANO_ROLL_EDITOR.click_enabled = True
            #^^^^huh?

    def show_not_enabled_warning(self):
        QMessageBox.warning(
            MAIN_WINDOW, _("Error"),
           _("You must open an item first by double-clicking on one in "
           "the region editor on the 'Song/Region' tab."))

    def set_midi_zoom(self, a_val):
        global_set_midi_zoom(a_val * 0.1)
        #global_open_items()
        AUDIO_SEQ.set_zoom(float(a_val) * 0.1)
        self.tab_changed()

    def set_headers(self): #Because clearing the table clears the headers
        self.notes_table_widget.setHorizontalHeaderLabels(
            [_('Start'), _('Length'), _('Note'), _('Note#'), _('Velocity')])
        self.ccs_table_widget.setHorizontalHeaderLabels(
            [_('Start'), _('Control'), _('Value')])
        self.pitchbend_table_widget.setHorizontalHeaderLabels(
            [_('Start'), _('Value')])

    def set_row_counts(self):
        if CURRENT_ITEM:
            self.notes_table_widget.setRowCount(len(CURRENT_ITEM.notes))
            self.ccs_table_widget.setRowCount(len(CURRENT_ITEM.ccs))
            self.pitchbend_table_widget.setRowCount(
                len(CURRENT_ITEM.pitchbends))
        else:
            self.notes_table_widget.setRowCount(0)
            self.ccs_table_widget.setRowCount(0)
            self.pitchbend_table_widget.setRowCount(0)

    def add_cc(self, a_cc):
        CURRENT_ITEM.add_cc(a_cc)

    def add_note(self, a_note):
        CURRENT_ITEM.add_note(a_note, False)

    def add_pb(self, a_pb):
        CURRENT_ITEM.add_pb(a_pb)

    def open_item_list(self):
        self.notes_table_widget.clear()
        self.ccs_table_widget.clear()
        self.pitchbend_table_widget.clear()
        self.set_headers()
        self.notes_table_widget.setSortingEnabled(False)
        self.set_row_counts()

        if not CURRENT_ITEM:
            return

        for note, f_i in zip(
        CURRENT_ITEM.notes, range(len(CURRENT_ITEM.notes))):
            f_note_str = note_num_to_string(note.note_num)
            self.notes_table_widget.setItem(
                f_i, 0, QTableWidgetItem(str(note.start)))
            self.notes_table_widget.setItem(
                f_i, 1, QTableWidgetItem(str(note.length)))
            self.notes_table_widget.setItem(
                f_i, 2, QTableWidgetItem(f_note_str))
            self.notes_table_widget.setItem(
                f_i, 3, QTableWidgetItem(str(note.note_num)))
            self.notes_table_widget.setItem(
                f_i, 4, QTableWidgetItem(str(note.velocity)))
        self.notes_table_widget.setSortingEnabled(True)
        self.ccs_table_widget.setSortingEnabled(False)

        for cc, f_i in zip(
        CURRENT_ITEM.ccs, range(len(CURRENT_ITEM.ccs))):
            self.ccs_table_widget.setItem(
                f_i, 0, QTableWidgetItem(str(cc.start)))
            self.ccs_table_widget.setItem(
                f_i, 1, QTableWidgetItem(str(cc.cc_num)))
            self.ccs_table_widget.setItem(
                f_i, 2, QTableWidgetItem(str(cc.cc_val)))
        self.ccs_table_widget.setSortingEnabled(True)
        self.pitchbend_table_widget.setSortingEnabled(False)

        for pb, f_i in zip(
        CURRENT_ITEM.pitchbends, range(len(CURRENT_ITEM.pitchbends))):
            self.pitchbend_table_widget.setItem(
                f_i, 0, QTableWidgetItem(str(pb.start)))
            self.pitchbend_table_widget.setItem(
                f_i, 1, QTableWidgetItem(str(pb.pb_val)))
        self.pitchbend_table_widget.setSortingEnabled(True)
        self.notes_table_widget.resizeColumnsToContents()
        self.ccs_table_widget.resizeColumnsToContents()
        self.pitchbend_table_widget.resizeColumnsToContents()


class MidiDevice:
    """ The controls for an individual MIDI hardware device, as
        configured in the hardware dialog
    """
    def __init__(self, a_name, a_index, a_layout, a_save_callback):
        self.suppress_updates = True
        self.name = str(a_name)
        self.index = int(a_index)
        self.save_callback = a_save_callback
        self.record_checkbox = QCheckBox()
        self.record_checkbox.toggled.connect(self.device_changed)
        f_index = int(a_index) + 1
        a_layout.addWidget(self.record_checkbox, f_index, 0)
        a_layout.addWidget(QLabel(a_name), f_index, 1)
        self.track_combobox = QComboBox()
        self.track_combobox.setMinimumWidth(180)
        self.track_combobox.addItems(TRACK_NAMES)
        TRACK_NAME_COMBOBOXES.append(self.track_combobox)
        self.track_combobox.currentIndexChanged.connect(self.device_changed)
        a_layout.addWidget(self.track_combobox, f_index, 2)
        self.suppress_updates = False

    def device_changed(self, a_val=None):
        if SUPPRESS_TRACK_COMBOBOX_CHANGES or self.suppress_updates:
            return
        track_index = self.track_combobox.currentIndex()
        PROJECT.IPC.pydaw_midi_device(
            self.record_checkbox.isChecked(), self.index,
            track_index)
        if track_index:  # not master
            TRACK_PANEL.tracks[track_index].check_output()
        self.save_callback()

    def get_routing(self):
        return pydaw_midi_route(
            1 if self.record_checkbox.isChecked() else 0,
            self.track_combobox.currentIndex(), self.name)

    def set_routing(self, a_routing):
        self.suppress_updates = True
        self.track_combobox.setCurrentIndex(a_routing.track_num)
        self.record_checkbox.setChecked(a_routing.on)
        self.suppress_updates = False

class MidiDevicesDialog:
    """ The container for all of the MidiDevice objects, located in
        the DAW-Next TransportWidget
    """
    def __init__(self):
        self.layout = QGridLayout()
        self.devices = []
        self.devices_dict = {}
        if not pydaw_util.MIDI_IN_DEVICES:
            return
        self.layout.addWidget(QLabel(_("On")), 0, 0)
        self.layout.addWidget(QLabel(_("MIDI Device")), 0, 1)
        self.layout.addWidget(QLabel(_("Output")), 0, 2)
        for f_name, f_i in zip(
        pydaw_util.MIDI_IN_DEVICES, range(len(pydaw_util.MIDI_IN_DEVICES))):
            f_device = MidiDevice(
                f_name, f_i, self.layout, self.save_callback)
            self.devices.append(f_device)
            self.devices_dict[f_name] = f_device

    def get_routings(self):
        return pydaw_midi_routings([x.get_routing() for x in self.devices])

    def save_callback(self):
        PROJECT.save_midi_routing(self.get_routings())

    def set_routings(self):
        f_routings = PROJECT.get_midi_routing()
        for f_routing in f_routings.routings:
            if f_routing.device_name in self.devices_dict:
                self.devices_dict[f_routing.device_name].set_routing(f_routing)


def global_open_mixer():
    """ Update the mixer to reflect the current routing and track names """
    f_graph = PROJECT.get_routing_graph()
    f_track_names = {
        f_i:x for f_i, x in zip(range(len(TRACK_NAMES)), TRACK_NAMES)}
    f_plugins = {}
    for k in f_track_names:
        f_track_plugins = PROJECT.get_track_plugins(k)
        if f_track_plugins:
            f_plugins[k] = {x.index:x for x in f_track_plugins.plugins}
    MIXER_WIDGET.update_sends(f_graph, f_plugins)
    MIXER_WIDGET.update_track_names(
        {f_i:x for f_i, x in zip(
        range(len(TRACK_NAMES)), TRACK_NAMES)})


class SeqTrack:
    """ The widget that contains the controls for an individual track
    """
    def __init__(self, a_track_num, a_track_text=_("track")):
        self.suppress_osc = True
        self.automation_uid = None
        self.automation_plugin = None
        self.track_number = a_track_num
        self.group_box = QWidget()
        self.group_box.contextMenuEvent = self.context_menu_event
        self.group_box.setObjectName("track_panel")
        self.main_hlayout = QHBoxLayout()
        self.main_hlayout.setContentsMargins(2, 2, 2, 2)
        self.main_vlayout = QVBoxLayout()
        self.main_hlayout.addLayout(self.main_vlayout)
        self.peak_meter = pydaw_widgets.peak_meter()
        if a_track_num in ALL_PEAK_METERS:
            ALL_PEAK_METERS[a_track_num].append(self.peak_meter)
        else:
            ALL_PEAK_METERS[a_track_num] = [self.peak_meter]
        self.main_hlayout.addWidget(self.peak_meter.widget)
        self.group_box.setLayout(self.main_hlayout)
        self.track_name_lineedit = QLineEdit()
        if a_track_num == 0:
            self.track_name_lineedit.setText("Master")
            self.track_name_lineedit.setDisabled(True)
        else:
            self.track_name_lineedit.setText(a_track_text)
            self.track_name_lineedit.setMaxLength(48)
            self.track_name_lineedit.editingFinished.connect(
                self.on_name_changed)
        self.main_vlayout.addWidget(self.track_name_lineedit)
        self.hlayout3 = QHBoxLayout()
        self.main_vlayout.addLayout(self.hlayout3)

        self.menu_button = QPushButton()
        self.menu_button.setFixedWidth(42)
        self.button_menu = QMenu()
        self.menu_button.setMenu(self.button_menu)
        self.hlayout3.addWidget(self.menu_button)
        self.button_menu.aboutToShow.connect(self.menu_button_pressed)
        self.menu_created = False
        self.solo_checkbox = QCheckBox()
        self.mute_checkbox = QCheckBox()
        if self.track_number == 0:
            self.hlayout3.addItem(
                QSpacerItem(1, 1, QSizePolicy.Expanding))
        else:
            self.solo_checkbox.stateChanged.connect(self.on_solo)
            self.solo_checkbox.setObjectName("solo_checkbox")
            self.hlayout3.addWidget(self.solo_checkbox)
            self.mute_checkbox.stateChanged.connect(self.on_mute)
            self.mute_checkbox.setObjectName("mute_checkbox")
            self.hlayout3.addWidget(self.mute_checkbox)
        self.action_widget = None
        self.automation_plugin_name = "None"
        self.port_num = None
        self.ccs_in_use_combobox = None
        self.suppress_osc = False
        self.automation_combobox = None

    def menu_button_pressed(self):
        if not self.menu_created:
            self.create_menu()

        self.suppress_ccs_in_use = True
        index = self.automation_combobox.currentIndex()
        plugins = PROJECT.get_track_plugins(self.track_number)
        if plugins:
            names = [PLUGIN_UIDS_REVERSE[x.plugin_index]
                for x in plugins.plugins]
        else:
            names = ["None" for x in range(10)]
        self.automation_combobox.clear()
        self.automation_combobox.addItems(names)
        self.automation_combobox.setCurrentIndex(index)
        self.suppress_ccs_in_use = False

        self.update_in_use_combobox()

    def open_plugins(self):
        PLUGIN_RACK.track_combobox.setCurrentIndex(self.track_number)
        MAIN_WINDOW.main_tabwidget.setCurrentIndex(TAB_PLUGIN_RACK)
        self.button_menu.close()

    def create_menu(self):
        if self.action_widget:
            self.button_menu.removeAction(self.action_widget)
        self.menu_created = True
        self.menu_widget = QWidget()
        self.menu_hlayout = QHBoxLayout(self.menu_widget)
        self.menu_gridlayout = QGridLayout()
        self.menu_hlayout.addLayout(self.menu_gridlayout)
        self.action_widget = QWidgetAction(self.button_menu)
        self.action_widget.setDefaultWidget(self.menu_widget)
        self.button_menu.addAction(self.action_widget)

        self.plugins_button = QPushButton(_("Plugins"))
        self.menu_gridlayout.addWidget(self.plugins_button, 0, 21)
        self.plugins_button.pressed.connect(self.open_plugins)

        self.automation_combobox = QComboBox()
        self.automation_combobox.setMinimumWidth(240)
        self.menu_gridlayout.addWidget(QLabel(_("Plugin:")), 5, 20)
        self.menu_gridlayout.addWidget(self.automation_combobox, 5, 21)
        self.automation_combobox.currentIndexChanged.connect(
            self.automation_callback)

        self.control_combobox = QComboBox()
        self.control_combobox.setMinimumWidth(240)
        self.menu_gridlayout.addWidget(QLabel(_("Automation:")), 9, 20)
        self.menu_gridlayout.addWidget(self.control_combobox, 9, 21)
        self.control_combobox.currentIndexChanged.connect(
            self.control_changed)
        self.ccs_in_use_combobox = QComboBox()
        self.ccs_in_use_combobox.setMinimumWidth(300)
        self.suppress_ccs_in_use = False
        self.ccs_in_use_combobox.currentIndexChanged.connect(
            self.ccs_in_use_combobox_changed)
        self.menu_gridlayout.addWidget(QLabel(_("In Use:")), 10, 20)
        self.menu_gridlayout.addWidget(self.ccs_in_use_combobox, 10, 21)

    def refresh(self):
        self.track_name_lineedit.setText(TRACK_NAMES[self.track_number])
        if self.menu_created:
            for f_plugin in self.plugins:
                f_plugin.remove_from_layout()
            self.create_menu()

    def plugin_changed(self, a_val=None):
        self.control_combobox.clear()
        if self.automation_plugin_name != "None":
            self.control_combobox.addItems(
                CC_NAMES[self.automation_plugin_name])
        TRACK_PANEL.update_plugin_track_map()

    def control_changed(self, a_val=None):
        self.set_cc_num()
        self.ccs_in_use_combobox.setCurrentIndex(0)
        if not libmk.IS_PLAYING:
            SEQUENCER.open_region()

    def set_cc_num(self, a_val=None):
        f_port_name = str(self.control_combobox.currentText())
        if f_port_name == "":
            self.port_num = None
        else:
            self.port_num = CONTROLLER_PORT_NAME_DICT[
                self.automation_plugin_name][f_port_name].port
        TRACK_PANEL.update_automation()

    def ccs_in_use_combobox_changed(self, a_val=None):
        if not self.suppress_ccs_in_use:
            f_str = str(self.ccs_in_use_combobox.currentText())
            if f_str:
                self.control_combobox.setCurrentIndex(
                    self.control_combobox.findText(f_str))

    def update_in_use_combobox(self):
        if self.ccs_in_use_combobox is not None:
            self.ccs_in_use_combobox.clear()
            if self.automation_uid is not None:
                f_list = ATM_REGION.get_ports(self.automation_uid)
                self.ccs_in_use_combobox.addItems(
                    [""] +
                    [CONTROLLER_PORT_NUM_DICT[
                        self.automation_plugin_name][x].name
                    for x in f_list])

    def on_solo(self, value):
        if not self.suppress_osc:
            PROJECT.IPC.pydaw_set_solo(
                self.track_number, self.solo_checkbox.isChecked())
            PROJECT.save_tracks(TRACK_PANEL.get_tracks())
            PROJECT.commit(_("Set solo for track {} to {}").format(
                self.track_number, self.solo_checkbox.isChecked()))

    def on_mute(self, value):
        if not self.suppress_osc:
            PROJECT.IPC.pydaw_set_mute(
                self.track_number, self.mute_checkbox.isChecked())
            PROJECT.save_tracks(TRACK_PANEL.get_tracks())
            PROJECT.commit(_("Set mute for track {} to {}").format(
                self.track_number, self.mute_checkbox.isChecked()))

    def on_name_changed(self):
        f_name = pydaw_remove_bad_chars(self.track_name_lineedit.text())
        self.track_name_lineedit.setText(f_name)
        global_update_track_comboboxes(self.track_number, f_name)
        f_tracks = PROJECT.get_tracks()
        f_tracks.tracks[self.track_number].name = f_name
        PROJECT.save_tracks(f_tracks)
        PROJECT.commit(
            _("Set name for track {} to {}").format(self.track_number,
            self.track_name_lineedit.text()))

    def context_menu_event(self, a_event=None):
        pass

    def automation_callback(self, a_val=None):
        if self.suppress_ccs_in_use:
            return
        plugins = PROJECT.get_track_plugins(self.track_number)
        index = self.automation_combobox.currentIndex()
        plugin = plugins.plugins[index]
        self.automation_uid = int(plugin.plugin_uid)
        self.automation_plugin = int(plugin.plugin_index)
        self.automation_plugin_name = PLUGIN_UIDS_REVERSE[
            self.automation_plugin]
        self.plugin_changed()
        if not libmk.IS_PLAYING:
            SEQUENCER.open_region()

    def save_callback(self):
        self.check_output()
        self.plugin_changed()

    def check_output(self):
        f_graph = PROJECT.get_routing_graph()
        if self.track_number != 0 and \
        f_graph.set_default_output(self.track_number):
            PROJECT.save_routing_graph(f_graph)
            PROJECT.commit(_("Set default output "
                "for track {}".format(self.track_number)))

    def name_callback(self):
        return str(self.track_name_lineedit.text())

    def open_track(self, a_track, a_notify_osc=False):
        if not a_notify_osc:
            self.suppress_osc = True
        if self.track_number != 0:
            self.track_name_lineedit.setText(a_track.name)
            self.solo_checkbox.setChecked(a_track.solo)
            self.mute_checkbox.setChecked(a_track.mute)
        self.suppress_osc = False

    def get_track(self):
        return pydaw_track(
            self.track_number, self.solo_checkbox.isChecked(),
            self.mute_checkbox.isChecked(),
            self.track_number, self.track_name_lineedit.text())


class AudioInput:
    def __init__(self, a_num, a_layout, a_callback, a_count):
        self.input_num = int(a_num)
        self.callback = a_callback
        a_layout.addWidget(QLabel(str(a_num)), a_num + 1, 21)
        self.name_lineedit = QLineEdit(str(a_num))
        self.name_lineedit.editingFinished.connect(self.name_update)
        a_num += 1
        a_layout.addWidget(self.name_lineedit, a_num, 0)
        self.rec_checkbox = QCheckBox("")
        self.rec_checkbox.clicked.connect(self.update_engine)
        a_layout.addWidget(self.rec_checkbox, a_num, 1)

        self.monitor_checkbox = QCheckBox(_(""))
        self.monitor_checkbox.clicked.connect(self.update_engine)
        a_layout.addWidget(self.monitor_checkbox, a_num, 2)

        self.vol_layout = QHBoxLayout()
        a_layout.addLayout(self.vol_layout, a_num, 3)
        self.vol_slider = QSlider(QtCore.Qt.Horizontal)
        self.vol_slider.setRange(-240, 240)
        self.vol_slider.setValue(0)
        self.vol_slider.setMinimumWidth(240)
        self.vol_slider.valueChanged.connect(self.vol_changed)
        self.vol_slider.sliderReleased.connect(self.update_engine)
        self.vol_layout.addWidget(self.vol_slider)
        self.vol_label = QLabel("0.0dB")
        self.vol_label.setMinimumWidth(64)
        self.vol_layout.addWidget(self.vol_label)
        self.stereo_combobox = QComboBox()
        a_layout.addWidget(self.stereo_combobox, a_num, 4)
        self.stereo_combobox.setMinimumWidth(75)
        self.stereo_combobox.addItems([_("None")] +
            [str(x) for x in range(a_count + 1)])
        self.stereo_combobox.currentIndexChanged.connect(self.update_engine)
        self.output_mode_combobox = QComboBox()
        self.output_mode_combobox.setMinimumWidth(100)
        self.output_mode_combobox.addItems(
            [_("Normal"), _("Sidechain"), _("Both")])
        a_layout.addWidget(self.output_mode_combobox, a_num, 5)
        self.output_mode_combobox.currentIndexChanged.connect(
            self.update_engine)
        self.output_track_combobox = QComboBox()
        self.output_track_combobox.setMinimumWidth(140)
        TRACK_NAME_COMBOBOXES.append(self.output_track_combobox)
        self.output_track_combobox.addItems(TRACK_NAMES)
        self.output_track_combobox.currentIndexChanged.connect(
            self.output_track_changed)
        a_layout.addWidget(self.output_track_combobox, a_num, 6)
        self.suppress_updates = False

    def output_track_changed(self, a_val=None):
        if not self.suppress_updates and not SUPPRESS_TRACK_COMBOBOX_CHANGES:
            f_track = self.output_track_combobox.currentIndex()
            if f_track in TRACK_PANEL.tracks:
                TRACK_PANEL.tracks[f_track].check_output()
                self.update_engine()
            else:
                print("{} not in TRACK_PANEL".format(f_track))

    def name_update(self, a_val=None):
        self.update_engine(a_notify=False)

    def update_engine(self, a_val=None, a_notify=True):
        if not self.suppress_updates:
            self.callback(a_notify)

    def vol_changed(self):
        f_vol = self.get_vol()
        self.vol_label.setText("{}dB".format(f_vol))
        if not self.suppress_updates:
            libmk.IPC.audio_input_volume(self.input_num, f_vol)

    def get_vol(self):
        return round(self.vol_slider.value() * 0.1, 1)

    def get_name(self):
        return str(self.name_lineedit.text())

    def get_value(self):
        f_on = 1 if self.rec_checkbox.isChecked() else 0
        f_vol = self.get_vol()
        f_monitor = 1 if self.monitor_checkbox.isChecked() else 0
        f_stereo = self.stereo_combobox.currentIndex() - 1
        f_mode = self.output_mode_combobox.currentIndex()
        f_output = self.output_track_combobox.currentIndex()
        f_name = self.name_lineedit.text()

        return libmk.mk_project.AudioInputTrack(
            f_on, f_monitor, f_vol, f_output, f_stereo, f_mode, f_name)

    def set_value(self, a_val):
        self.suppress_updates = True
        f_rec = True if a_val.rec else False
        f_monitor = True if a_val.monitor else False
        self.name_lineedit.setText(a_val.name)
        self.rec_checkbox.setChecked(f_rec)
        self.monitor_checkbox.setChecked(f_monitor)
        self.vol_slider.setValue(int(a_val.vol * 10.0))
        self.stereo_combobox.setCurrentIndex(a_val.stereo + 1)
        self.output_mode_combobox.setCurrentIndex(a_val.sidechain)
        self.output_track_combobox.setCurrentIndex(a_val.output)
        self.suppress_updates = False


class AudioInputWidget:
    def __init__(self):
        self.widget = QWidget()
        self.main_layout = QVBoxLayout(self.widget)
        self.layout = QGridLayout()
        self.main_layout.addWidget(QLabel(_("Audio Inputs")))
        self.main_layout.addLayout(self.layout)
        f_labels = (
            _("Name"), _("Rec."), _("Mon."), _("Gain"), _("Stereo"),
            _("Mode"), _("Output"))
        for f_i, f_label in zip(range(len(f_labels)), f_labels):
            self.layout.addWidget(QLabel(f_label), 0, f_i)
        self.inputs = []
        f_count = 0
        if "audioInputs" in pydaw_util.global_device_val_dict:
            f_count = int(pydaw_util.global_device_val_dict["audioInputs"])
        for f_i in range(f_count):
            f_input = AudioInput(f_i, self.layout, self.callback, f_count - 1)
            self.inputs.append(f_input)

    def get_inputs(self):
        f_result = libmk.mk_project.AudioInputTracks()
        for f_i, f_input in zip(range(len(self.inputs)), self.inputs):
            f_result.add_track(f_i, f_input.get_value())
        return f_result

    def callback(self, a_notify):
        f_result = self.get_inputs()
        PROJECT.save_audio_inputs(f_result)
        if a_notify:
            PROJECT.IPC.save_audio_inputs()

    def active(self):
        return [x.get_value() for x in self.inputs
            if x.rec_checkbox.isChecked()]

    def open_project(self):
        f_audio_inputs = PROJECT.get_audio_inputs()
        for k, v in f_audio_inputs.tracks.items():
            if k < len(self.inputs):
                self.inputs[k].set_value(v)


MREC_EVENTS = []

class TransportWidget(libmk.AbstractTransport):
    def __init__(self):
        self.recording_timestamp = None
        self.suppress_osc = True
        self.last_open_dir = global_home
        self.group_box = QGroupBox()
        self.group_box.setObjectName("transport_panel")
        self.vlayout = QVBoxLayout()
        self.group_box.setLayout(self.vlayout)
        self.hlayout1 = QHBoxLayout()
        self.vlayout.addLayout(self.hlayout1)
        self.playback_menu_button = QPushButton("")
        self.playback_menu_button.setMaximumWidth(21)
        self.playback_menu_button.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.hlayout1.addWidget(self.playback_menu_button)
        self.grid_layout1 = QGridLayout()
        self.hlayout1.addLayout(self.grid_layout1)

        self.playback_menu = QMenu(self.playback_menu_button)
        self.playback_menu_button.setMenu(self.playback_menu)
        self.playback_widget_action = QWidgetAction(self.playback_menu)
        self.playback_widget = QWidget()
        self.playback_widget_action.setDefaultWidget(self.playback_widget)
        self.playback_vlayout = QVBoxLayout(self.playback_widget)
        self.playback_menu.addAction(self.playback_widget_action)

        self.grid_layout1.addWidget(QLabel(_("Loop Mode:")), 0, 30)
        self.loop_mode_combobox = QComboBox()
        self.loop_mode_combobox.addItems([_("Off"), _("Region")])
        self.loop_mode_combobox.setMinimumWidth(90)
        self.loop_mode_combobox.currentIndexChanged.connect(
            self.on_loop_mode_changed)
        self.grid_layout1.addWidget(self.loop_mode_combobox, 1, 30)

        self.grid_layout1.addItem(
            QSpacerItem(1, 1, QSizePolicy.Expanding), 1, 60)

        self.overdub_checkbox = QCheckBox(_("Overdub"))
        self.overdub_checkbox.clicked.connect(self.on_overdub_changed)
        #self.playback_vlayout.addWidget(self.overdub_checkbox)
        self.playback_vlayout.addWidget(QLabel(_("MIDI Input Devices")))

        self.playback_vlayout.addLayout(MIDI_DEVICES_DIALOG.layout)
        self.active_devices = []

        self.audio_inputs = AudioInputWidget()
        self.playback_vlayout.addWidget(self.audio_inputs.widget)

        self.suppress_osc = False

    def open_project(self):
        self.audio_inputs.open_project()

    def on_panic(self):
        PROJECT.IPC.pydaw_panic()

    def set_time(self, a_beat):
        f_text = CURRENT_REGION.get_time_at_beat(a_beat)
        libmk.TRANSPORT.set_time(f_text)

    def set_pos_from_cursor(self, a_beat):
        if libmk.IS_PLAYING or libmk.IS_RECORDING:
            f_beat = float(a_beat)
            self.set_time(f_beat)

    def set_controls_enabled(self, a_enabled):
        for f_widget in (
        REGION_SETTINGS.snap_combobox, self.overdub_checkbox):
            f_widget.setEnabled(a_enabled)

    def on_play(self):
        if MAIN_WINDOW.main_tabwidget.currentIndex() == TAB_ITEM_EDITOR:
            SEQUENCER.open_region()
        REGION_SETTINGS.on_play()
        AUDIO_SEQ_WIDGET.on_play()
        SEQUENCER.start_playback()
        PROJECT.IPC.pydaw_en_playback(1, SEQUENCER.get_beat_value())
        self.set_controls_enabled(False)
        return True

    def on_stop(self):
        PROJECT.IPC.pydaw_en_playback(0)
        REGION_SETTINGS.on_stop()
        AUDIO_SEQ_WIDGET.on_stop()
        self.set_controls_enabled(True)
        self.loop_mode_combobox.setEnabled(True)
        self.playback_menu_button.setEnabled(True)

        if libmk.IS_RECORDING:
            f_restart_engine = False
            f_audio_count = len(self.audio_inputs.active())
            if f_audio_count:
                f_stop_time = datetime.datetime.now()
                f_delta = (f_stop_time -
                    self.recording_timestamp) * f_audio_count
                f_restart_engine = libmk.add_entropy(f_delta)
            if self.rec_end is None:
                self.rec_end = round(SEQUENCER.get_beat_value() + 0.5)
            self.show_save_items_dialog(a_restart=f_restart_engine)

        SEQUENCER.stop_playback()
        #REGION_SETTINGS.open_region()
        self.set_time(SEQUENCER.get_beat_value())

    def show_save_items_dialog(self, a_restart=False):
        f_inputs = self.audio_inputs.inputs
        def ok_handler():
            f_file_name = str(f_file.text())
            if f_file_name is None or f_file_name == "":
                QMessageBox.warning(
                    f_window, _("Error"),
                    _("You must select a name for the item"))
                return

            f_sample_count = CURRENT_REGION.get_sample_count(
                self.rec_start, self.rec_end, pydaw_util.SAMPLE_RATE)

            PROJECT.save_recorded_items(
                f_file_name, MREC_EVENTS, self.overdub_checkbox.isChecked(),
                pydaw_util.SAMPLE_RATE, self.rec_start, self.rec_end,
                f_inputs, f_sample_count, f_file_name)
            REGION_SETTINGS.open_region()
            if pydaw_util.IS_ENGINE_LIB:
                libmk.clean_wav_pool()
            elif a_restart:
                libmk.restart_engine()
            f_window.close()

        def text_edit_handler(a_val=None):
            f_file.setText(pydaw_remove_bad_chars(f_file.text()))

        f_window = QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Save Recorded Files"))
        f_window.setMinimumWidth(330)
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)
        f_layout.addWidget(QLabel(_("Save recorded items")), 0, 2)
        f_layout.addWidget(QLabel(_("Item Name:")), 3, 1)
        f_file = QLineEdit()
        f_file.setMaxLength(24)
        f_file.textEdited.connect(text_edit_handler)
        f_layout.addWidget(f_file, 3, 2)
        f_ok_button = QPushButton(_("Save"))
        f_ok_button.clicked.connect(ok_handler)
        f_cancel_button = QPushButton(_("Discard"))
        f_cancel_button.clicked.connect(f_window.close)
        f_ok_cancel_layout = QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_layout.addLayout(f_ok_cancel_layout, 8, 2)
        f_window.exec_()


    def on_rec(self):
        if self.loop_mode_combobox.currentIndex() == 1:
            QMessageBox.warning(
                self.group_box, _("Error"),
                _("Loop recording is not yet supported"))
            return False
        self.active_devices = [x for x in MIDI_DEVICES_DIALOG.devices
            if x.record_checkbox.isChecked()]
        if not self.active_devices and not self.audio_inputs.active():
            QMessageBox.warning(
                self.group_box, _("Error"),
                _("No MIDI or audio inputs record-armed"))
            return False
#        if self.overdub_checkbox.isChecked() and \
#        self.loop_mode_combobox.currentIndex() > 0:
#            QMessageBox.warning(
#                self.group_box, _("Error"),
#                _("Cannot use overdub mode with loop mode to record"))
#            return False
        REGION_SETTINGS.on_play()
        AUDIO_SEQ_WIDGET.on_play()
        SEQUENCER.start_playback()
        self.set_controls_enabled(False)
        self.loop_mode_combobox.setEnabled(False)
        self.playback_menu_button.setEnabled(False)
        global MREC_EVENTS
        MREC_EVENTS = []
        f_loop_pos = SEQUENCER.get_loop_pos(a_warn=False)
        if self.loop_mode_combobox.currentIndex() == 0 or not f_loop_pos:
            self.rec_start = SEQUENCER.get_beat_value()
            self.rec_end = None
        else:
            self.rec_start, self.rec_end = f_loop_pos
        self.recording_timestamp = datetime.datetime.now()
        PROJECT.IPC.pydaw_en_playback(2, self.rec_start)
        return True

    def on_loop_mode_changed(self, a_loop_mode):
        if not self.suppress_osc:
            PROJECT.IPC.pydaw_set_loop_mode(a_loop_mode)

    def toggle_loop_mode(self):
        f_index = self.loop_mode_combobox.currentIndex() + 1
        if f_index >= self.loop_mode_combobox.count():
            f_index = 0
        self.loop_mode_combobox.setCurrentIndex(f_index)

    def on_overdub_changed(self, a_val=None):
        PROJECT.IPC.pydaw_set_overdub_mode(
            self.overdub_checkbox.isChecked())

    def reset(self):
        self.loop_mode_combobox.setCurrentIndex(0)
        self.overdub_checkbox.setChecked(False)

    def set_tooltips(self, a_enabled):
        if a_enabled:
            self.overdub_checkbox.setToolTip(
                _("Checking this box causes recording to "
                "unlink existing items and append new events to the "
                "existing events"))
            self.loop_mode_combobox.setToolTip(
                _("Use this to toggle between normal playback "
                "and looping a region.\nYou can toggle between "
                "settings with CTRL+L"))
            self.group_box.setToolTip(libdawnext.strings.transport)
        else:
            self.overdub_checkbox.setToolTip("")
            self.loop_mode_combobox.setToolTip("")
            self.group_box.setToolTip("")


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

        self.loop_mode_action = QAction(self)
        self.addAction(self.loop_mode_action)
        self.loop_mode_action.setShortcut(
            QKeySequence.fromString("CTRL+L"))
        self.loop_mode_action.triggered.connect(TRANSPORT.toggle_loop_mode)

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

        self.song_region_vlayout.addWidget(REGION_SETTINGS.widget)

        self.midi_scroll_area = QScrollArea()
        self.midi_scroll_area.setWidgetResizable(True)
        self.midi_scroll_widget = QWidget()
        self.midi_scroll_widget.setContentsMargins(0, 0, 0, 0)
        self.midi_hlayout = QHBoxLayout(self.midi_scroll_widget)
        self.midi_hlayout.setContentsMargins(0, 0, 0, 0)
        self.midi_scroll_area.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn)
        self.midi_scroll_area.setWidget(self.midi_scroll_widget)
        self.midi_hlayout.addWidget(TRACK_PANEL.tracks_widget)
        self.midi_hlayout.addWidget(SEQUENCER)

        self.file_browser = FileDragDropper(pydaw_util.is_audio_midi_file)
        self.file_browser.set_multiselect(True)
        self.file_browser.hsplitter.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sequencer_vlayout.addWidget(self.file_browser.hsplitter)
        self.file_browser.hsplitter.insertWidget(0, self.midi_scroll_area)
        self.file_browser.hsplitter.setSizes([9999, 200])

        self.midi_scroll_area.scrollContentsBy = self.midi_scrollContentsBy
        self.vscrollbar = self.midi_scroll_area.verticalScrollBar()
        self.vscrollbar.sliderReleased.connect(self.vscrollbar_released)
        self.vscrollbar.setSingleStep(REGION_EDITOR_TRACK_HEIGHT)

        self.main_tabwidget.addTab(PLUGIN_RACK.widget, _("Plugin Rack"))
        self.main_tabwidget.addTab(ITEM_EDITOR.widget, _("Item Editor"))

        self.automation_tab = QWidget()
        self.automation_tab.setObjectName("plugin_ui")

        self.main_tabwidget.addTab(ROUTING_GRAPH_WIDGET, _("Routing"))
        self.main_tabwidget.addTab(MIXER_WIDGET.widget, _("Mixer"))

        self.notes_tab = QTextEdit(self)
        self.notes_tab.setAcceptRichText(False)
        self.notes_tab.leaveEvent = self.on_edit_notes
        self.main_tabwidget.addTab(self.notes_tab, _("Project Notes"))

        self.main_tabwidget.currentChanged.connect(self.tab_changed)

    def vscrollbar_released(self, a_val=None):
        f_val = round(self.vscrollbar.value() /
            REGION_EDITOR_TRACK_HEIGHT) * REGION_EDITOR_TRACK_HEIGHT
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
            f_dir = PROJECT.project_folder
            f_out_file = f_name.text()
            f_fini = os.path.join(f_out_file, "finished") if f_stem else None
            f_samp_rate = f_sample_rate.currentText()
            f_buff_size = pydaw_util.global_device_val_dict["bufferSize"]
            f_thread_count = 1 if pydaw_util.IS_WINDOWS else \
                pydaw_util.global_device_val_dict["threads"]

            self.last_offline_dir = os.path.dirname(str(f_name.text()))

            f_window.close()

            if pydaw_util.IS_LINUX and f_debug_checkbox.isChecked():
                f_cmd = "{} -e bash -c 'gdb {}-dbg'".format(
                    pydaw_util.TERMINAL, pydaw_util.RENDER_BIN_PATH)
                f_run_cmd = [str(x) for x in
                    ("run", "dawnext", "'{}'".format(f_dir),
                    "'{}'".format(f_out_file), f_start_beat, f_end_beat,
                    f_samp_rate, f_buff_size, f_thread_count, f_stem)]
                f_clipboard = QApplication.clipboard()
                f_clipboard.setText(" ".join(f_run_cmd))
                subprocess.Popen(f_cmd, shell=True)
            else:
                f_cmd = [str(x) for x in
                    (pydaw_util.RENDER_BIN_PATH, "dawnext",
                     f_dir, f_out_file, f_start_beat, f_end_beat,
                     f_samp_rate, f_buff_size, f_thread_count,
                     pydaw_util.USE_HUGEPAGES, f_stem)]
                libmk.MAIN_WINDOW.show_offline_rendering_wait_window_v2(
                    f_cmd, f_out_file, f_file_name=f_fini)
                if f_stem:
                    f_tracks = PROJECT.get_tracks()
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
                    self, _('Select an empty directory to render stems to'),
                    self.last_offline_dir, QFileDialog.ShowDirsOnly)
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
                    f_window, _("Select a file name to save to..."),
                    self.last_offline_dir)
                f_file_name = str(f_file_name)
                if f_file_name and str(f_file_name):
                    if not f_file_name.endswith(".wav"):
                        f_file_name += ".wav"
                    if f_file_name and str(f_file_name):
                        f_name.setText(f_file_name)
                    self.last_offline_dir = os.path.dirname(f_file_name)

        f_marker_pos = SEQUENCER.get_loop_pos(a_warn=False)

        if not f_marker_pos:
            QMessageBox.warning(
                MAIN_WINDOW, _("Error"),
                _("You must set the Loop/Export markers first by "
                "right-clicking on the sequencer timeline"))
            return

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
        f_sample_rate.addItems(["44100", "48000", "88200", "96000", "192000"])

        try:
            f_sr_index = f_sample_rate.findText(
                pydaw_util.global_device_val_dict["sampleRate"])
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

        if pydaw_util.IS_LINUX:
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
        if libmk.IS_PLAYING:
            return
        if PROJECT.undo():
            global_ui_refresh_callback()
        else:
            QMessageBox.warning(
                MAIN_WINDOW, "Error", "No more undo history left")

    def on_redo(self):
        if libmk.IS_PLAYING:
            return
        if PROJECT.redo():
            global_ui_refresh_callback()
        else:
            QMessageBox.warning(
                MAIN_WINDOW, "Error", "Already at the latest commit")

    def tab_changed(self):
        f_index = self.main_tabwidget.currentIndex()
        if f_index == TAB_SEQUENCER and not libmk.IS_PLAYING:
            SEQUENCER.open_region()
        elif f_index == TAB_ITEM_EDITOR:
            ITEM_EDITOR.tab_changed()
        elif f_index == TAB_ROUTING:
            ROUTING_GRAPH_WIDGET.draw_graph(
                PROJECT.get_routing_graph(), TRACK_NAMES)
        elif f_index == TAB_MIXER:
            global_open_mixer()

        PLUGIN_RACK.tab_selected(f_index == TAB_PLUGIN_RACK)

    def on_edit_notes(self, a_event=None):
        QTextEdit.leaveEvent(self.notes_tab, a_event)
        PROJECT.write_notes(self.notes_tab.toPlainText())

    def set_tooltips(self, a_on):
        if a_on:
            ROUTING_GRAPH_WIDGET.setToolTip(libpydaw.strings.routing_graph)
        else:
            ROUTING_GRAPH_WIDGET.setToolTip("")

    def midi_scrollContentsBy(self, x, y):
        QScrollArea.scrollContentsBy(self.midi_scroll_area, x, y)
        f_y = self.midi_scroll_area.verticalScrollBar().value()
        SEQUENCER.set_header_y_pos(f_y)

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
                if libmk.IS_PLAYING:
                    f_beat = float(a_val)
                    TRANSPORT.set_pos_from_cursor(f_beat)
                    for f_editor in (
                            SEQUENCER, AUDIO_SEQ, PIANO_ROLL_EDITOR,
                            PB_EDITOR, CC_EDITOR):
                        f_editor.set_playback_pos(f_beat)
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
                PIANO_ROLL_EDITOR.highlight_keys(f_state, f_note)
            elif a_key == "ml":
                libmk.PLUGIN_UI_DICT.midi_learn_control[0].update_cc_map(
                    a_val, libmk.PLUGIN_UI_DICT.midi_learn_control[1])
            elif a_key == "ready":
                print("Engine sent 'ready' signal to the UI")
        #This prevents multiple events from moving the same control,
        #only the last goes through
        for k, f_val in f_ui_dict.items():
            f_plugin_uid, f_name = k
            if int(f_plugin_uid) in libmk.PLUGIN_UI_DICT:
                libmk.PLUGIN_UI_DICT[int(f_plugin_uid)].ui_message(
                    f_name, f_val)
        for k, f_val in f_pc_dict.items():
            f_plugin_uid, f_port = (int(x) for x in k)
            if f_plugin_uid in libmk.PLUGIN_UI_DICT:
                libmk.PLUGIN_UI_DICT[f_plugin_uid].set_control_val(
                    f_port, float(f_val))
        for k, f_val in f_cc_dict.items():
            f_track_num, f_cc = (int(x) for x in k)
            if f_track_num in PLUGIN_RACK.plugin_racks:
                rack = PLUGIN_RACK.plugin_racks[f_track_num]
                for f_plugin_uid in rack.get_plugin_uids():
                    if f_plugin_uid in libmk.PLUGIN_UI_DICT:
                        libmk.PLUGIN_UI_DICT[
                            f_plugin_uid].set_cc_val(f_cc, f_val)

    def prepare_to_quit(self):
        try:
            for f_widget in (AUDIO_SEQ, PIANO_ROLL_EDITOR,
            CC_EDITOR, PB_EDITOR, SEQUENCER, ROUTING_GRAPH_WIDGET):
                f_widget.prepare_to_quit()
        except Exception as ex:
            print("Exception thrown while attempting to close DAW-Next")
            print("Exception:  {}".format(ex))


def global_update_peak_meters(a_val):
    for f_val in a_val.split("|"):
        f_list = f_val.split(":")
        f_index = int(f_list[0])
        if f_index in ALL_PEAK_METERS:
            for f_pkm in ALL_PEAK_METERS[f_index]:
                f_pkm.set_value(f_list[1:])
        else:
            print("{} not in ALL_PEAK_METERS".format(f_index))

def active_wav_pool_uids():
    return PROJECT.active_wav_pool_uids()

def global_close_all():
    global AUDIO_ITEMS_TO_DROP
    if libmk.PLUGIN_UI_DICT:
        libmk.PLUGIN_UI_DICT.close_all_plugin_windows()
    REGION_SETTINGS.clear_new()
    ITEM_EDITOR.clear_new()
    AUDIO_SEQ.clear_drawn_items()
    PB_EDITOR.clear_drawn_items()
    TRANSPORT.reset()
    AUDIO_ITEMS_TO_DROP = []

def global_ui_refresh_callback(a_restore_all=False):
    """ Use this to re-open all existing items/regions/song in
        their editors when the files have been changed externally
    """
    global_open_items(CURRENT_ITEM_NAME)
    TRACK_PANEL.open_tracks()
    REGION_SETTINGS.open_region()
    MAIN_WINDOW.tab_changed()
    PROJECT.IPC.pydaw_open_song(PROJECT.project_folder, a_restore_all)

#Opens or creates a new project
def global_open_project(a_project_file):
    global PROJECT, TRACK_NAMES
    PROJECT = DawNextProject(global_pydaw_with_audio)
    PROJECT.suppress_updates = True
    PROJECT.open_project(a_project_file, False)
    TRACK_PANEL.open_tracks()
    PROJECT.suppress_updates = False
    f_scale = PROJECT.get_midi_scale()
    if f_scale is not None:
        PIANO_ROLL_EDITOR_WIDGET.scale_key_combobox.setCurrentIndex(f_scale[0])
        PIANO_ROLL_EDITOR_WIDGET.scale_combobox.setCurrentIndex(f_scale[1])
    MAIN_WINDOW.last_offline_dir = libmk.PROJECT.user_folder
    MAIN_WINDOW.notes_tab.setText(PROJECT.get_notes())
    ROUTING_GRAPH_WIDGET.draw_graph(
        PROJECT.get_routing_graph(), TRACK_PANEL.get_track_names())
    global_open_mixer()
    MIDI_DEVICES_DIALOG.set_routings()
    REGION_SETTINGS.open_region()
    REGION_SETTINGS.snap_combobox.setCurrentIndex(1)
    TRANSPORT.open_project()
    PLUGIN_RACK.initialize(PROJECT)
    MIXER_WIDGET.set_project(PROJECT)

def global_new_project(a_project_file):
    global PROJECT
    PROJECT = DawNextProject(global_pydaw_with_audio)
    PROJECT.new_project(a_project_file)
    global_update_track_comboboxes()
    MAIN_WINDOW.last_offline_dir = libmk.PROJECT.user_folder
    MAIN_WINDOW.notes_tab.setText("")
    ROUTING_GRAPH_WIDGET.scene.clear()
    global_open_mixer()
    REGION_SETTINGS.open_region()
    REGION_SETTINGS.snap_combobox.setCurrentIndex(1)
    PLUGIN_RACK.initialize(PROJECT)
    MIXER_WIDGET.set_project(PROJECT)

PROJECT = DawNextProject(global_pydaw_with_audio)

TRACK_NAMES = ["Master" if x == 0 else "track{}".format(x)
    for x in range(TRACK_COUNT_ALL)]

SUPPRESS_TRACK_COMBOBOX_CHANGES = False
TRACK_NAME_COMBOBOXES = []

SEQUENCER = ItemSequencer()

PB_EDITOR = AutomationEditor(a_is_cc=False)
CC_EDITOR = AutomationEditor()
CC_EDITOR_WIDGET = AutomationEditorWidget(CC_EDITOR)

REGION_SETTINGS = RegionSettings()
TRACK_PANEL = TrackPanel()

PIANO_ROLL_EDITOR = PianoRollEditor()
PIANO_ROLL_EDITOR_WIDGET = PianoRollEditorWidget()
AUDIO_SEQ = AudioItemSeq()
AUDIO_SEQ_WIDGET = AudioItemSeqWidget()
ITEM_EDITOR = ItemListViewer()
MIXER_WIDGET = mkplugins.MixerWidget(TRACK_COUNT_ALL)

def get_mixer_peak_meters():
    for k, v in MIXER_WIDGET.tracks.items():
        ALL_PEAK_METERS[k].append(v.peak_meter)

get_mixer_peak_meters()

MIDI_EDITORS = (PIANO_ROLL_EDITOR, CC_EDITOR, PB_EDITOR)

MIDI_DEVICES_DIALOG = MidiDevicesDialog()
TRANSPORT = TransportWidget()

def routing_graph_toggle_callback(a_src, a_dest, a_sidechain):
    f_graph = PROJECT.get_routing_graph()
    f_result = f_graph.toggle(a_src, a_dest, a_sidechain)
    if f_result:
        QMessageBox.warning(MAIN_WINDOW, _("Error"), f_result)
    else:
        PROJECT.save_routing_graph(f_graph)
        ROUTING_GRAPH_WIDGET.draw_graph(f_graph, TRACK_NAMES)
        PROJECT.commit(_("Update routing"))

ROUTING_GRAPH_WIDGET = pydaw_widgets.RoutingGraphWidget(
    routing_graph_toggle_callback)

PLUGIN_RACK = PluginRackTab()

# Must call this after instantiating the other widgets,
# as it relies on them existing
MAIN_WINDOW = MainWindow()

PIANO_ROLL_EDITOR.verticalScrollBar().setSliderPosition(
    PIANO_ROLL_EDITOR.scene.height() * 0.4)

ITEM_EDITOR.snap_combobox.setCurrentIndex(4)

if libmk.TOOLTIPS_ENABLED:
    set_tooltips_enabled(libmk.TOOLTIPS_ENABLED)

CLOSE_ENGINE_ON_RENDER = True
