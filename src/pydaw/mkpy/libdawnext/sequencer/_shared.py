from .  import _shared
from mkpy import libmk
from mkpy.libdawnext import shared
from mkpy.libdawnext.project import *
from mkpy.libpydaw.translate import _
from mkpy.libpydaw import (
    pydaw_util,
    pydaw_widgets,
)
from mkpy.mkqt import *


REGION_EDITOR_MODE = 0

ATM_CLIPBOARD = []
REGION_CLIPBOARD = []

def copy_selected():
    if not shared.SEQUENCER.enabled:
        shared.SEQUENCER.warn_no_region_selected()
        return
    if REGION_EDITOR_MODE == 0:
        global REGION_CLIPBOARD
        REGION_CLIPBOARD = [x.audio_item.clone() for x in
            shared.SEQUENCER.get_selected_items()]
        if REGION_CLIPBOARD:
            REGION_CLIPBOARD.sort()
            f_start = int(REGION_CLIPBOARD[0].start_beat)
            for f_item in REGION_CLIPBOARD:
                f_item.start_beat -= f_start
    elif REGION_EDITOR_MODE == 1:
        global ATM_CLIPBOARD
        ATM_CLIPBOARD = [
            x.item.clone()
            for x in shared.SEQUENCER.get_selected_points(
                shared.SEQUENCER.current_coord[0]
            )
        ]
        if ATM_CLIPBOARD:
            ATM_CLIPBOARD.sort()
            f_start = int(ATM_CLIPBOARD[0].beat)
            for f_item in ATM_CLIPBOARD:
                f_item.beat -= f_start

def paste_clipboard():
    if libmk.IS_PLAYING or not shared.SEQUENCER.current_coord:
        return
    shared.SEQUENCER.scene.clearSelection()
    f_track, f_beat, f_val = shared.SEQUENCER.current_coord
    f_beat = int(f_beat)
    if REGION_EDITOR_MODE == 0:
        shared.SEQUENCER.selected_item_strings = set()
        for f_item in REGION_CLIPBOARD:
            f_new_item = f_item.clone()
            f_new_item.start_beat += f_beat
            shared.CURRENT_REGION.add_item_ref_by_uid(f_new_item)
            shared.SEQUENCER.selected_item_strings.add(str(f_new_item))
        shared.PROJECT.save_region(shared.CURRENT_REGION)
        shared.REGION_SETTINGS.open_region()
    elif REGION_EDITOR_MODE == 1:
        f_track_port_num, f_track_index = shared.TRACK_PANEL.has_automation(
            shared.SEQUENCER.current_coord[0])
        if f_track_port_num is None:
            QMessageBox.warning(
                shared.SEQUENCER, _("Error"),
                _("No automation selected for this track"))
            return
        f_track_params = shared.TRACK_PANEL.get_atm_params(f_track)
        f_end = ATM_CLIPBOARD[-1].beat + f_beat
        f_point = ATM_CLIPBOARD[0]
        shared.ATM_REGION.clear_range(
            f_point.index, f_point.port_num, f_beat, f_end)
        for f_point in ATM_CLIPBOARD:
            shared.ATM_REGION.add_point(
                pydaw_atm_point(
                    f_point.beat + f_beat, f_track_port_num,
                    f_point.cc_val, *f_track_params))
        shared.SEQUENCER.automation_save_callback()

def delete_selected():
    if shared.SEQUENCER.check_running():
        return
    if REGION_EDITOR_MODE == 0:
        f_item_list = shared.SEQUENCER.get_selected()
        shared.SEQUENCER.clear_selected_item_strings()
        if f_item_list:
            for f_item in f_item_list:
                shared.CURRENT_REGION.remove_item_ref(f_item.audio_item)
            shared.PROJECT.save_region(shared.CURRENT_REGION)
            shared.PROJECT.commit(_("Delete item(s)"))
            shared.REGION_SETTINGS.open_region()
            libmk.clean_wav_pool()
    elif REGION_EDITOR_MODE == 1:
        for f_point in shared.SEQUENCER.get_selected_points():
            shared.ATM_REGION.remove_point(f_point.item)
        shared.SEQUENCER.automation_save_callback()

copy_action = QAction(text=_("Copy"))
copy_action.triggered.connect(copy_selected)
copy_action.setShortcut(QKeySequence.Copy)

delete_action = QAction(text=_("Delete"))
delete_action.triggered.connect(delete_selected)
delete_action.setShortcut(QKeySequence.Delete)
