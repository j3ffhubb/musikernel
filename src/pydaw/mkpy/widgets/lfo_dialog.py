from . import _shared
from .control import pydaw_knob_control
from .playback_widget import pydaw_playback_widget
from mkpy.lib.translate import _
from mkpy.mkqt import *

def lfo_dialog(a_update_callback, a_save_callback):
    """ Generic dialog for doing event transforms that are LFO-like.
        The actual transforms are performed by the caller using the
        event callbacks.  The caller should create a list of event
        objects and their original values.
    """
    def ok_handler():
        f_dialog.close()
        f_dialog.retval = True

    def update(*args):
        f_vals = [x.control.value() for x in f_controls]
        f_vals += [
            x.control.value() if y.isChecked() else z.control.value()
            for x, y, z in f_optional_controls
        ]
        a_update_callback(*f_vals)

    def save(*args):
        a_save_callback()

    def update_and_save(a_val=None):
        update()
        save()

    f_dialog = QDialog()
    f_dialog.setWindowModality(QtCore.Qt.NonModal)
    f_dialog.setMinimumWidth(450)
    f_dialog.retval = False
    f_dialog.setWindowTitle(_("LFO Generator"))
    f_vlayout = QVBoxLayout(f_dialog)
    f_layout = QGridLayout()
    f_vlayout.addLayout(f_layout)

    f_knob_size = 48

    f_phase_knob = pydaw_knob_control(
        f_knob_size, _("Phase"), 0, save, update,
        0, 100, 0, _shared.KC_DECIMAL)
    f_phase_knob.add_to_grid_layout(f_layout, 0)

    f_start_freq_knob = pydaw_knob_control(
        f_knob_size, _("Start Freq"), 0, save, update,
        10, 400, 100, _shared.KC_DECIMAL)
    f_start_freq_knob.add_to_grid_layout(f_layout, 5)

    f_end_freq_knob = pydaw_knob_control(
        f_knob_size, _("End Freq"), 0, save, update,
        10, 400, 100, _shared.KC_DECIMAL)
    f_end_freq_knob.add_to_grid_layout(f_layout, 10)

    f_end_freq_cbox = QCheckBox()
    f_end_freq_cbox.stateChanged.connect(update_and_save)
    f_layout.addWidget(f_end_freq_cbox, 5, 10)

    f_start_amp_knob = pydaw_knob_control(
        f_knob_size, _("Start Amp"), 0, save, update,
        0, 127, 64, _shared.KC_INTEGER)
    f_start_amp_knob.add_to_grid_layout(f_layout, 11)

    f_end_amp_knob = pydaw_knob_control(
        f_knob_size, _("End Amp"), 0, save, update,
        0, 127, 64, _shared.KC_INTEGER)
    f_end_amp_knob.add_to_grid_layout(f_layout, 12)

    f_end_amp_cbox = QCheckBox()
    f_end_amp_cbox.stateChanged.connect(update_and_save)
    f_layout.addWidget(f_end_amp_cbox, 5, 12)

    f_start_center_knob = pydaw_knob_control(
        f_knob_size, _("Start Center"), 0, save, update,
        0, 127, 64, _shared.KC_INTEGER)
    f_start_center_knob.add_to_grid_layout(f_layout, 15)

    f_end_center_knob = pydaw_knob_control(
        f_knob_size, _("End Center"), 0, save, update,
        0, 127, 64, _shared.KC_INTEGER)
    f_end_center_knob.add_to_grid_layout(f_layout, 16)

    f_end_center_cbox = QCheckBox()
    f_end_center_cbox.stateChanged.connect(update_and_save)
    f_layout.addWidget(f_end_center_cbox, 5, 16)

    def start_fade_changed(*args):
        f_start, f_end = (x.control.value() for x in
            (f_start_fade_knob, f_end_fade_knob))
        if  f_start >= f_end:
            f_end_fade_knob.control.setValue(f_start + 1)
        else:
            update()

    f_start_fade_knob = pydaw_knob_control(
        f_knob_size, _("Start Fade"), 0, save, start_fade_changed,
        0, 99, 0, _shared.KC_INTEGER)
    f_start_fade_knob.add_to_grid_layout(f_layout, 20)

    def end_fade_changed(*args):
        f_start, f_end = (x.control.value() for x in
            (f_start_fade_knob, f_end_fade_knob))
        if f_end <= f_start:
            f_start_fade_knob.control.setValue(f_end - 1)
        else:
            update()

    f_end_fade_knob = pydaw_knob_control(
        f_knob_size, _("End Fade"), 0, save, end_fade_changed,
        1, 100, 100, _shared.KC_INTEGER)
    f_end_fade_knob.add_to_grid_layout(f_layout, 25)

    f_playback_widget = pydaw_playback_widget()
    f_layout.addWidget(f_playback_widget.play_button, 1, 30)
    f_layout.addWidget(f_playback_widget.stop_button, 1, 31)

    f_controls = (
        f_phase_knob, f_start_freq_knob, f_start_amp_knob,
        f_start_center_knob, f_start_fade_knob, f_end_fade_knob,
        )

    f_optional_controls = (
        (f_end_freq_knob, f_end_freq_cbox, f_start_freq_knob),
        (f_end_amp_knob, f_end_amp_cbox, f_start_amp_knob),
        (f_end_center_knob, f_end_center_cbox, f_start_center_knob),
        )

    f_ok_button = QPushButton(_("OK"))
    f_layout.addWidget(f_ok_button, 5, 30)
    f_ok_button.pressed.connect(ok_handler)
    f_cancel_button = QPushButton("Cancel")
    f_layout.addWidget(f_cancel_button, 5, 31)
    f_cancel_button.pressed.connect(f_dialog.close)
    update()
    save()
    f_dialog.move(0, 0)
    f_dialog.exec_()
    return f_dialog.retval

