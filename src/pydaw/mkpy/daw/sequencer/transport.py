from .audio_input import AudioInputWidget
from mkpy import glbl
from mkpy.daw import shared
from mkpy.daw import strings as daw_strings
from mkpy.daw.project import *
from mkpy.daw.shared import *
from mkpy.libpydaw import pydaw_util
from mkpy.libpydaw.pydaw_util import *
from mkpy.libpydaw.translate import _
from mkpy.plugins import *
from mkpy.mkqt import *


MREC_EVENTS = []

class TransportWidget(glbl.AbstractTransport):
    def __init__(self):
        self.recording_timestamp = None
        self.suppress_osc = True
        self.last_open_dir = global_home
        self.group_box = QWidget()
        self.group_box.setObjectName("transport_panel")
        self.hlayout1 = QHBoxLayout(self.group_box)
        self.playback_menu_button = QPushButton("")
        self.playback_menu_button.setMaximumWidth(21)
        self.playback_menu_button.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.hlayout1.addWidget(self.playback_menu_button)
        self.vlayout = QVBoxLayout()
        self.hlayout1.addLayout(self.vlayout)

        self.hlayout2 = QHBoxLayout()
        self.vlayout.addLayout(self.hlayout2)

        self.playback_menu = QMenu(self.playback_menu_button)
        self.playback_menu_button.setMenu(self.playback_menu)
        self.playback_widget_action = QWidgetAction(self.playback_menu)
        self.playback_widget = QWidget()
        self.playback_widget_action.setDefaultWidget(self.playback_widget)
        self.playback_vlayout = QVBoxLayout(self.playback_widget)
        self.playback_menu.addAction(self.playback_widget_action)

        self.hlayout2.addWidget(QLabel(_("Loop Mode:")))
        self.loop_mode_combobox = QComboBox()
        self.loop_mode_combobox.addItems([_("Off"), _("Region")])
        self.loop_mode_combobox.setMinimumWidth(90)
        self.loop_mode_combobox.currentIndexChanged.connect(
            self.on_loop_mode_changed,
        )
        self.hlayout2.addWidget(self.loop_mode_combobox)

        self.hlayout3 = QHBoxLayout()
        self.vlayout.addLayout(self.hlayout3)
        self.hlayout3.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding))
        self.hlayout3.setContentsMargins(-3, 1, -3, 1)

        # Mouse tools
        self.tool_select_rb = QRadioButton()
        self.tool_select_rb.setObjectName("tool_select")
        self.tool_select_rb.setToolTip(_("Select (hotkey: a)"))
        self.hlayout3.addWidget(self.tool_select_rb)
        self.tool_select_rb.clicked.connect(self.tool_select_clicked)
        self.tool_select_rb.setChecked(True)

        self.tool_draw_rb = QRadioButton()
        self.tool_draw_rb.setObjectName("tool_draw")
        self.tool_draw_rb.setToolTip(_("Draw (hotkey: s)"))
        self.tool_draw_rb.clicked.connect(self.tool_draw_clicked)
        self.hlayout3.addWidget(self.tool_draw_rb)

        self.tool_erase_rb = QRadioButton()
        self.tool_erase_rb.setObjectName("tool_erase")
        self.tool_erase_rb.setToolTip(_("Erase (hotkey: d)"))
        self.tool_erase_rb.clicked.connect(self.tool_erase_clicked)
        self.hlayout3.addWidget(self.tool_erase_rb)

        self.tool_split_rb = QRadioButton()
        self.tool_split_rb.setObjectName("tool_split")
        self.tool_split_rb.setToolTip(_("Split (hotkey: f)"))
        self.tool_split_rb.clicked.connect(self.tool_split_clicked)
        self.hlayout3.addWidget(self.tool_split_rb)

        self.overdub_checkbox = QCheckBox(_("Overdub"))
        self.overdub_checkbox.clicked.connect(self.on_overdub_changed)
        #self.playback_vlayout.addWidget(self.overdub_checkbox)
        self.playback_vlayout.addWidget(QLabel(_("MIDI Input Devices")))

        self.playback_vlayout.addLayout(shared.MIDI_DEVICES_DIALOG.layout)
        self.active_devices = []

        self.audio_inputs = AudioInputWidget()
        self.playback_vlayout.addWidget(self.audio_inputs.widget)

        self.suppress_osc = False

    def tool_select_clicked(self, a_val=None):
        shared.EDITOR_MODE = shared.EDITOR_MODE_SELECT
        if not self.tool_select_rb.isChecked():
            self.tool_select_rb.setChecked(True)

    def tool_draw_clicked(self, a_val=None):
        shared.EDITOR_MODE = shared.EDITOR_MODE_DRAW
        if not self.tool_draw_rb.isChecked():
            self.tool_draw_rb.setChecked(True)

    def tool_erase_clicked(self, a_val=None):
        shared.EDITOR_MODE = shared.EDITOR_MODE_ERASE
        if not self.tool_erase_rb.isChecked():
            self.tool_erase_rb.setChecked(True)

    def tool_split_clicked(self, a_val=None):
        shared.EDITOR_MODE = shared.EDITOR_MODE_SPLIT
        if not self.tool_split_rb.isChecked():
            self.tool_split_rb.setChecked(True)

    def open_project(self):
        self.audio_inputs.open_project()

    def on_panic(self):
        shared.PROJECT.IPC.pydaw_panic()

    def set_time(self, a_beat):
        f_text = shared.CURRENT_REGION.get_time_at_beat(a_beat)
        glbl.TRANSPORT.set_time(f_text)

    def set_pos_from_cursor(self, a_beat):
        if glbl.IS_PLAYING or glbl.IS_RECORDING:
            f_beat = float(a_beat)
            self.set_time(f_beat)

    def set_controls_enabled(self, a_enabled):
        for f_widget in (
        shared.REGION_SETTINGS.snap_combobox, self.overdub_checkbox):
            f_widget.setEnabled(a_enabled)

    def on_play(self):
        if (
            shared.MAIN_WINDOW.main_tabwidget.currentIndex()
            ==
            shared.TAB_ITEM_EDITOR
        ):
            shared.SEQUENCER.open_region()
        shared.REGION_SETTINGS.on_play()
        shared.AUDIO_SEQ_WIDGET.on_play()
        shared.SEQUENCER.start_playback()
        shared.PROJECT.IPC.pydaw_en_playback(
            1,
            shared.SEQUENCER.get_beat_value(),
        )
        self.set_controls_enabled(False)
        return True

    def on_stop(self):
        shared.PROJECT.IPC.pydaw_en_playback(0)
        shared.REGION_SETTINGS.on_stop()
        shared.AUDIO_SEQ_WIDGET.on_stop()
        self.set_controls_enabled(True)
        self.loop_mode_combobox.setEnabled(True)
        self.playback_menu_button.setEnabled(True)

        if glbl.IS_RECORDING:
            f_restart_engine = False
            f_audio_count = len(self.audio_inputs.active())
            if f_audio_count:
                f_stop_time = datetime.datetime.now()
                f_delta = (f_stop_time -
                    self.recording_timestamp) * f_audio_count
                f_restart_engine = glbl.add_entropy(f_delta)
            if self.rec_end is None:
                self.rec_end = round(shared.SEQUENCER.get_beat_value() + 0.5)
            self.show_save_items_dialog(a_restart=f_restart_engine)

        shared.SEQUENCER.stop_playback()
        #shared.REGION_SETTINGS.open_region()
        self.set_time(shared.SEQUENCER.get_beat_value())

    def show_save_items_dialog(self, a_restart=False):
        f_inputs = self.audio_inputs.inputs
        def ok_handler():
            f_file_name = str(f_file.text())
            if f_file_name is None or f_file_name == "":
                QMessageBox.warning(
                    f_window, _("Error"),
                    _("You must select a name for the item"))
                return

            f_sample_count = shared.CURRENT_REGION.get_sample_count(
                self.rec_start, self.rec_end, pydaw_util.SAMPLE_RATE)

            shared.PROJECT.save_recorded_items(
                f_file_name, MREC_EVENTS, self.overdub_checkbox.isChecked(),
                pydaw_util.SAMPLE_RATE, self.rec_start, self.rec_end,
                f_inputs, f_sample_count, f_file_name)
            shared.REGION_SETTINGS.open_region()
            if pydaw_util.IS_ENGINE_LIB:
                glbl.clean_wav_pool()
            elif a_restart:
                glbl.restart_engine()
            f_window.close()

        def text_edit_handler(a_val=None):
            f_file.setText(pydaw_remove_bad_chars(f_file.text()))

        f_window = QDialog(shared.MAIN_WINDOW)
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
        self.active_devices = [x for x in shared.MIDI_DEVICES_DIALOG.devices
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
        shared.REGION_SETTINGS.on_play()
        shared.AUDIO_SEQ_WIDGET.on_play()
        shared.SEQUENCER.start_playback()
        self.set_controls_enabled(False)
        self.loop_mode_combobox.setEnabled(False)
        self.playback_menu_button.setEnabled(False)
        global MREC_EVENTS
        MREC_EVENTS = []
        f_loop_pos = shared.SEQUENCER.get_loop_pos(a_warn=False)
        if self.loop_mode_combobox.currentIndex() == 0 or not f_loop_pos:
            self.rec_start = shared.SEQUENCER.get_beat_value()
            self.rec_end = None
        else:
            self.rec_start, self.rec_end = f_loop_pos
        self.recording_timestamp = datetime.datetime.now()
        shared.PROJECT.IPC.pydaw_en_playback(2, self.rec_start)
        return True

    def on_loop_mode_changed(self, a_loop_mode):
        if not self.suppress_osc:
            shared.PROJECT.IPC.pydaw_set_loop_mode(a_loop_mode)

    def toggle_loop_mode(self):
        f_index = self.loop_mode_combobox.currentIndex() + 1
        if f_index >= self.loop_mode_combobox.count():
            f_index = 0
        self.loop_mode_combobox.setCurrentIndex(f_index)

    def on_overdub_changed(self, a_val=None):
        shared.PROJECT.IPC.pydaw_set_overdub_mode(
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
            self.group_box.setToolTip(daw_strings.transport)
        else:
            self.overdub_checkbox.setToolTip("")
            self.loop_mode_combobox.setToolTip("")
            self.group_box.setToolTip("")

