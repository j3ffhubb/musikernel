from .  import _shared
from mkpy import libmk
from mkpy.libdawnext import shared
from mkpy.libdawnext.project import *
from mkpy.libpydaw import (
    pydaw_util,
    pydaw_widgets,
)
from mkpy.mkqt import *

MENU = QMenu(shared.SEQUENCER)
track_atm_clipboard = []

def clear_plugin():
    if not shared.SEQUENCER.current_coord:
        return
    f_track = shared.SEQUENCER.current_coord[0]
    f_track_port_num, f_track_index = shared.TRACK_PANEL.has_automation(f_track)
    if f_track_port_num is None:
        QMessageBox.warning(
            shared.SEQUENCER,
            _("Error"),
            _("No automation selected for this track")
        )
        return
    f_index, f_plugin = shared.TRACK_PANEL.get_atm_params(f_track)
    shared.ATM_REGION.clear_plugins([f_index])
    shared.SEQUENCER.automation_save_callback()

def paste_atm_point():
    if libmk.IS_PLAYING:
        return
    shared.SEQUENCER.context_menu_enabled = False
    if pydaw_widgets.CC_CLIPBOARD is None:
        QMessageBox.warning(
            shared.SEQUENCER,
            _("Error"),
            _(
                "Nothing copied to the clipboard.\n"
                "Right-click->'Copy' on any knob on any plugin."
            ),
        )
        return
    f_track, f_beat, f_val = shared.SEQUENCER.current_coord
    f_beat = shared.SEQUENCER.quantize(f_beat)
    f_val = pydaw_widgets.CC_CLIPBOARD
    f_port, f_index = shared.TRACK_PANEL.has_automation(
        shared.SEQUENCER.current_coord[0],
    )
    if f_port is not None:
        f_point = pydaw_atm_point(
            f_beat,
            f_port,
            f_val,
            *shared.TRACK_PANEL.get_atm_params(f_track)
        )
        shared.ATM_REGION.add_point(f_point)
        shared.SEQUENCER.draw_point(f_point)
        shared.SEQUENCER.automation_save_callback()

def copy_track_region():
    if not shared.SEQUENCER.current_coord:
        return
    f_range = shared.SEQUENCER.get_loop_pos()
    if not f_range:
        return
    f_start, f_end = f_range
    f_track = shared.SEQUENCER.current_coord[0]
    f_plugins = shared.PROJECT.get_track_plugin_uids(f_track)
    if not f_plugins:
        return
    shared.SEQUENCER.track_atm_clipboard = \
        shared.ATM_REGION.copy_range_by_plugins(
            f_start,
            f_end,
            f_plugins,
        )
    shared.SEQUENCER.automation_save_callback()

def paste_track_region():
    if (
        not shared.SEQUENCER.current_coord
        or
        not shared.SEQUENCER.track_atm_clipboard
    ):
        return
    f_beat = shared.SEQUENCER.quantize(
        shared.SEQUENCER.current_coord[1],
    )
    for f_point in (
        x.clone()
        for x in shared.SEQUENCER.track_atm_clipboard
    ):
        f_point.beat += f_beat
        shared.ATM_REGION.add_point(f_point)
    shared.SEQUENCER.automation_save_callback()

def clear_track_region():
    if not shared.SEQUENCER.current_coord:
        return
    f_range = shared.SEQUENCER.get_loop_pos()
    if not f_range:
        return
    f_start, f_end = f_range
    f_track, f_beat = shared.SEQUENCER.current_coord[:2]
    f_plugins = shared.PROJECT.get_track_plugin_uids(f_track)
    if not f_plugins:
        return
    shared.ATM_REGION.clear_range_by_plugins(f_start, f_end, f_plugins)
    shared.SEQUENCER.automation_save_callback()

def clear_track():
    if not shared.SEQUENCER.current_coord:
        return
    f_track = shared.SEQUENCER.current_coord[0]
    f_plugins = shared.PROJECT.get_track_plugin_uids(f_track)
    if not f_plugins:
        return
    shared.ATM_REGION.clear_plugins(f_plugins)
    shared.SEQUENCER.automation_save_callback()

# Not used
def clear_port():
    if not shared.SEQUENCER.current_coord:
        return
    f_track = shared.SEQUENCER.current_coord[0]
    (
        f_track_port_num,
        f_track_index,
    ) = shared.TRACK_PANEL.has_automation(f_track)

    if f_track_port_num is None:
        QMessageBox.warning(
            shared.SEQUENCER,
            _("Error"),
            _("No automation selected for this track"),
        )
        return
    f_index, f_plugin = shared.TRACK_PANEL.get_atm_params(f_track)
    shared.ATM_REGION.clear_port(f_index, f_track_port_num)
    shared.SEQUENCER.automation_save_callback()

def transform_atm_callback(a_add, a_mul):
    shared.SEQUENCER.setUpdatesEnabled(False)
    for f_point, f_val in zip(
        shared.SEQUENCER.atm_selected,
        shared.SEQUENCER.atm_selected_vals,
    ):
        f_val = (f_val * a_mul) + a_add
        f_val = pydaw_util.pydaw_clip_value(f_val, 0.0, 127.0, True)
        f_point.item.cc_val = f_val
        f_point.setPos(
            shared.SEQUENCER.get_pos_from_point(f_point.item),
        )
    shared.SEQUENCER.setUpdatesEnabled(True)
    shared.SEQUENCER.update()

def transform_atm():
    shared.SEQUENCER.atm_selected = sorted(
        shared.SEQUENCER.get_selected_points(),
    )
    if not shared.SEQUENCER.atm_selected:
        QMessageBox.warning(
            shared.SEQUENCER,
            _("Error"),
            _("No automation points selected"),
        )
        return
    f_start_beat = shared.SEQUENCER.atm_selected[0].item.beat
    shared.SEQUENCER.set_playback_pos(f_start_beat)
    f_scrollbar = shared.SEQUENCER.horizontalScrollBar()
    f_scrollbar.setValue(SEQUENCER_PX_PER_BEAT * f_start_beat)

    shared.SEQUENCER.atm_selected_vals = [
        x.item.cc_val
        for x in shared.SEQUENCER.atm_selected
    ]

    f_result = pydaw_widgets.add_mul_dialog(
        shared.SEQUENCER.transform_atm_callback,
        lambda: shared.SEQUENCER.automation_save_callback(a_open=False)
    )

    if not f_result:
        for f_point, f_val in zip(
            shared.SEQUENCER.atm_selected,
            shared.SEQUENCER.atm_selected_vals,
        ):
            f_point.item.cc_val = f_val
        shared.SEQUENCER.automation_save_callback()
    else:
        shared.SEQUENCER.open_region()

def lfo_atm_callback(
    a_phase,
    a_start_freq,
    a_start_amp,
    a_start_center,
    a_start_fade,
    a_end_fade,
    a_end_freq,
    a_end_amp,
    a_end_center,
):
    a_phase, a_start_freq, a_start_fade, a_end_freq, a_end_fade = (
        x * 0.01
        for x in (
            a_phase,
            a_start_freq,
            a_start_fade,
            a_end_freq,
            a_end_fade,
        )
    )

    a_phase *= math.pi
    f_start_beat, f_end_beat = shared.SEQUENCER.get_loop_pos()

    f_length_beats = f_end_beat - f_start_beat
    two_pi = 2.0 * math.pi
    f_start_radians_p64, f_end_radians_p64 = (
        (x * two_pi) / 8.0
        for x in (a_start_freq, a_end_freq)
    )
    f_length_beats_recip = 1.0 / f_length_beats

    shared.SEQUENCER.setUpdatesEnabled(False)

    for f_point in shared.SEQUENCER.atm_selected:
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
        f_point.setPos(shared.SEQUENCER.get_pos_from_point(f_point.item))

        a_phase += pydaw_util.linear_interpolate(
            f_start_radians_p64, f_end_radians_p64, f_pos)
        if a_phase >= two_pi:
            a_phase -= two_pi

    shared.SEQUENCER.setUpdatesEnabled(True)
    shared.SEQUENCER.update()

def lfo_atm():
    if not shared.SEQUENCER.current_coord:
        return
    f_range = shared.SEQUENCER.get_loop_pos()
    if not f_range:
        return
    f_start_beat, f_end_beat = f_range
    if f_end_beat - f_start_beat > 64:
        QMessageBox.warning(
            shared.SEQUENCER,
            _("Error"),
            _("LFO patterns are limited to 64 beats in length"),
        )
        return
    f_scrollbar = shared.SEQUENCER.horizontalScrollBar()
    f_scrollbar.setValue(SEQUENCER_PX_PER_BEAT * f_start_beat)
    shared.SEQUENCER.set_playback_pos(f_start_beat)
    f_step = 1.0 / 16.0
    f_track, f_beat, f_val = shared.SEQUENCER.current_coord
    f_index, f_plugin = shared.TRACK_PANEL.get_atm_params(f_track)
    if f_index is None:
        QMessageBox.warning(
            shared.SEQUENCER,
            _("Error"),
            _("Track has no automation selected"),
        )
        return

    f_port, f_atm_uid = shared.TRACK_PANEL.has_automation(f_track)
    f_old = shared.ATM_REGION.clear_range(
        f_index,
        f_port,
        f_start_beat,
        f_end_beat,
    )
    if f_old:
        shared.SEQUENCER.automation_save_callback()
    f_pos = f_start_beat
    shared.SEQUENCER.scene.clearSelection()
    shared.SEQUENCER.atm_selected = []

    for f_i in range(int((f_end_beat - f_start_beat) / f_step)):
        f_point = project.pydaw_atm_point(
            f_pos,
            f_port,
            64.0,
            f_index,
            f_plugin,
        )
        shared.ATM_REGION.add_point(f_point)
        f_item = shared.SEQUENCER.draw_point(f_point)
        shared.SEQUENCER.atm_selected.append(f_item)
        f_pos += f_step

    f_result = pydaw_widgets.lfo_dialog(
        shared.SEQUENCER.lfo_atm_callback,
        lambda : shared.SEQUENCER.automation_save_callback(a_open=False)
    )

    if not f_result:
        for f_point in shared.SEQUENCER.atm_selected:
            shared.ATM_REGION.remove_point(f_point.item)
        if f_old:
            for f_point in f_old:
                shared.ATM_REGION.add_point(f_point)
        shared.SEQUENCER.automation_save_callback()
    else:
        shared.SEQUENCER.open_region()

def break_atm(checked=False, new_val=1):
    if _shared.REGION_EDITOR_MODE != 1:
        return
    assert new_val in (0, 1), "Unexpected value '{}'".format(new_val)
    points = [
        x.item
        for x in shared.SEQUENCER.get_selected_points()
    ]
    if points:
        for point in points:
            point.break_after = new_val
        shared.SEQUENCER.automation_save_callback()

def unbreak_atm():
    break_atm(new_val=0)



MENU.addAction(_shared.copy_action)

paste_action = MENU.addAction(_("Paste"))
paste_action.triggered.connect(_shared.paste_clipboard)

paste_ctrl_action = MENU.addAction(_("Paste Plugin Control"))
paste_ctrl_action.triggered.connect(paste_atm_point)

track_atm_menu = MENU.addMenu(_("All Plugins for Track"))

copy_track_region_action = track_atm_menu.addAction(_("Copy Region"))
copy_track_region_action.triggered.connect(copy_track_region)
paste_track_region_action = track_atm_menu.addAction(_("Paste Region"))
paste_track_region_action.triggered.connect(paste_track_region)
track_atm_menu.addSeparator()
clear_track_region_action = track_atm_menu.addAction(_("Clear Region"))
clear_track_region_action.triggered.connect(clear_track_region)

atm_clear_menu = MENU.addMenu(_("Clear All"))

atm_clear_menu.addSeparator()
clear_plugin_action = atm_clear_menu.addAction(_("Current Plugin"))
clear_plugin_action.triggered.connect(clear_plugin)

atm_clear_menu.addSeparator()
clear_track_action = atm_clear_menu.addAction(_("Track"))
clear_track_action.triggered.connect(clear_track)

transform_atm_action = MENU.addAction(_("Transform..."))
transform_atm_action.triggered.connect(transform_atm)

lfo_atm_action = MENU.addAction(_("LFO Tool..."))
lfo_atm_action.triggered.connect(lfo_atm)

MENU.addSeparator()

break_atm_action = MENU.addAction(
    _("Break after selected automation point(s)"),
)
break_atm_action.triggered.connect(break_atm)
break_atm_action.setShortcut(QKeySequence.fromString("CTRL+B"))

unbreak_atm_action = MENU.addAction(
    _("Un-break after selected automation point(s)"))
unbreak_atm_action.triggered.connect(unbreak_atm)
unbreak_atm_action.setShortcut(
    QKeySequence.fromString("CTRL+SHIFT+B"),
)
MENU.addSeparator()
MENU.addAction(_shared.delete_action)
