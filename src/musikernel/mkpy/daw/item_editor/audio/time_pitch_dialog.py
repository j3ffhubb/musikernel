from mkpy import glbl
from mkpy.daw import shared
from mkpy.daw.project import *
from mkpy.daw.shared import *
from mkpy.lib import util
from mkpy.lib.util import *
from mkpy.lib.translate import _
from mkpy.mkqt import *


class TimePitchDialogWidget:
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
        a_val = util.TIMESTRETCH_INDEXES[
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
        if glbl.IS_PLAYING:
            QMessageBox.warning(
                self.widget, _("Error"),
                _("Cannot edit audio items during playback"))
            return

        self.end_mode = 0

        f_selected_count = 0

        f_was_stretching = False
        f_stretched_items = []

        for f_item in shared.AUDIO_SEQ.audio_items:
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
                        glbl.PROJECT.timestretch_get_orig_file_uid(
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
                    f_ts_result = glbl.PROJECT.timestretch_audio_item(
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
                glbl.PROJECT.save_stretch_dicts()
                for f_stretch_item, f_audio_item in f_stretched_items:
                    f_stretch_item[2].wait()
                    glbl.PROJECT.get_wav_uid_by_name(
                        f_stretch_item[0], a_uid=f_stretch_item[1])
#                    f_new_uid = glbl.PROJECT.get_wav_uid_by_name(
#                        f_stretch_item[0], a_uid=f_stretch_item[1])
#                    f_graph = glbl.PROJECT.get_sample_graph_by_uid(f_new_uid)
#                    f_audio_item.clip_at_region_end(
#                        f_current_region_length, f_global_tempo,
#                        f_graph.length_in_seconds)
            shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
            global_open_audio_items(True)
            shared.PROJECT.commit(_("Update audio items"))
        self.widget.close()

