from . import _shared
from .fade_vol_dialog import FadeVolDialogWidget
from .time_pitch_dialog import TimePitchDialogWidget
from mkpy import glbl
from mkpy.daw import shared
from mkpy.daw.project import *
from mkpy.daw.shared import *
from mkpy.lib import util
from mkpy.lib.util import *
from mkpy.lib.translate import _
from mkpy.mkqt import *
import shutil


LAST_AUDIO_ITEM_DIR = global_home

def show():
    f_CURRENT_AUDIO_ITEM_INDEX = _shared.CURRENT_AUDIO_ITEM_INDEX
    _shared.CURRENT_AUDIO_ITEM_INDEX = _shared.CURRENT_ITEM.track_num
    f_menu = QMenu(shared.MAIN_WINDOW)

    shared.AUDIO_SEQ.context_menu_enabled = False

    f_file_menu = f_menu.addMenu(_("File"))
    f_save_a_copy_action = f_file_menu.addAction(_("Save a Copy..."))
    f_save_a_copy_action.triggered.connect(save_a_copy)
    f_open_folder_action = f_file_menu.addAction(_("Open File in Browser"))
    f_open_folder_action.triggered.connect(open_item_folder)
    f_wave_editor_action = f_file_menu.addAction(_("Open in Wave Editor"))
    f_wave_editor_action.triggered.connect(open_in_wave_editor)
    f_copy_file_path_action = f_file_menu.addAction(
        _("Copy File Path to Clipboard"),
    )
    f_copy_file_path_action.triggered.connect(
        copy_file_path_to_clipboard,
    )
    f_select_instance_action = f_file_menu.addAction(
        _("Select All Instances of This File"),
    )
    f_select_instance_action.triggered.connect(select_file_instance)
    f_file_menu.addSeparator()
    f_replace_action = f_file_menu.addAction(
        _("Replace with Path in Clipboard"),
    )
    f_replace_action.triggered.connect(replace_with_path_in_clipboard)

    f_properties_menu = f_menu.addMenu(_("Properties"))

    f_ts_mode_menu = f_properties_menu.addMenu("Timestretch Mode")
    f_ts_mode_menu.triggered.connect(ts_mode_menu_triggered)

    f_ts_modes = {
        x.audio_item.time_stretch_mode
        for x in shared.AUDIO_SEQ.get_selected()
    }

    for f_ts_mode in TIMESTRETCH_MODES:
        f_index = util.TIMESTRETCH_INDEXES[f_ts_mode]
        f_action = f_ts_mode_menu.addAction(f_ts_mode)
        f_action.algo_name = f_ts_mode
        if len(f_ts_modes) == 1 and f_index in f_ts_modes:
            f_action.setCheckable(True)
            f_action.setChecked(True)

    if len(f_ts_modes) == 1 and [x for x in (3, 4) if x in f_ts_modes]:
        f_crisp_menu = f_properties_menu.addMenu("Crispness")
        f_crisp_menu.triggered.connect(crisp_menu_triggered)
        f_crisp_settings = {x.audio_item.crispness
            for x in shared.AUDIO_SEQ.get_selected()}
        for f_crisp_mode, f_index in zip(
        CRISPNESS_SETTINGS, range(len(CRISPNESS_SETTINGS))):
            f_action = f_crisp_menu.addAction(f_crisp_mode)
            f_action.crisp_mode = f_crisp_mode
            if len(f_crisp_settings) == 1 and \
            f_index in f_crisp_settings:
                f_action.setCheckable(True)
                f_action.setChecked(True)

    f_output_modes = {x.audio_item.output_track
        for x in shared.AUDIO_SEQ.get_selected()}

    f_output_menu = f_properties_menu.addMenu(_("Output"))
    f_output_menu.triggered.connect(output_mode_triggered)
    for f_i, f_name in zip(
    range(3), [_("Normal"), _("Sidechain"), _("Both")]):
        f_action = f_output_menu.addAction(f_name)
        f_action.output_val = f_i
        if len(f_output_modes) == 1 and f_i in f_output_modes:
            f_action.setCheckable(True)
            f_action.setChecked(True)

    f_volume_action = f_properties_menu.addAction(_("Volume..."))
    f_volume_action.triggered.connect(volume_dialog)
    f_normalize_action = f_properties_menu.addAction(_("Normalize..."))
    f_normalize_action.triggered.connect(normalize_dialog)
    f_reset_fades_action = f_properties_menu.addAction(_("Reset Fades"))
    f_reset_fades_action.triggered.connect(reset_fades)
    f_reset_end_action = f_properties_menu.addAction(_("Reset Ends"))
    f_reset_end_action.triggered.connect(reset_end)
    f_move_to_end_action = f_properties_menu.addAction(
        _("Move to Item End"),
    )
    f_move_to_end_action.triggered.connect(move_to_item_end)
    f_reverse_action = f_properties_menu.addAction(_("Reverse/Unreverse"))
    f_reverse_action.triggered.connect(_reverse)
    f_time_pitch_action = f_properties_menu.addAction(_("Time/Pitch..."))
    f_time_pitch_action.triggered.connect(time_pitch_dialog)
    f_fade_vol_action = f_properties_menu.addAction(_("Fade Volume..."))
    f_fade_vol_action.triggered.connect(fade_vol_dialog)

    f_paif_menu = f_menu.addMenu(_("Per-Item FX"))
    f_edit_paif_action = f_paif_menu.addAction(_("Edit Per-Item Effects"))
    f_edit_paif_action.triggered.connect(edit_paif)
    f_paif_menu.addSeparator()
    f_paif_copy = f_paif_menu.addAction(_("Copy"))
    f_paif_copy.triggered.connect(
        shared.AUDIO_SEQ_WIDGET.on_modulex_copy,
    )
    f_paif_paste = f_paif_menu.addAction(_("Paste"))
    f_paif_paste.triggered.connect(
        shared.AUDIO_SEQ_WIDGET.on_modulex_paste,
    )
    f_paif_clear = f_paif_menu.addAction(_("Clear"))
    f_paif_clear.triggered.connect(
        shared.AUDIO_SEQ_WIDGET.on_modulex_clear,
    )

    f_menu.exec_(QCursor.pos())
    _shared.CURRENT_AUDIO_ITEM_INDEX = f_CURRENT_AUDIO_ITEM_INDEX

def save_a_copy():
    global LAST_AUDIO_ITEM_DIR
    f_file, f_filter = QFileDialog.getSaveFileName(
        parent=shared.MAIN_WINDOW,
        caption=_('Save audio item as .wav'),
        directory=LAST_AUDIO_ITEM_DIR,
        options=QFileDialog.DontUseNativeDialog,
    )
    if not f_file is None and not str(f_file) == "":
        f_file = str(f_file)
        if not f_file.endswith(".wav"):
            f_file += ".wav"
        LAST_AUDIO_ITEM_DIR = os.path.dirname(f_file)
        f_orig_path = glbl.PROJECT.get_wav_name_by_uid(
            _shared.CURRENT_ITEM.audio_item.uid,
        )
        shutil.copy(f_orig_path, f_file)

def open_item_folder():
    f_path = glbl.PROJECT.get_wav_name_by_uid(
        _shared.CURRENT_ITEM.audio_item.uid,
    )
    shared.AUDIO_SEQ_WIDGET.open_file_in_browser(f_path)

def open_in_wave_editor():
    f_path = _shared.CURRENT_ITEM.get_file_path()
    glbl.MAIN_WINDOW.open_in_wave_editor(f_path)

def copy_file_path_to_clipboard():
    f_path = _shared.CURRENT_ITEM.get_file_path()
    f_clipboard = QApplication.clipboard()
    f_clipboard.setText(f_path)

def select_file_instance():
    shared.AUDIO_SEQ.scene.clearSelection()
    f_uid = _shared.CURRENT_ITEM.audio_item.uid
    for f_item in shared.AUDIO_SEQ.audio_items:
        if f_item.audio_item.uid == f_uid:
            f_item.setSelected(True)

def replace_with_path_in_clipboard():
    f_path = _shared.global_get_audio_file_from_clipboard()
    if f_path is not None:
        _shared.CURRENT_ITEM.audio_item.uid = \
            glbl.PROJECT.get_wav_uid_by_name(f_path)
        shared.PROJECT.save_item(
            shared.CURRENT_ITEM_NAME,
            shared.CURRENT_ITEM,
        )
        shared.PROJECT.commit(_("Replace audio item"))
        global_open_audio_items(True)

def ts_mode_menu_triggered(a_action):
    f_index = TIMESTRETCH_INDEXES[a_action.algo_name]
    f_list = [x.audio_item for x in shared.AUDIO_SEQ.get_selected()]
    for f_item in f_list:
        f_item.time_stretch_mode = f_index
    timestretch_items(f_list)

def output_mode_triggered(a_action):
    f_list = shared.AUDIO_SEQ.get_selected()
    for f_item in f_list:
        f_item.audio_item.output_track = a_action.output_val
    shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
    shared.PROJECT.commit(_("Set audio items output mode"))
    global_open_audio_items(True)

def volume_dialog():
    def on_ok():
        f_val = round(f_db_spinbox.value(), 1)
        for f_item in shared.AUDIO_SEQ.get_selected():
            f_item.audio_item.vol = f_val
        shared.PROJECT.save_item(
            shared.CURRENT_ITEM_NAME,
            shared.CURRENT_ITEM,
        )
        shared.PROJECT.commit(_("Normalize audio items"))
        global_open_audio_items(True)
        f_window.close()

    def on_cancel():
        f_window.close()

    f_window = QDialog(shared.MAIN_WINDOW)
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
    f_vols = {x.audio_item.vol for x in shared.AUDIO_SEQ.get_selected()}
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

def normalize_dialog():
    f_val = _normalize_dialog()
    if f_val is None:
        return
    f_save = False
    for f_item in shared.AUDIO_SEQ.get_selected():
        f_save = True
        f_item.normalize(f_val)
    if f_save:
        shared.PROJECT.save_item(
            shared.CURRENT_ITEM_NAME,
            shared.CURRENT_ITEM,
        )
        shared.PROJECT.commit(_("Normalize audio items"))
        global_open_audio_items(True)

def _normalize_dialog():
    def on_ok():
        f_window.f_result = f_db_spinbox.value()
        f_window.close()

    def on_cancel():
        f_window.close()

    f_window = QDialog(shared.MAIN_WINDOW)
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

def reset_fades():
    f_list = shared.AUDIO_SEQ.get_selected()
    if f_list:
        for f_item in f_list:
            f_item.audio_item.fade_in = 0.0
            f_item.audio_item.fade_out = 999.0
        shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
        shared.PROJECT.commit(_("Reset audio item fades"))
        global_open_audio_items(True)

def reset_end():
    f_list = shared.AUDIO_SEQ.get_selected()
    for f_item in f_list:
        f_item.audio_item.sample_start = 0.0
        f_item.audio_item.sample_end = 1000.0
        _shared.CURRENT_ITEM.draw()
        _shared.CURRENT_ITEM.clip_at_region_end()
    shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
    shared.PROJECT.commit(_("Reset sample ends for audio item(s)"))
    global_open_audio_items()

def move_to_item_end():
    f_list = shared.AUDIO_SEQ.get_selected()
    if f_list:
        f_current_region_length = pydaw_get_current_region_length()
        f_global_tempo = shared.CURRENT_REGION.get_tempo_at_pos(
            shared.CURRENT_ITEM_REF.start_beat,
        )
        for f_item in f_list:
            f_item.audio_item.clip_at_region_end(
                f_current_region_length,
                f_global_tempo,
                f_item.graph_object.length_in_seconds,
                False,
            )
        shared.PROJECT.save_item(
            shared.CURRENT_ITEM_NAME,
            shared.CURRENT_ITEM,
        )
        shared.PROJECT.commit(_("Move audio item(s) to region end"))
        global_open_audio_items(True)

def _reverse():
    f_list = shared.AUDIO_SEQ.get_selected()
    for f_item in f_list:
        f_item.audio_item.reversed = not f_item.audio_item.reversed
        # Invert the start/end and fades so that the same section stays in
        # the sequencer exactly as it is, just reversed
        start = f_item.audio_item.sample_start
        end = f_item.audio_item.sample_end
        f_item.audio_item.sample_start = 1000. - end
        f_item.audio_item.sample_end = 1000. - start

        fade_in = f_item.audio_item.fade_in
        fade_out = f_item.audio_item.fade_out
        f_item.audio_item.fade_in = 999. - fade_out
        f_item.audio_item.fade_out = 1000. - fade_in - 1.

    shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
    shared.PROJECT.commit(_("Toggle audio items reversed"))
    global_open_audio_items(True)

def time_pitch_dialog():
    f_dialog = TimePitchDialogWidget(_shared.CURRENT_ITEM.audio_item)
    f_dialog.widget.exec_()

def fade_vol_dialog():
    f_dialog = FadeVolDialogWidget(_shared.CURRENT_ITEM.audio_item)
    f_dialog.widget.exec_()

def edit_paif():
    shared.AUDIO_SEQ.scene.clearSelection()
    _shared.CURRENT_ITEM.setSelected(True)
    shared.AUDIO_SEQ_WIDGET.folders_tab_widget.setCurrentIndex(2)

def crisp_menu_triggered(a_action):
    f_index = CRISPNESS_SETTINGS.index(a_action.crisp_mode)
    f_list = [
        x.audio_item
        for x in shared.AUDIO_SEQ.get_selected()
        if x.audio_item.time_stretch_mode in (3, 4)
    ]
    for f_item in f_list:
        f_item.crispness = f_index
    timestretch_items(f_list)

def timestretch_items(a_list):
    f_stretched_items = []
    for f_item in a_list:
        if f_item.time_stretch_mode >= 3:
            f_ts_result = glbl.PROJECT.timestretch_audio_item(f_item)
            if f_ts_result is not None:
                f_stretched_items.append(f_ts_result)

    glbl.PROJECT.save_stretch_dicts()

    for f_stretch_item in f_stretched_items:
        f_stretch_item[2].wait()
        glbl.PROJECT.get_wav_uid_by_name(
            f_stretch_item[0],
            a_uid=f_stretch_item[1],
        )
    for f_audio_item in shared.AUDIO_SEQ.get_selected():
        f_new_graph = glbl.PROJECT.get_sample_graph_by_uid(
            f_audio_item.audio_item.uid,
        )
        f_audio_item.audio_item.clip_at_region_end(
            pydaw_get_current_region_length(),
            shared.CURRENT_REGION.get_tempo_at_pos(
                shared.CURRENT_ITEM_REF.start_beat,
            ),
            f_new_graph.length_in_seconds,
        )

    shared.PROJECT.save_item(
        shared.CURRENT_ITEM_NAME,
        shared.CURRENT_ITEM,
    )
    shared.PROJECT.commit(_("Change timestretch mode for audio item(s)"))
    global_open_audio_items()

