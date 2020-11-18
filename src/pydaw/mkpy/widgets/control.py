from . import _shared
from .knob import pydaw_pixmap_knob
from mkpy.libpydaw import pydaw_util
from mkpy.libpydaw.translate import _
from mkpy.mkqt import *
import collections
import math


LAST_TEMPO_COMBOBOX_INDEX = 2

class AbstractUiControl:
    def __init__(
        self,
        a_label,
        a_port_num,
        a_rel_callback,
        a_val_callback,
        a_val_conversion=_shared.KC_NONE,
        a_port_dict=None,
        a_preset_mgr=None,
        a_default_value=None,
    ):
        if a_label is None:
            self.name_label = None
        else:
            self.name_label = QLabel(str(a_label))
            self.name_label.setAlignment(QtCore.Qt.AlignCenter)
            self.name_label.setMinimumWidth(15)
        self.undo_history = collections.deque()
        self.value_set = 0
        self.port_num = int(a_port_num)
        self.val_callback = a_val_callback
        self.rel_callback = a_rel_callback
        self.suppress_changes = False
        self.val_conversion = a_val_conversion
        if a_port_dict is not None:
            a_port_dict[self.port_num] = self
        if a_preset_mgr is not None:
            a_preset_mgr.add_control(self)
        self.default_value = a_default_value
        self.ratio_callback = None
        self.midi_learn_callback = None

    def set_midi_learn(self, a_callback, a_get_cc_map):
        self.midi_learn_callback = a_callback
        self.get_cc_map = a_get_cc_map

    def reset_default_value(self):
        if self.default_value is not None:
            self.set_value(self.default_value, True)

    def set_value(self, a_val, a_changed=False):
        f_val = int(a_val)
        if self.value_set < 2:
            self.value_set += 1
            self.add_undo_history(f_val)
        if not a_changed:
            self.suppress_changes = True
        self.control.setValue(f_val)
        self.control_value_changed(f_val)
        self.suppress_changes = False

    def get_value(self):
        return self.control.value()

    def set_127_min_max(self, a_min, a_max):
        self.min_label_value_127 = a_min;
        self.max_label_value_127 = a_max;
        self.label_value_127_add_to = 0.0 - a_min;
        self.label_value_127_multiply_by = ((a_max - a_min) / 127.0);

    def add_undo_history(self, value):
        self.undo_history.append(value)
        if len(self.undo_history) > 10:
            self.undo_history.popleft()

    def control_released(self):
        value = self.control.value()
        self.add_undo_history(value)
        if self.rel_callback is not None:
            self.rel_callback(self.port_num, value)

    def value_conversion(self, a_value):
        """ Convert a control value to a human-readable string """
        f_value = float(a_value)
        f_dec_value = 0.0
        retval = None
        if self.val_conversion == _shared.KC_NONE:
            pass
        elif self.val_conversion in (
        _shared.KC_DECIMAL, _shared.KC_TIME_DECIMAL,_shared.KC_HZ_DECIMAL):
            retval = (str(round(f_value * .01, 2)))
        elif self.val_conversion in (_shared.KC_INTEGER, _shared.KC_INT_PITCH, _shared.KC_MILLISECOND):
            retval = str(int(f_value))
        elif self.val_conversion == _shared.KC_PITCH:
            f_val = int(pydaw_util.pydaw_pitch_to_hz(f_value))
            if f_val >= 1000:
                f_val = str(round(f_val * 0.001, 1)) + "k"
            retval = (str(f_val))
        elif self.val_conversion == _shared.KC_127_PITCH:
            f_val = (
                int(pydaw_util.pydaw_pitch_to_hz(
                (f_value * 0.818897638) + 20.0)))
            if f_val >= 1000:
                f_val = str(round(f_val * 0.001, 1)) + "k"
            retval = (str(f_val))
        elif self.val_conversion == _shared.KC_127_ZERO_TO_X:
            f_dec_value = (float(f_value) *
                self.label_value_127_multiply_by) - \
                self.label_value_127_add_to
            f_dec_value = ((int)(f_dec_value * 10.0)) * 0.1
            retval = (str(round(f_dec_value, 2)))
        elif self.val_conversion == _shared.KC_127_ZERO_TO_X_INT:
            f_dec_value = (float(f_value) *
                self.label_value_127_multiply_by) - \
                self.label_value_127_add_to
            retval = (str(int(f_dec_value)))
        elif self.val_conversion == _shared.KC_LOG_TIME:
            f_dec_value = float(f_value) * 0.01
            f_dec_value = f_dec_value * f_dec_value
            retval = (str(round(f_dec_value, 2)))
        elif self.val_conversion == _shared.KC_TENTH:
            retval = (str(round(f_value * .1, 1)))
        else:
            assert False, "Unknown self.val_conversion: {}".format(
                self.val_conversion)
        return retval

    def control_value_changed(self, a_value):
        if not self.suppress_changes:
            self.val_callback(self.port_num, self.control.value())

        if self.value_label is not None:
            self.value_label.setText(self.value_conversion(a_value))

    def add_to_grid_layout(
            self, a_layout, a_x, a_alignment=QtCore.Qt.AlignHCenter):
        if self.name_label is not None:
            if a_alignment:
                a_layout.addWidget(
                    self.name_label, 0, a_x, alignment=a_alignment)
            else:
                a_layout.addWidget(self.name_label, 0, a_x)
        if a_alignment:
            a_layout.addWidget(
                self.control, 1, a_x, alignment=a_alignment)
        else:
            a_layout.addWidget(self.control, 1, a_x)
        if self.value_label is not None:
            if a_alignment:
                a_layout.addWidget(
                    self.value_label, 2, a_x, alignment=a_alignment)
            else:
                a_layout.addWidget(self.value_label, 2, a_x)

    def set_value_dialog(self):
        def ok_handler(a_self=None, a_val=None):
            self.control.setValue(f_spinbox.value())
            f_dialog.close()
        f_dialog = QDialog(self.control)
        f_dialog.setWindowTitle(_("Set Value"))
        f_layout = QGridLayout(f_dialog)
        f_layout.addWidget(QLabel(_("Value:")), 3, 0)
        f_spinbox = QSpinBox()
        f_spinbox.setMinimum(self.control.minimum())
        f_spinbox.setMaximum(self.control.maximum())
        f_spinbox.setValue(self.control.value())
        f_layout.addWidget(f_spinbox, 3, 1)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_layout.addWidget(f_cancel_button, 6, 0)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_handler)
        f_layout.addWidget(f_ok_button, 6, 1)
        f_dialog.move(self.control.mapToGlobal(QtCore.QPoint(0.0, 0.0)))
        f_dialog.exec_()

    def tempo_sync_dialog(self):
        def sync_button_pressed(a_self=None):
            global LAST_TEMPO_COMBOBOX_INDEX
            f_frac = 1.0
            f_switch = (f_beat_frac_combobox.currentIndex())
            f_dict = {0 : 0.25, 1 : 0.33333, 2 : 0.5, 3 : 0.666666, 4 : 0.75,
                      5 : 1.0, 6 : 2.0, 7 : 4.0}
            f_frac = f_dict[f_switch]
            f_seconds_per_beat = 60 / (f_spinbox.value())
            if self.val_conversion == _shared.KC_TIME_DECIMAL:
                f_result = round(f_seconds_per_beat * f_frac * 100)
            elif self.val_conversion == _shared.KC_HZ_DECIMAL:
                f_result = round((1.0 / (f_seconds_per_beat * f_frac)) * 100)
            elif self.val_conversion == _shared.KC_LOG_TIME:
                f_result = round(math.sqrt(f_seconds_per_beat * f_frac) * 100)
            elif self.val_conversion == _shared.KC_MILLISECOND:
                f_result = round(f_seconds_per_beat * f_frac * 1000)
            f_result = pydaw_util.pydaw_clip_value(
                f_result, self.control.minimum(), self.control.maximum())
            self.control.setValue(f_result)
            LAST_TEMPO_COMBOBOX_INDEX = f_beat_frac_combobox.currentIndex()
            f_dialog.close()
        f_dialog = QDialog(self.control)
        f_dialog.setWindowTitle(_("Tempo Sync"))
        f_groupbox_layout = QGridLayout(f_dialog)
        f_spinbox = QDoubleSpinBox()
        f_spinbox.setDecimals(1)
        f_spinbox.setRange(60, 200)
        f_spinbox.setSingleStep(0.1)
        f_spinbox.setValue(_shared.TEMPO)
        f_beat_fracs = ["1/16", "1/12", "1/8", "2/12", "3/16",
                        "1/4", "2/4", "4/4"]
        f_beat_frac_combobox = QComboBox()
        f_beat_frac_combobox.setMinimumWidth(75)
        f_beat_frac_combobox.addItems(f_beat_fracs)
        f_beat_frac_combobox.setCurrentIndex(LAST_TEMPO_COMBOBOX_INDEX)
        f_sync_button = QPushButton(_("Sync"))
        f_sync_button.pressed.connect(sync_button_pressed)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_groupbox_layout.addWidget(QLabel(_("BPM")), 0, 0)
        f_groupbox_layout.addWidget(f_spinbox, 1, 0)
        f_groupbox_layout.addWidget(QLabel("Length"), 0, 1)
        f_groupbox_layout.addWidget(f_beat_frac_combobox, 1, 1)
        f_groupbox_layout.addWidget(f_cancel_button, 2, 0)
        f_groupbox_layout.addWidget(f_sync_button, 2, 1)
        f_dialog.move(self.control.mapToGlobal(QtCore.QPoint(0.0, 0.0)))
        f_dialog.exec_()

    def set_note_dialog(self):
        def ok_button_pressed():
            f_value = f_note_selector.get_value()
            f_value = pydaw_util.pydaw_clip_value(
                f_value, self.control.minimum(), self.control.maximum())
            self.set_value(f_value)
            f_dialog.close()
        f_dialog = QDialog(self.control)
        f_dialog.setMinimumWidth(210)
        f_dialog.setWindowTitle(_("Set to Note"))
        f_vlayout = QVBoxLayout(f_dialog)
        f_note_selector = pydaw_note_selector_widget(0, None, None)
        f_note_selector.set_value(self.get_value())
        f_vlayout.addWidget(f_note_selector.widget)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_button_pressed)
        f_cancel_button = QPushButton(_("Cancel"))
        f_ok_cancel_layout = QHBoxLayout()
        f_cancel_button.pressed.connect(f_dialog.close)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_vlayout.addLayout(f_ok_cancel_layout)
        f_dialog.move(self.control.mapToGlobal(QtCore.QPoint(0.0, 0.0)))
        f_dialog.exec_()

    def set_ratio_dialog(self):
        def ok_button_pressed():
            f_value = pydaw_util.pydaw_ratio_to_pitch(f_ratio_spinbox.value())
            if self.ratio_callback:
                f_int = round(f_value)
                self.set_value(f_int, True)
                f_frac = round((f_value - f_int) * 100)
                self.ratio_callback(f_frac, True)
            else:
                self.set_value(f_value, True)
            f_dialog.close()
        f_dialog = QDialog(self.control)
        f_dialog.setMinimumWidth(210)
        f_dialog.setWindowTitle(_("Set to Ratio"))
        f_layout = QGridLayout(f_dialog)
        f_layout.addWidget(QLabel(_("Ratio:")), 0, 0)
        f_ratio_spinbox = QDoubleSpinBox()

        f_min = pydaw_util.pydaw_pitch_to_ratio(self.control.minimum())
        f_max = pydaw_util.pydaw_pitch_to_ratio(self.control.maximum())
        f_ratio_spinbox.setRange(f_min, round(f_max))
        f_ratio_spinbox.setDecimals(4)
        f_ratio_spinbox.setValue(
            pydaw_util.pydaw_pitch_to_ratio(self.get_value()))
        f_layout.addWidget(f_ratio_spinbox, 0, 1)

        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_button_pressed)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_layout.addWidget(f_ok_button, 5, 0)
        f_layout.addWidget(f_cancel_button, 5, 1)
        f_dialog.move(self.control.mapToGlobal(QtCore.QPoint(0.0, 0.0)))
        f_dialog.exec_()

    def set_octave_dialog(self):
        def ok_button_pressed():
            f_value = f_spinbox.value() * 12
            self.set_value(f_value, True)
            f_dialog.close()
        f_dialog = QDialog(self.control)
        f_dialog.setMinimumWidth(210)
        f_dialog.setWindowTitle(_("Set to Octave"))
        f_layout = QGridLayout(f_dialog)
        f_layout.addWidget(QLabel(_("Octave:")), 0, 0)
        f_spinbox = QSpinBox()
        f_min = self.control.minimum() // 12
        f_max = self.control.maximum() // 12
        f_spinbox.setRange(f_min, f_max)
        f_spinbox.setValue(self.get_value() // 12)
        f_layout.addWidget(f_spinbox, 0, 1)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_button_pressed)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_layout.addWidget(f_ok_button, 5, 0)
        f_layout.addWidget(f_cancel_button, 5, 1)
        f_dialog.move(self.control.mapToGlobal(QtCore.QPoint(0.0, 0.0)))
        f_dialog.exec_()

    def copy_automation(self):
        global CC_CLIPBOARD
        f_value = ((self.get_value() - self.control.minimum()) /
                  (self.control.maximum() - self.control.minimum())) * 127.0
        CC_CLIPBOARD = pydaw_util.pydaw_clip_value(f_value, 0.0, 127.0)

    def paste_automation(self):
        f_frac = CC_CLIPBOARD / 127.0
        f_frac = pydaw_util.pydaw_clip_value(f_frac, 0.0, 1.0)
        f_min = self.control.minimum()
        f_max = self.control.maximum()
        f_value = round(((f_max - f_min) * f_frac) + f_min)
        self.set_value(f_value)

    def midi_learn(self):
        self.midi_learn_callback(self)

    def cc_menu_triggered(self, a_item):
        self.midi_learn_callback(self, a_item.cc_num)

    def cc_range_dialog(self, a_item):
        f_cc = a_item.cc_num

        def get_zero_to_one(a_val):
            a_val = float(a_val)
            f_min = float(self.control.minimum())
            f_max = float(self.control.maximum())
            f_range = f_max - f_min
            f_result = (a_val - f_min) / f_range
            return round(f_result, 6)

        def get_real_value(a_val):
            a_val = float(a_val)
            f_min = float(self.control.minimum())
            f_max = float(self.control.maximum())
            f_range = f_max - f_min
            f_result = (a_val * f_range) + f_min
            return int(round(f_result))

        def ok_hander():
            f_low = get_zero_to_one(f_low_spinbox.value())
            f_high = get_zero_to_one(f_high_spinbox.value())
            print((f_low, f_high))
            self.midi_learn_callback(self, f_cc, f_low, f_high)
            f_dialog.close()

        f_cc_map = self.get_cc_map()
        f_default_low, f_default_high = (get_real_value(x) for x in
            f_cc_map[f_cc].ports[self.port_num])

        f_dialog = QDialog(self.control)
        f_dialog.setWindowTitle(_("Set Range for CC"))
        f_layout = QVBoxLayout(f_dialog)
        f_spinbox_layout = QHBoxLayout()
        f_layout.addLayout(f_spinbox_layout)
        f_spinbox_layout.addWidget(QLabel(_("Low")))
        f_low_spinbox = QSpinBox()
        f_low_spinbox.setRange(self.control.minimum(), self.control.maximum())
        f_low_spinbox.setValue(f_default_low)
        f_spinbox_layout.addWidget(f_low_spinbox)
        f_spinbox_layout.addWidget(QLabel(_("High")))
        f_high_spinbox = QSpinBox()
        f_high_spinbox.setRange(self.control.minimum(), self.control.maximum())
        f_high_spinbox.setValue(f_default_high)
        f_spinbox_layout.addWidget(f_high_spinbox)
        f_ok_cancel_layout = QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_hander)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.move(self.control.mapToGlobal(QtCore.QPoint(0.0, 0.0)))
        f_dialog.exec_()

    def undo_action_callback(self, a_action):
        value = a_action.control_value
        self.set_value(value)
        self.add_undo_history(value)

    def contextMenuEvent(self, a_event):
        f_menu = QMenu(self.control)
        if self.undo_history:
            undo_menu = QMenu(_("Undo"))
            f_menu.addMenu(undo_menu)
            undo_menu.triggered.connect(self.undo_action_callback)
            for x in reversed(self.undo_history):
                value = self.value_conversion(x)
                if value:
                    action = undo_menu.addAction(self.value_conversion(x))
                    if action is not None: # Not sure why this happens
                        action.control_value = x

        if self.midi_learn_callback:
            f_ml_action = f_menu.addAction(_("MIDI Learn"))
            f_ml_action.triggered.connect(self.midi_learn)
            f_cc_menu = QMenu(_("CCs"))
            f_menu.addMenu(f_cc_menu)
            f_cc_menu.triggered.connect(self.cc_menu_triggered)
            f_cc_map = self.get_cc_map()
            if f_cc_map:
                f_range_menu = QMenu(_("Set Range for CC"))
                f_range_menu.triggered.connect(self.cc_range_dialog)
                f_menu.addMenu(f_range_menu)
            for f_i in range(1, 128):
                f_cc_action = f_cc_menu.addAction(str(f_i))
                f_cc_action.cc_num = f_i
                f_cc_action.setCheckable(True)
                if f_i in f_cc_map and f_cc_map[f_i].has_port(self.port_num):
                    f_cc_action.setChecked(True)
                    f_action = f_range_menu.addAction(str(f_i))
                    f_action.cc_num = f_i
            f_menu.addSeparator()
        f_reset_action = f_menu.addAction(_("Reset to Default Value"))
        f_reset_action.triggered.connect(self.reset_default_value)
        f_set_value_action = f_menu.addAction(_("Set Raw Controller Value..."))
        f_set_value_action.triggered.connect(self.set_value_dialog)
        f_menu.addSeparator()
        f_copy_automation_action = f_menu.addAction(_("Copy"))
        f_copy_automation_action.triggered.connect(self.copy_automation)
        if CC_CLIPBOARD:
            f_paste_automation_action = f_menu.addAction(_("Paste"))
            f_paste_automation_action.triggered.connect(self.paste_automation)
        f_menu.addSeparator()

        if self.val_conversion in (
        _shared.KC_TIME_DECIMAL, _shared.KC_HZ_DECIMAL, _shared.KC_LOG_TIME, _shared.KC_MILLISECOND):
            f_tempo_sync_action = f_menu.addAction(_("Tempo Sync..."))
            f_tempo_sync_action.triggered.connect(self.tempo_sync_dialog)
        if self.val_conversion == _shared.KC_PITCH:
            f_set_note_action = f_menu.addAction(_("Set to Note..."))
            f_set_note_action.triggered.connect(self.set_note_dialog)
        if self.val_conversion == _shared.KC_INT_PITCH:
            f_set_ratio_action = f_menu.addAction(_("Set to Ratio..."))
            f_set_ratio_action.triggered.connect(self.set_ratio_dialog)
            f_set_octave_action = f_menu.addAction(_("Set to Octave..."))
            f_set_octave_action.triggered.connect(self.set_octave_dialog)

        f_menu.exec_(QCursor.pos())


class pydaw_null_control:
    """ For controls with no visual representation,
        ie: controls that share a UI widget
        depending on selected index, so that they can participate
        normally in the data representation mechanisms
    """
    def __init__(self, a_port_num, a_rel_callback,
                 a_val_callback, a_default_val,
                 a_port_dict, a_preset_mgr=None):
        self.name_label = None
        self.value_label = None
        self.port_num = int(a_port_num)
        self.val_callback = a_val_callback
        self.rel_callback = a_rel_callback
        self.suppress_changes = False
        self.value = a_default_val
        a_port_dict[self.port_num] = self
        self.default_value = a_default_val
        self.control_callback = None
        if a_preset_mgr is not None:
            a_preset_mgr.add_control(self)

    def reset_default_value(self):
        if self.default_value is not None:
            self.set_value(self.default_value, True)

    def get_value(self):
        return self.value

    def set_value(self, a_val, a_changed=False):
        self.value = a_val
        if self.control_callback is not None:
            self.control_callback.set_value(self.value)
        if a_changed:
            self.control_value_changed(a_val)

    def set_control_callback(self, a_callback=None):
        self.control_callback = a_callback

    def control_released(self):
        if self.rel_callback is not None:
            self.rel_callback(self.port_num, self.value)

    def control_value_changed(self, a_value):
        self.val_callback(self.port_num, self.value)

    def set_midi_learn(self, a_ignored, a_ignored2):
        pass

class pydaw_knob_control(AbstractUiControl):
    def __init__(self, a_size, a_label, a_port_num,
                 a_rel_callback, a_val_callback,
                 a_min_val, a_max_val, a_default_val, a_val_conversion=_shared.KC_NONE,
                 a_port_dict=None, a_preset_mgr=None):
        AbstractUiControl.__init__(
            self, a_label, a_port_num, a_rel_callback,
            a_val_callback, a_val_conversion, a_port_dict, a_preset_mgr,
            a_default_val)
        self.control = pydaw_pixmap_knob(a_size, a_min_val, a_max_val)
        self.control.valueChanged.connect(self.control_value_changed)
        self.control.sliderReleased.connect(self.control_released)
        self.control.contextMenuEvent = self.contextMenuEvent
        self.value_label = QLabel("")
        self.value_label.setAlignment(QtCore.Qt.AlignCenter)
        self.value_label.setMinimumWidth(15)
        self.set_value(a_default_val)


class pydaw_slider_control(AbstractUiControl):
    def __init__(self, a_orientation, a_label, a_port_num, a_rel_callback,
                 a_val_callback, a_min_val, a_max_val,
                 a_default_val, a_val_conversion=_shared.KC_NONE, a_port_dict=None,
                 a_preset_mgr=None):
        AbstractUiControl.__init__(
            self, a_label, a_port_num, a_rel_callback, a_val_callback,
            a_val_conversion, a_port_dict, a_preset_mgr, a_default_val)
        self.control = QSlider(a_orientation)
        self.control.contextMenuEvent = self.contextMenuEvent
        self.control.setRange(a_min_val, a_max_val)
        self.control.valueChanged.connect(self.control_value_changed)
        self.control.sliderReleased.connect(self.control_released)
        self.value_label = QLabel("")
        self.value_label.setAlignment(QtCore.Qt.AlignCenter)
        self.value_label.setMinimumWidth(15)
        self.set_value(a_default_val)


class pydaw_spinbox_control(AbstractUiControl):
    def __init__(self, a_label, a_port_num, a_rel_callback,
                 a_val_callback, a_min_val, a_max_val,
                 a_default_val, a_val_conversion=_shared.KC_NONE,
                 a_port_dict=None, a_preset_mgr=None):
        AbstractUiControl.__init__(
            self, a_label, a_port_num, a_rel_callback,
            a_val_callback, a_val_conversion,
            a_port_dict, a_preset_mgr, a_default_val)
        self.control = QSpinBox()
        self.widget = self.control
        self.control.setRange(a_min_val, a_max_val)
        self.control.setKeyboardTracking(False)
        self.control.valueChanged.connect(self.control_value_changed)
        self.control.valueChanged.connect(self.control_released)
        self.value_label = None
        self.set_value(a_default_val)


class pydaw_doublespinbox_control(AbstractUiControl):
    def __init__(
        self,
        a_label,
        a_port_num,
        a_rel_callback,
        a_val_callback,
        a_min_val,
        a_max_val,
        a_default_val,
        a_val_conversion=_shared.KC_NONE,
        a_port_dict=None,
        a_preset_mgr=None,
    ):
        AbstractUiControl.__init__(
            self, a_label, a_port_num, a_rel_callback,
            a_val_callback, a_val_conversion,
            a_port_dict, a_preset_mgr, a_default_val)
        self.control = QDoubleSpinBox()
        self.widget = self.control
        self.control.setRange(a_min_val, a_max_val)
        self.control.setKeyboardTracking(False)
        self.control.valueChanged.connect(self.control_value_changed)
        self.control.valueChanged.connect(self.control_released)
        self.value_label = None
        self.set_value(a_default_val)


class pydaw_checkbox_control(AbstractUiControl):
    def __init__(self, a_label, a_port_num, a_rel_callback, a_val_callback,
                 a_port_dict=None, a_preset_mgr=None, a_default=0):
        AbstractUiControl.__init__(
            self, None, a_port_num, a_rel_callback, a_val_callback,
            a_port_dict=a_port_dict, a_preset_mgr=a_preset_mgr,
            a_default_value=a_default)
        self.control = QCheckBox(a_label)
        if a_default:
            self.control.setChecked(True)
        self.widget = self.control
        self.control.stateChanged.connect(self.control_value_changed)
        #self.control.stateChanged.connect(self.control_released)
        self.value_label = None
        self.suppress_changes = False

    def control_value_changed(self, a_val=None):
        if not self.suppress_changes:
            self.val_callback(self.port_num, self.get_value())

    def control_released(self):
        if self.rel_callback is not None:
            self.rel_callback(self.port_num, self.get_value())

    def set_value(self, a_val, a_changed=False):
        self.suppress_changes = True
        f_val = int(a_val)
        if f_val == 0:
            self.control.setChecked(False)
        else:
            self.control.setChecked(True)
        self.suppress_changes = False
        if a_changed:
            self.control_value_changed()

    def get_value(self):
        if self.control.isChecked():
            return 1
        else:
            return 0


class pydaw_combobox_control(AbstractUiControl):
    def __init__(self, a_size, a_label, a_port_num,
                 a_rel_callback, a_val_callback,
                 a_items_list=[], a_port_dict=None, a_default_index=None,
                 a_preset_mgr=None):
        self.suppress_changes = True
        self.name_label = QLabel(str(a_label))
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.control = QComboBox()
        self.control.wheelEvent = self.wheel_event
        self.widget = self.control
        self.control.setMinimumWidth(a_size)
        self.control.addItems(a_items_list)
        self.control.setCurrentIndex(0)
        self.control.currentIndexChanged.connect(self.control_value_changed)
        self.port_num = int(a_port_num)
        self.rel_callback = a_rel_callback
        self.val_callback = a_val_callback
        self.suppress_changes = False
        if a_port_dict is not None:
            a_port_dict[self.port_num] = self
        self.value_label = None
        self.default_value = a_default_index
        if a_default_index is not None:
            self.set_value(a_default_index)
        if a_preset_mgr is not None:
            a_preset_mgr.add_control(self)

    def wheel_event(self, a_event=None):
        pass

    def control_value_changed(self, a_val):
        if not self.suppress_changes:
            self.val_callback(self.port_num, a_val)
            if self.rel_callback is not None:
                self.rel_callback(self.port_num, a_val)

    def set_value(self, a_val, a_changed=False):
        if not a_changed:
            self.suppress_changes = True
        self.control.setCurrentIndex(int(a_val))
        self.suppress_changes = False

    def get_value(self):
        return self.control.currentIndex()


