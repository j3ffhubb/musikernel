"""

"""
from mkpy import glbl
from mkpy.daw.project import *
from mkpy.lib import util
from mkpy.lib.translate import _
from mkpy.mkqt import *


AUDIO_ITEMS_TO_DROP = []
MIDI_FILES_TO_DROP = []

AUDIO_LINES_ENABLED = True
AUDIO_SNAP_RANGE = 8
AUDIO_SNAP_VAL = 2
AUDIO_PX_PER_BEAT = 100.0

AUDIO_QUANTIZE = False
AUDIO_QUANTIZE_PX = 100.0
AUDIO_QUANTIZE_AMT = 1.0

AUDIO_RULER_HEIGHT = 20.0
AUDIO_ITEM_HEIGHT = 75.0

AUDIO_ITEM_MAX_LANE = 23
AUDIO_ITEM_LANE_COUNT = 24

AUDIO_ITEM_HANDLE_HEIGHT = 12.0
AUDIO_ITEM_HANDLE_SIZE = 6.25
AUDIO_ITEM_HANDLE_BRUSH = QLinearGradient(
    0.0,
    0.0,
    AUDIO_ITEM_HANDLE_SIZE,
    AUDIO_ITEM_HANDLE_HEIGHT,
)
AUDIO_ITEM_HANDLE_BRUSH.setColorAt(
    0.0,
    QColor.fromRgb(255, 255, 255, 120),
)
AUDIO_ITEM_HANDLE_BRUSH.setColorAt(
    0.0,
    QColor.fromRgb(255, 255, 255, 90),
)

AUDIO_ITEM_HANDLE_SELECTED_BRUSH = QLinearGradient(
    0.0,
    0.0,
    AUDIO_ITEM_HANDLE_SIZE,
    AUDIO_ITEM_HANDLE_HEIGHT,
)
AUDIO_ITEM_HANDLE_SELECTED_BRUSH.setColorAt(
    0.0,
    QColor.fromRgb(24, 24, 24, 120),
)
AUDIO_ITEM_HANDLE_SELECTED_BRUSH.setColorAt(
    0.0,
    QColor.fromRgb(24, 24, 24, 90),
)

AUDIO_ITEM_HANDLE_PEN = QPen(QtCore.Qt.white)
AUDIO_ITEM_LINE_PEN = QPen(QtCore.Qt.white, 2.0)
AUDIO_ITEM_HANDLE_SELECTED_PEN = QPen(QColor.fromRgb(24, 24, 24))
AUDIO_ITEM_LINE_SELECTED_PEN = QPen(
    QColor.fromRgb(24, 24, 24),
    2.0,
)

SEQUENCER_HEADER_BRUSH = QBrush(
    QColor(
        util.COLOR_PALETTE["SEQUENCER_HEADER_BRUSH"]
    )
)

ITEM_SNAP_DIVISORS = {
    0: 4.0,
    1: 1.0,
    2: 2.0,
    3: 3.0,
    4: 4.0,
    5: 8.0,
    6: 16.0,
    7: 32.0,
}

SELECTED_ITEM_COLOR = QBrush(QColor("#eeeeee"))
START_PEN = QPen(QColor.fromRgb(120, 120, 255), 6.0)
END_PEN = QPen(QColor.fromRgb(255, 60, 60), 6.0)

NO_PEN = QPen(QtCore.Qt.NoPen)
NO_PEN.setWidth(0)

CURRENT_REGION = None
CURRENT_REGION_NAME = None

TRACK_COLORS = None

DRAW_LAST_ITEMS = False

CURRENT_ITEM_NAME = None
LAST_ITEM_NAME = None
CURRENT_ITEM = None
CURRENT_ITEM_REF = None
LAST_ITEM = None
LAST_ITEM_REF = None
CURRENT_ITEM_LEN = 4

TAB_SEQUENCER = 0
TAB_PLUGIN_RACK = 1
TAB_ITEM_EDITOR = 2
TAB_ROUTING = 3
TAB_MIXER = 4
TAB_NOTES = 5

REGION_EDITOR_TRACK_HEIGHT = 64
PROJECT = DawProject(util.global_pydaw_with_audio)
TRACK_NAMES = [
    "Master" if x == 0 else "track{}".format(x)
    for x in range(TRACK_COUNT_ALL)
]

# Used by the transport tool selector radio buttons
EDITOR_MODE_SELECT = 0
EDITOR_MODE_DRAW = 1
EDITOR_MODE_ERASE = 2
EDITOR_MODE_SPLIT = 3
# The global variable that editors reference on mousePressEvent
EDITOR_MODE = EDITOR_MODE_SELECT

PLAYBACK_POS = 0.0
SUPPRESS_TRACK_COMBOBOX_CHANGES = False
TRACK_NAME_COMBOBOXES = []

CLOSE_ENGINE_ON_RENDER = True

ITEM_REF_POS = None
MIDI_SCALE = 1.0

ALL_PEAK_METERS = {}

LAST_NOTE_RESIZE = 0.25

PIANO_ROLL_SNAP = False
PIANO_ROLL_GRID_WIDTH = 1000.0
PIANO_KEYS_WIDTH = 34  #Width of the piano keys in px
PIANO_ROLL_GRID_MAX_START_TIME = 999.0 + PIANO_KEYS_WIDTH
PIANO_ROLL_NOTE_HEIGHT = util.get_file_setting("PIANO_VZOOM", int, 21)
PIANO_ROLL_SNAP_DIVISOR = 4.0
PIANO_ROLL_SNAP_BEATS = 1.0
PIANO_ROLL_SNAP_VALUE = PIANO_ROLL_GRID_WIDTH / PIANO_ROLL_SNAP_DIVISOR
PIANO_ROLL_NOTE_COUNT = 120
#gets updated by the piano roll to it's real value:
PIANO_ROLL_TOTAL_HEIGHT = 1000
PIANO_ROLL_QUANTIZE_INDEX = 4
PIANO_ROLL_MIN_NOTE_LENGTH = PIANO_ROLL_GRID_WIDTH / 128.0

# Placeholders for global access to UI comonents
ATM_REGION = None
AUTOMATION_EDITORS = []
SEQUENCER = None
PB_EDITOR = None
CC_EDITOR = None
CC_EDITOR_WIDGET = None
SEQ_WIDGET = None
TRACK_PANEL = None
PIANO_ROLL_EDITOR = None
PIANO_ROLL_EDITOR_WIDGET = None
AUDIO_SEQ = None
AUDIO_SEQ_WIDGET = None
ITEM_EDITOR = None
MIXER_WIDGET = None
MIDI_DEVICES_DIALOG = None
TRANSPORT = None
ROUTING_GRAPH_WIDGET = None
PLUGIN_RACK = None
MAIN_WINDOW = None

MIDI_EDITORS = None


def pydaw_get_current_region_length():
    return CURRENT_REGION.get_length() if CURRENT_REGION else 32

def global_update_hidden_rows(a_val=None):
    return # TODO
#    REGION_EDITOR.setUpdatesEnabled(False)
#    if CURRENT_REGION and SEQ_WIDGET.hide_inactive:
#        f_active = {x.track_num for x in CURRENT_REGION.items}
#        for k, v in TRACK_PANEL.tracks.items():
#            v.group_box.setHidden(k not in f_active)
#    else:
#        for v in TRACK_PANEL.tracks.values():
#            v.group_box.setHidden(False)
#    REGION_EDITOR.setUpdatesEnabled(True)
#    REGION_EDITOR.update()

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
        if a_items != CURRENT_ITEM_NAME:
            # Don't allow undo/redo to items that are no
            # longer open in the editor
            PROJECT.clear_undo_context(TAB_ITEM_EDITOR)
            LAST_ITEM_NAME = CURRENT_ITEM_NAME
            LAST_ITEM = CURRENT_ITEM
            CURRENT_ITEM_NAME = a_items
        ITEM_EDITOR.enabled = True
        PIANO_ROLL_EDITOR.selected_note_strings = []
        pydaw_set_piano_roll_quantize()
        if a_reset_scrollbar:
            for f_editor in MIDI_EDITORS:
                f_editor.horizontalScrollBar().setSliderPosition(0)
        f_items_dict = PROJECT.get_items_dict()
        f_uid = f_items_dict.get_uid_by_name(a_items)
        CURRENT_ITEM = PROJECT.get_item_by_uid(f_uid)
        ITEM_EDITOR.item_name_lineedit.setText(a_items)
        ITEM_EDITOR.item_name_lineedit.setReadOnly(False)

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

def open_last():
    if LAST_ITEM_NAME:
        global_open_items(LAST_ITEM_NAME, a_new_ref=LAST_ITEM_REF)
        MAIN_WINDOW.tab_changed()

#Opens or creates a new project
def global_open_project(a_project_file):
    global PROJECT, TRACK_NAMES, TRACK_COLORS
    PROJECT = DawProject(util.global_pydaw_with_audio)
    PROJECT.suppress_updates = True
    PROJECT.open_project(a_project_file, False)
    TRACK_COLORS = PROJECT.get_track_colors()
    TRACK_PANEL.open_tracks()
    PROJECT.suppress_updates = False
    f_scale = PROJECT.get_midi_scale()
    if f_scale is not None:
        PIANO_ROLL_EDITOR_WIDGET.scale_key_combobox.setCurrentIndex(f_scale[0])
        PIANO_ROLL_EDITOR_WIDGET.scale_combobox.setCurrentIndex(f_scale[1])
    MAIN_WINDOW.last_offline_dir = glbl.PROJECT.user_folder
    MAIN_WINDOW.notes_tab.setText(PROJECT.get_notes())
    ROUTING_GRAPH_WIDGET.draw_graph(
        PROJECT.get_routing_graph(), TRACK_PANEL.get_track_names())
    global_open_mixer()
    MIDI_DEVICES_DIALOG.set_routings()
    SEQ_WIDGET.open_region()
    SEQ_WIDGET.snap_combobox.setCurrentIndex(1)
    TRANSPORT.open_project()
    PLUGIN_RACK.initialize(PROJECT)
    MIXER_WIDGET.set_project(PROJECT)
    PIANO_ROLL_EDITOR.default_vposition()

def global_new_project(a_project_file):
    global PROJECT, TRACK_COLORS
    PROJECT = DawProject(util.global_pydaw_with_audio)
    PROJECT.new_project(a_project_file)
    TRACK_COLORS = PROJECT.get_track_colors()
    global_update_track_comboboxes()
    MAIN_WINDOW.last_offline_dir = glbl.PROJECT.user_folder
    MAIN_WINDOW.notes_tab.setText("")
    ROUTING_GRAPH_WIDGET.scene.clear()
    global_open_mixer()
    SEQ_WIDGET.open_region()
    SEQ_WIDGET.snap_combobox.setCurrentIndex(1)
    PLUGIN_RACK.initialize(PROJECT)
    MIXER_WIDGET.set_project(PROJECT)
    PIANO_ROLL_EDITOR.default_vposition()

def pydaw_seconds_to_beats(a_seconds):
    '''converts seconds to regions'''
    return a_seconds * (CURRENT_REGION.get_tempo_at_pos(
        CURRENT_ITEM_REF.start_beat) / 60.0)


def global_set_playback_pos(a_beat=None):
    if a_beat is not None:
        global PLAYBACK_POS
        PLAYBACK_POS = float(a_beat)
    TRANSPORT.set_pos_from_cursor(PLAYBACK_POS)
    for f_editor in (
        SEQUENCER,
        AUDIO_SEQ,
        PIANO_ROLL_EDITOR,
        PB_EDITOR,
        CC_EDITOR,
    ):
        f_editor.set_playback_pos(PLAYBACK_POS)
    TRANSPORT.set_time(PLAYBACK_POS)

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
    if glbl.PLUGIN_UI_DICT:
        glbl.PLUGIN_UI_DICT.close_all_plugin_windows()
    SEQ_WIDGET.clear_new()
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
    SEQ_WIDGET.open_region()
    MAIN_WINDOW.tab_changed()
    PROJECT.IPC.pydaw_open_song(PROJECT.project_folder, a_restore_all)


def on_ready():
    """ Called after re-opening the audio engine """
    # Ensure that loop mode is restored in the engine
    # to the same setting as the UI, since this is not part
    # of the saved data
    TRANSPORT.on_loop_mode_changed(
        TRANSPORT.loop_mode_combobox.currentIndex(),
    )

def get_mixer_peak_meters():
    for k, v in MIXER_WIDGET.tracks.items():
        ALL_PEAK_METERS[k].append(v.peak_meter)

def routing_graph_toggle_callback(a_src, a_dest, a_sidechain):
    f_graph = PROJECT.get_routing_graph()
    f_result = f_graph.toggle(a_src, a_dest, a_sidechain)
    if f_result:
        QMessageBox.warning(MAIN_WINDOW, _("Error"), f_result)
    else:
        PROJECT.save_routing_graph(f_graph)
        ROUTING_GRAPH_WIDGET.draw_graph(f_graph, TRACK_NAMES)
        PROJECT.commit(_("Update routing"))

def set_tooltips_enabled(a_enabled):
    """ Set extensive tooltips as an alternative to
        maintaining a separate user manual
    """
    glbl.TOOLTIPS_ENABLED = a_enabled

    f_list = [
        AUDIO_SEQ,
        AUDIO_SEQ_WIDGET,
        MAIN_WINDOW,
        MIXER_WIDGET,
        PIANO_ROLL_EDITOR,
        PLUGIN_RACK,
        SEQUENCER,
        TRACK_PANEL,
        TRANSPORT,
    ] + list(AUTOMATION_EDITORS)
    for f_widget in f_list:
        f_widget.set_tooltips(a_enabled)

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
    LAST_NOTE_RESIZE = util.pydaw_clip_min(
        LAST_NOTE_RESIZE,
        PIANO_ROLL_SNAP_BEATS,
    )
    PIANO_ROLL_EDITOR.set_grid_div(PIANO_ROLL_SNAP_DIVISOR)
    PIANO_ROLL_SNAP_VALUE = (
        PIANO_ROLL_GRID_WIDTH
        /
        CURRENT_ITEM_LEN
        /
        PIANO_ROLL_SNAP_DIVISOR
    )
    PIANO_ROLL_MIN_NOTE_LENGTH = (
        PIANO_ROLL_GRID_WIDTH
        /
        CURRENT_ITEM_LEN
        /
        32.0
    )

def global_open_audio_items(
    a_update_viewer=True,
    a_reload=True,
):
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
                    f_graph = glbl.PROJECT.get_sample_graph_by_uid(v.uid)
                    if f_graph is None:
                        print(
                            _(
                                "Error drawing item for {}, could not get "
                                "sample graph object"
                            ).format(v.uid)
                        )
                        continue
                    AUDIO_SEQ.draw_item(k, v, f_graph)
#                except:
#                    if glbl.IS_PLAYING:
#                        print(_("Exception while loading {}".format(v.uid)))
#                    else:
#                        f_path = glbl.PROJECT.get_wav_path_by_uid(v.uid)
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

def global_update_track_comboboxes(a_index=None, a_value=None):
    if (
        a_index is not None
        and
        a_value is not None
    ):
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
        PROJECT.get_routing_graph(),
        TRACK_PANEL.get_track_names(),
    )
    global_open_mixer()


# Only functions, globals must accessed through the module
__all__ = [
    'active_wav_pool_uids',
    'get_mixer_peak_meters',
    'global_close_all',
    'global_new_project',
    'global_open_audio_items',
    'global_open_items',
    'global_open_mixer',
    'global_open_project',
    'global_save_and_reload_items',
    'global_set_midi_zoom',
    'global_set_playback_pos',
    'global_ui_refresh_callback',
    'global_update_hidden_rows',
    'global_update_peak_meters',
    'global_update_track_comboboxes',
    'on_ready',
    'open_last',
    'pydaw_get_current_region_length',
    'pydaw_seconds_to_beats',
    'pydaw_set_audio_snap',
    'pydaw_set_piano_roll_quantize',
    'routing_graph_toggle_callback',
    'set_tooltips_enabled',
]
