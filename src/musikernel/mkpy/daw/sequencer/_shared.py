from .  import _shared
from mkpy import glbl
from mkpy.daw import shared
from mkpy.daw.project import *
from mkpy.lib.translate import _
from mkpy.lib import util
from mkpy.mkqt import *


DRAW_SEQUENCER_GRAPHS = True
CACHED_SEQ_LEN = 32
LAST_ITEM_LENGTH = 4
REGION_EDITOR_MODE = 0

ATM_CLIPBOARD = []
REGION_CLIPBOARD = []

REGION_EDITOR_HEADER_ROW_HEIGHT = 18
REGION_EDITOR_HEADER_HEIGHT = REGION_EDITOR_HEADER_ROW_HEIGHT * 3

REGION_TRACK_WIDTH = 180  #Width of the tracks in px
REGION_EDITOR_TRACK_COUNT = 32

SEQUENCER_PX_PER_BEAT = 24
SEQUENCER_QUANTIZE_PX = SEQUENCER_PX_PER_BEAT
SEQUENCER_QUANTIZE_64TH = SEQUENCER_PX_PER_BEAT / 16.0
SEQ_QUANTIZE = True

ATM_POINT_DIAMETER = 10.0
ATM_POINT_RADIUS = ATM_POINT_DIAMETER * 0.5

#gets updated by the region editor to it's real value:
REGION_EDITOR_TOTAL_HEIGHT = (
    REGION_EDITOR_TRACK_COUNT
    *
    shared.REGION_EDITOR_TRACK_HEIGHT
)

SEQUENCER_SNAP_VAL = 3
SEQ_QUANTIZE_AMT = 1.0
SEQ_LINES_ENABLED = False
SEQ_SNAP_RANGE = 8

REGION_EDITOR_DELETE_MODE = False

def pydaw_set_seq_snap(a_val=None):
    global \
        SEQUENCER_SNAP_VAL, \
        SEQ_LINES_ENABLED, \
        SEQ_QUANTIZE_AMT, \
        SEQ_SNAP_RANGE
    if a_val is None:
        a_val = SEQUENCER_SNAP_VAL
    else:
        SEQUENCER_SNAP_VAL = a_val
    SEQ_SNAP_RANGE = 8
    f_divisor = shared.ITEM_SNAP_DIVISORS[a_val]
    if a_val > 0:
        SEQ_QUANTIZE = True
        SEQ_LINES_ENABLED = False
    else:
        SEQ_QUANTIZE = False
        SEQ_LINES_ENABLED = False
    SEQUENCER_QUANTIZE_PX = SEQUENCER_PX_PER_BEAT / f_divisor
    SEQUENCER_QUANTIZE_64TH = SEQUENCER_PX_PER_BEAT / 16.0
    SEQ_QUANTIZE_AMT = f_divisor

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
    if glbl.IS_PLAYING or not shared.SEQUENCER.current_coord:
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
        shared.SEQ_WIDGET.open_region()
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
                DawAtmPoint(
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
            shared.SEQ_WIDGET.open_region()
            glbl.clean_wav_pool()
    elif REGION_EDITOR_MODE == 1:
        for f_point in shared.SEQUENCER.get_selected_points():
            shared.ATM_REGION.remove_point(f_point.item)
        shared.SEQUENCER.automation_save_callback()

def init():
    global copy_action, delete_action
    copy_action = QAction(
        parent=shared.SEQUENCER,
        text=_("Copy"),
    )
    copy_action.triggered.connect(copy_selected)
    copy_action.setShortcut(QKeySequence.Copy)

    delete_action = QAction(text=_("Delete"))
    delete_action.triggered.connect(delete_selected)
    delete_action.setShortcut(QKeySequence.Delete)
