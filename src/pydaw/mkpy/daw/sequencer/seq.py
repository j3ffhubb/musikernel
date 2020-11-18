from . import (
    _shared,
    atm_context_menu,
    context_menu,
    header_context_menu,
)
from .atm_item import SeqAtmItem
from .item import SequencerItem
from mkpy import glbl, widgets
from mkpy.daw import shared
from mkpy.daw import strings as daw_strings
from mkpy.daw.project import *
from mkpy.daw.shared import *
from mkpy.libpydaw import pydaw_util
from mkpy.libpydaw.pydaw_util import *
from mkpy.libpydaw.translate import _
from mkpy.plugins import *
from mkpy.mkqt import *

class ItemSequencer(QGraphicsView):
    """ This is the sequencer QGraphicsView and QGraphicsScene on
        the "Sequencer" tab
    """
    def __init__(self):
        QGraphicsView.__init__(self)

        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        #self.setOptimizationFlag(QGraphicsView.DontSavePainterState)
        #self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing)
        self.setRenderHint(QPainter.Antialiasing)

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

        self.current_atm_point = None

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
        self.scene.setBackgroundBrush(widgets.SCENE_BACKGROUND_BRUSH)
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

        _shared.init()
        atm_context_menu.init()
        context_menu.init()

        self.addAction(_shared.copy_action)
        self.addAction(_shared.delete_action)
        self.addAction(atm_context_menu.break_atm_action)
        self.addAction(atm_context_menu.unbreak_atm_action)
        self.addAction(context_menu.cut_action)
        self.addAction(context_menu.glue_action)
        self.addAction(context_menu.rename_action)
        self.addAction(context_menu.transpose_action)
        self.addAction(context_menu.unlink_action)
        self.addAction(context_menu.unlink_selected_action)
        self.addAction(context_menu.unlink_unique_action)

        self.context_menu_enabled = True

    def show_context_menu(self):
        if glbl.IS_PLAYING:
            return
        if not self.context_menu_enabled:
            self.context_menu_enabled = True
            return
        if _shared.REGION_EDITOR_MODE == 0:
            context_menu.populate_takes_menu()
            context_menu.MENU.exec_(QCursor.pos())
        elif _shared.REGION_EDITOR_MODE == 1:
            atm_context_menu.MENU.exec_(QCursor.pos())
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
        if glbl.IS_PLAYING:
            return
        f_pos = self.mapToScene(a_event.pos())
        self.current_coord = self.get_item_coord(f_pos)

        if f_pos.x() > self.max_x:
            return

        if self.check_header(f_pos):
            if a_event.button() == QtCore.Qt.LeftButton:
                f_beat = int(f_pos.x() / _shared.SEQUENCER_PX_PER_BEAT)
                global_set_playback_pos(f_beat)
            return

        if a_event.button() == QtCore.Qt.RightButton:
            if self.current_coord:
                if _shared.REGION_EDITOR_MODE == 0:
                    self.current_item = self.get_item(f_pos)
                    if self.current_item and \
                    not self.current_item.isSelected():
                        self.scene.clearSelection()
                        self.current_item.setSelected(True)
                        self.selected_item_strings = {
                            self.current_item.get_selected_string()}
                self.show_context_menu()
        elif _shared.REGION_EDITOR_MODE == 0:
            self.current_item = self.get_item(f_pos)
            self.setDragMode(QGraphicsView.RubberBandDrag)
            if shared.EDITOR_MODE == shared.EDITOR_MODE_SELECT:
                f_item = self.get_item(f_pos)
                if f_item:
                    if not f_item.isSelected():
                        self.scene.clearSelection()
                    f_item.setSelected(True)
                    self.selected_item_strings = {f_item.get_selected_string()}
                    QGraphicsView.mousePressEvent(self, a_event)
                    return
            elif shared.EDITOR_MODE == shared.EDITOR_MODE_DRAW:
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
                f_pos_y = f_pos.y() - _shared.REGION_EDITOR_HEADER_HEIGHT
                f_beat = float(f_pos_x // _shared.SEQUENCER_PX_PER_BEAT)
                f_track = int(f_pos_y // shared.REGION_EDITOR_TRACK_HEIGHT)
                print(f_track, shared.TRACK_NAMES)
                f_item_name = "{}-1".format(shared.TRACK_NAMES[f_track])
                f_uid = shared.PROJECT.create_empty_item(f_item_name)
                f_item_ref = pydaw_sequencer_item(
                    f_track,
                    f_beat,
                    _shared.LAST_ITEM_LENGTH,
                    f_uid,
                )
                shared.CURRENT_REGION.add_item_ref_by_uid(f_item_ref)
                self.selected_item_strings = {str(f_item_ref)}
                shared.PROJECT.save_region(shared.CURRENT_REGION)
                shared.PROJECT.commit(_("Add new item"))
                shared.REGION_SETTINGS.open_region()
                return
            elif shared.EDITOR_MODE == shared.EDITOR_MODE_ERASE:
                self.deleted_items = []
                region_editor_set_delete_mode(True)
            else:
                f_item = self.get_item(f_pos)
                if f_item:
                    self.selected_item_strings = {
                        f_item.get_selected_string()}
                else:
                    self.clear_selected_item_strings()

        elif _shared.REGION_EDITOR_MODE == 1:
            self.setDragMode(QGraphicsView.NoDrag)
            self.atm_select_pos_x = None
            self.atm_select_track = None
            if shared.EDITOR_MODE == shared.EDITOR_MODE_SELECT or \
            shared.EDITOR_MODE == shared.EDITOR_MODE_ERASE:
                self.current_coord = self.get_item_coord(f_pos, True)
                self.scene.clearSelection()
                self.atm_select_pos_x = f_pos.x()
                self.atm_select_track = self.current_coord[0]
                if shared.EDITOR_MODE == shared.EDITOR_MODE_ERASE:
                    self.atm_delete = True
                    return
            elif a_event.button() == QtCore.Qt.RightButton:
                pass
            elif shared.EDITOR_MODE == shared.EDITOR_MODE_DRAW and \
            self.current_coord is not None:
                f_port, f_index = shared.TRACK_PANEL.has_automation(
                    self.current_coord[0])
                if f_port is not None:
                    f_track, f_beat, f_val = self.current_coord
                    f_beat = self.quantize(f_beat)
                    f_point = DawAtmPoint(
                        f_beat, f_port, f_val,
                        *shared.TRACK_PANEL.get_atm_params(f_track))
                    shared.ATM_REGION.add_point(f_point)
                    point_item = self.draw_point(f_point)
                    point_item.setSelected(True)
                    self.current_atm_point = point_item
                    QGraphicsView.mousePressEvent(self, a_event)
                    return
        a_event.accept()
        QGraphicsView.mousePressEvent(self, a_event)

    def sceneMouseMoveEvent(self, a_event):
        QGraphicsScene.mouseMoveEvent(self.scene, a_event)
        if _shared.REGION_EDITOR_MODE == 0:
            if _shared.REGION_EDITOR_DELETE_MODE:
                f_item = self.get_item(a_event.scenePos())
                if f_item and not f_item.audio_item in self.deleted_items:
                    f_item.hide()
                    self.deleted_items.append(f_item.audio_item)
        elif _shared.REGION_EDITOR_MODE == 1:
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
        if _shared.REGION_EDITOR_MODE == 0:
            if _shared.REGION_EDITOR_DELETE_MODE:
                region_editor_set_delete_mode(False)
                self.scene.clearSelection()
                self.selected_item_strings = set()
                for f_item in self.deleted_items:
                    shared.CURRENT_REGION.remove_item_ref(f_item)
                shared.PROJECT.save_region(shared.CURRENT_REGION)
                shared.PROJECT.commit("Delete sequencer items")
                self.open_region()
                glbl.clean_wav_pool()
            else:
                QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        elif _shared.REGION_EDITOR_MODE == 1:
            if self.atm_delete:
                self.delete_selected_atm(self.atm_select_track)
            elif shared.EDITOR_MODE == shared.EDITOR_MODE_DRAW:
                if self.current_atm_point:
                    self.current_atm_point.set_point_value()
                    self.current_atm_point = None
                self.automation_save_callback()
            QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        else:
            QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        self.atm_select_pos_x = None
        self.atm_select_track = None
        self.atm_delete = False

    def get_item_coord(self, a_pos, a_clip=False):
        f_pos_x = a_pos.x()
        f_pos_y = a_pos.y() - _shared.REGION_EDITOR_HEADER_HEIGHT
        if a_clip or (
        f_pos_x > 0 and
        f_pos_y > 0 and
        f_pos_y < _shared.REGION_EDITOR_TOTAL_HEIGHT):
            f_pos_x = pydaw_util.pydaw_clip_min(f_pos_x, 0.0)
            f_pos_y = pydaw_util.pydaw_clip_value(
                f_pos_y,
                0.0,
                _shared.REGION_EDITOR_TOTAL_HEIGHT,
            )
            f_track_height = (
                shared.REGION_EDITOR_TRACK_HEIGHT
                -
                _shared.ATM_POINT_DIAMETER
            )
            f_track = int(f_pos_y / shared.REGION_EDITOR_TRACK_HEIGHT)
            f_val = (
                1.0 - (
                    (
                        f_pos_y - (
                            f_track * shared.REGION_EDITOR_TRACK_HEIGHT
                        )
                    ) / f_track_height
                )
            ) * 127.0
            f_beat = f_pos_x / _shared.SEQUENCER_PX_PER_BEAT
            return f_track, round(f_beat, 6), round(f_val, 6)
        else:
            return None

    def delete_selected_atm(self, a_track):
        _shared.copy_selected()
        f_selected = list(self.get_selected_points(a_track))
        self.scene.clearSelection()
        self.selected_point_strings = set()
        for f_point in f_selected:
            self.automation_points.remove(f_point)
            shared.ATM_REGION.remove_point(f_point.item)
        self.automation_save_callback()

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
        f_dict = shared.TRACK_PANEL.plugin_uid_map
        if a_track is None:
            for f_point in self.automation_points:
                yield f_point
        else:
            a_track = int(a_track)
            for f_point in self.automation_points:
                if f_dict[f_point.item.index] == a_track:
                    yield f_point

    def get_selected_points(self, a_track=None):
        f_dict = shared.TRACK_PANEL.plugin_uid_map
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
        if _shared.REGION_EDITOR_MODE == 0:
            shared.SEQUENCER.setDragMode(QGraphicsView.NoDrag)
        elif _shared.REGION_EDITOR_MODE == 1:
            shared.SEQUENCER.setDragMode(QGraphicsView.RubberBandDrag)
        self.enabled = False
        shared.ATM_REGION = shared.PROJECT.get_atm_region()
        f_items_dict = shared.PROJECT.get_items_dict()
        f_scrollbar = self.horizontalScrollBar()
        f_scrollbar_value = f_scrollbar.value()
        self.setUpdatesEnabled(False)
        self.clear_drawn_items()
        self.ignore_selection_change = True
        #, key=lambda x: x.bar_num,
        _shared.CACHED_SEQ_LEN = pydaw_get_current_region_length()
        for f_item in sorted(shared.CURRENT_REGION.items, reverse=True):
            if f_item.start_beat < pydaw_get_current_region_length():
                f_item_name = f_items_dict.get_name_by_uid(f_item.item_uid)
                f_new_item = self.draw_item(f_item_name, f_item)
                if f_new_item.get_selected_string() in \
                self.selected_item_strings:
                    f_new_item.setSelected(True)
        self.ignore_selection_change = False
        if _shared.REGION_EDITOR_MODE == 1:
            self.open_atm_region()
            shared.TRACK_PANEL.update_ccs_in_use()
        f_scrollbar.setValue(f_scrollbar_value)
        self.setUpdatesEnabled(True)
        self.update()
        self.enabled = True

    def open_atm_region(self):
        self.atm_paths = {}
        for f_track in shared.TRACK_PANEL.tracks:
            f_port, f_index = shared.TRACK_PANEL.has_automation(f_track)
            if f_port is not None:
                points = shared.ATM_REGION.get_points(f_index, f_port)
                if points:
                    point_items = [self.draw_point(x) for x in points]
                    self.draw_atm_lines(f_track, point_items)

    def draw_atm_lines(self, a_track_num, a_points):
        plugin_uid = a_points[0].item.index
        path = QPainterPath()
        point = a_points[0]
        pos = point.scenePos()
        x = pos.x() + _shared.ATM_POINT_RADIUS
        y = pos.y() + _shared.ATM_POINT_RADIUS
        path.moveTo(0.0, y)
        path.lineTo(x, y)
        break_after = point.item.break_after

        for point in a_points[1:]:
            pos = point.scenePos()
            x = pos.x() + _shared.ATM_POINT_RADIUS
            y = pos.y() + _shared.ATM_POINT_RADIUS
            if break_after:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
            break_after = point.item.break_after

        if not break_after:
            path.lineTo(self.sceneRect().right(), y)

        path_item = QGraphicsPathItem(path)
        path_item.setPen(QtCore.Qt.white)
        #path_item.setBrush(QtCore.Qt.white)
        self.scene.addItem(path_item)
        self.atm_paths[plugin_uid] = path_item

    def remove_atm_path(self, a_plugin_uid):
        if a_plugin_uid in self.atm_paths:
            self.scene.removeItem(self.atm_paths.pop(a_plugin_uid))

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

    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip(daw_strings.sequencer)
        else:
            self.setToolTip("")
        for f_item in self.audio_items:
            f_item.set_tooltips(a_on)

    def resizeEvent(self, a_event):
        QGraphicsView.resizeEvent(self, a_event)

    def sceneContextMenuEvent(self, a_event):
        if glbl.IS_PLAYING:
            return
        QGraphicsScene.contextMenuEvent(self.scene, a_event)
        self.show_context_menu()

    def highlight_selected(self):
        self.setUpdatesEnabled(False)
        self.has_selected = False
        if _shared.REGION_EDITOR_MODE == 0:
            for f_item in self.audio_items:
                f_item.set_brush()
                self.has_selected = True
        elif _shared.REGION_EDITOR_MODE == 1:
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
        if glbl.IS_PLAYING:
            return True
        return False

    def sceneDropEvent(self, a_event):
        f_pos = a_event.scenePos()
        if shared.AUDIO_ITEMS_TO_DROP:
            self.add_items(f_pos, shared.AUDIO_ITEMS_TO_DROP)
        elif MIDI_FILES_TO_DROP:
            f_midi_path = MIDI_FILES_TO_DROP[0]
            f_beat, f_lane_num = self.pos_to_beat_and_track(f_pos)
            f_midi = DawMidiFile(f_midi_path, shared.PROJECT)
            shared.PROJECT.import_midi_file(f_midi, f_beat, f_lane_num)
            shared.PROJECT.commit("Import MIDI file")
            shared.REGION_SETTINGS.open_region()

    def quantize(self, a_beat):
        if _shared.SEQ_QUANTIZE:
            return int(
                a_beat * _shared.SEQ_QUANTIZE_AMT
            ) / _shared.SEQ_QUANTIZE_AMT
        else:
            return a_beat

    def pos_to_beat_and_track(self, a_pos):
        f_beat_frac = (a_pos.x() / _shared.SEQUENCER_PX_PER_BEAT)
        f_beat_frac = pydaw_clip_min(f_beat_frac, 0.0)
        f_beat_frac = self.quantize(f_beat_frac)

        f_lane_num = int((a_pos.y() - _shared.REGION_EDITOR_HEADER_HEIGHT) /
            shared.REGION_EDITOR_TRACK_HEIGHT)
        f_lane_num = pydaw_clip_value(
            f_lane_num, 0, TRACK_COUNT_ALL - 1)

        return f_beat_frac, f_lane_num

    def add_items(self, a_pos, a_item_list, a_single_item=None):
        if self.check_running():
            return

        if a_single_item is None:
            if len(a_item_list) > 1:
                menu = QMenu()
                multi_action = menu.addAction(
                    "Add each file to it's own track")
                multi_action.triggered.connect(
                    lambda : self.add_items(a_pos, a_item_list, False))
                single_action = menu.addAction(
                    "Add all files to one item on one track")
                single_action.triggered.connect(
                    lambda : self.add_items(a_pos, a_item_list, True))
                menu.exec_(QCursor.pos())
                return
            else:
                a_single_item = True

        glbl.APP.setOverrideCursor(QtCore.Qt.WaitCursor)

        f_beat_frac, f_track_num = self.pos_to_beat_and_track(a_pos)

        f_seconds_per_beat = (60.0 /
            shared.CURRENT_REGION.get_tempo_at_pos(f_beat_frac))

        f_restart = False

        if a_single_item:
            lane_num = 0
            f_item_name = "{}-1".format(shared.TRACK_NAMES[f_track_num])
            f_item_uid = shared.PROJECT.create_empty_item(f_item_name)
            f_items = shared.PROJECT.get_item_by_uid(f_item_uid)
            f_item_ref = pydaw_sequencer_item(
                f_track_num,
                f_beat_frac,
                1.0,
                f_item_uid,
            )

        for f_file_name in a_item_list:
            glbl.APP.processEvents()
            f_file_name_str = str(f_file_name)
            f_item_name = os.path.basename(f_file_name_str)
            if f_file_name_str:
                if not a_single_item:
                    f_item_uid = shared.PROJECT.create_empty_item(f_item_name)
                    f_items = shared.PROJECT.get_item_by_uid(f_item_uid)
                f_index = f_items.get_next_index()

                if f_index == -1:
                    QMessageBox.warning(self, _("Error"),
                    _("No more available audio item slots, "
                    "max per region is {}").format(MAX_AUDIO_ITEM_COUNT))
                    break

                f_uid = glbl.PROJECT.get_wav_uid_by_name(f_file_name_str)
                f_graph = glbl.PROJECT.get_sample_graph_by_uid(f_uid)
                f_delta = datetime.timedelta(
                    seconds=f_graph.length_in_seconds)
                if not f_restart and glbl.add_entropy(f_delta):
                    f_restart = True
                f_length = f_graph.length_in_seconds / f_seconds_per_beat
                if a_single_item:
                    f_item = DawAudioItem(
                        f_uid, a_start_bar=0, a_start_beat=0.0,
                        a_lane_num=lane_num)
                    lane_num += 1
                    f_items.add_item(f_index, f_item)
                    if f_length > f_item_ref.length_beats:
                        f_item_ref.length_beats = f_length
                else:
                    f_item_ref = pydaw_sequencer_item(
                        f_track_num,
                        f_beat_frac,
                        f_length,
                        f_item_uid,
                    )
                    shared.CURRENT_REGION.add_item_ref_by_uid(f_item_ref)
                    f_item = DawAudioItem(
                        f_uid,
                        a_start_bar=0,
                        a_start_beat=0.0,
                        a_lane_num=0,
                    )
                    f_items.add_item(f_index, f_item)
                    shared.PROJECT.save_item_by_uid(f_item_uid, f_items)
                    f_track_num += 1
                    if f_track_num >= TRACK_COUNT_ALL:
                        break

        if a_single_item:
            shared.CURRENT_REGION.add_item_ref_by_uid(f_item_ref)
            shared.PROJECT.save_item_by_uid(f_item_uid, f_items)

        shared.PROJECT.save_region(shared.CURRENT_REGION, a_notify=not f_restart)
        shared.PROJECT.commit("Added audio items")
        shared.REGION_SETTINGS.open_region()
        self.last_open_dir = os.path.dirname(f_file_name_str)

        if f_restart:
            glbl.restart_engine()

        glbl.APP.restoreOverrideCursor()

    def get_beat_value(self):
        return self.playback_pos

    def set_playback_pos(self, a_beat=0.0):
        f_right = self.sceneRect().right()
        self.playback_pos = float(a_beat)
        if self.playback_pos > f_right:
            return
        f_pos = (self.playback_pos * _shared.SEQUENCER_PX_PER_BEAT)
        self.playback_cursor.setPos(f_pos, 0.0)
        if glbl.IS_PLAYING and shared.REGION_SETTINGS.follow_checkbox.isChecked():
            f_port_rect = self.viewport().rect()
            f_rect = self.mapToScene(f_port_rect).boundingRect()
            if not (f_pos > f_rect.left() and f_pos < f_rect.right()):
                f_pos = int(self.playback_pos) * _shared.SEQUENCER_PX_PER_BEAT
                shared.REGION_SETTINGS.scrollbar.setValue(int(f_pos))

    def start_playback(self):
        self.playback_pos_orig = self.playback_pos
        if _shared.REGION_EDITOR_MODE == 0:
            self.set_selected_strings()
        elif _shared.REGION_EDITOR_MODE == 1:
            self.set_selected_point_strings()

    def set_playback_clipboard(self):
        self.reselect_on_stop = []
        for f_item in self.audio_items:
            if f_item.isSelected():
                self.reselect_on_stop.append(str(f_item.audio_item))

    def stop_playback(self):
        self.reset_selection()
        global_set_playback_pos(self.playback_pos_orig)

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
        if (
            not glbl.IS_PLAYING
            and
            a_event.button() != QtCore.Qt.RightButton
        ):
            f_beat = int(a_event.scenePos().x() / _shared.SEQUENCER_PX_PER_BEAT)
            global_set_playback_pos(f_beat)

    def check_line_count(self):
        """ Check that there are not too many vertical
            lines on the screen
        """
        f_num_count = len(self.text_list)
        if f_num_count == 0:
            return
        view_pct = float(self.width()) / float(self.max_x)
        f_num_visible_count = int(f_num_count * view_pct)

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

    def get_region_items(self):
        f_region_start = shared.CURRENT_REGION.loop_marker.start_beat
        f_region_end = shared.CURRENT_REGION.loop_marker.beat
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
        f_size = _shared.SEQUENCER_PX_PER_BEAT * f_region_length
        self.max_x = f_size
        self.setSceneRect(
            -3.0,
            0.0,
            f_size + self.width() + 3.0,
            _shared.REGION_EDITOR_TOTAL_HEIGHT,
        )
        self.header = QGraphicsRectItem(
            0, 0, f_size, _shared.REGION_EDITOR_HEADER_HEIGHT)
        self.header.setZValue(1500.0)
        self.header.setBrush(shared.SEQUENCER_HEADER_BRUSH)
        self.header.mousePressEvent = self.header_click_event
        self.header.contextMenuEvent = header_context_menu.show
        self.scene.addItem(self.header)

        for f_marker in shared.CURRENT_REGION.get_markers():
            if f_marker.type == 1:  # Loop
                self.loop_start = f_marker.start_beat
                self.loop_end = f_marker.beat
                f_x = f_marker.start_beat * _shared.SEQUENCER_PX_PER_BEAT
                f_start = QGraphicsLineItem(
                    f_x, 0, f_x, _shared.REGION_EDITOR_HEADER_HEIGHT, self.header)
                f_start.setPen(shared.START_PEN)

                f_x = f_marker.beat * _shared.SEQUENCER_PX_PER_BEAT
                f_end = QGraphicsLineItem(
                    f_x, 0, f_x, _shared.REGION_EDITOR_HEADER_HEIGHT, self.header)
                f_end.setPen(shared.END_PEN)
            elif f_marker.type == 2:  # Tempo
                f_text = "{} : {}/{}".format(
                    f_marker.tempo,
                    f_marker.tsig_num,
                    f_marker.tsig_den,
                )
                item = QGraphicsEllipseItem(
                    0., 0., 12., 12.,
                    self.header,
                )
                item.setBrush(QtCore.Qt.white)
                item.setPos(
                    f_marker.beat * _shared.SEQUENCER_PX_PER_BEAT,
                    _shared.REGION_EDITOR_HEADER_ROW_HEIGHT,
                )
                item.setToolTip(f_text)
                item.mousePressEvent = header_context_menu.TempoMarkerEvent(
                    f_marker.beat,
                ).mouse_press
                self.draw_region(f_marker)
            elif f_marker.type == 3:  # Text
                f_item = QGraphicsSimpleTextItem(
                    f_marker.text, self.header)
                f_item.setBrush(QtCore.Qt.white)
                f_item.setPos(
                    f_marker.beat * _shared.SEQUENCER_PX_PER_BEAT,
                    _shared.REGION_EDITOR_HEADER_ROW_HEIGHT * 2,
                )
            else:
                assert False, "Invalid marker type"

        f_total_height = (
            _shared.REGION_EDITOR_TRACK_COUNT
            *
            shared.REGION_EDITOR_TRACK_HEIGHT
        ) + _shared.REGION_EDITOR_HEADER_HEIGHT
        self.playback_cursor = self.scene.addLine(
            0.0, 0.0, 0.0, f_total_height, QPen(QtCore.Qt.red, 2.0))
        self.playback_cursor.setZValue(1000.0)

        self.set_playback_pos(self.playback_pos)
        self.check_line_count()
        self.set_header_y_pos()

    def draw_region(self, a_marker):
        f_region_length = pydaw_get_current_region_length()
        f_size = _shared.SEQUENCER_PX_PER_BEAT * f_region_length
        f_v_pen = QPen(QtCore.Qt.black)
        f_beat_pen = QPen(QColor(210, 210, 210))
        f_16th_pen = QPen(QColor(120, 120, 120))
        f_reg_pen = QPen(QtCore.Qt.white)
        f_total_height = (
            _shared.REGION_EDITOR_TRACK_COUNT
            *
            shared.REGION_EDITOR_TRACK_HEIGHT
        ) + _shared.REGION_EDITOR_HEADER_HEIGHT

        f_x_offset = a_marker.beat * _shared.SEQUENCER_PX_PER_BEAT
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
                if (
                    _shared.SEQ_LINES_ENABLED
                    and
                    _shared.DRAW_SEQUENCER_GRAPHS
                ):
                    for f_i4 in range(1, _shared.SEQ_SNAP_RANGE):
                        f_sub_x = i3 + (_shared.SEQUENCER_QUANTIZE_PX * f_i4)
                        f_line = self.scene.addLine(
                            f_sub_x, _shared.REGION_EDITOR_HEADER_HEIGHT,
                            f_sub_x, f_total_height, f_16th_pen)
                        self.beat_line_list.append(f_line)
            elif _shared.DRAW_SEQUENCER_GRAPHS:
                f_beat_x = i3
                f_line = self.scene.addLine(
                    f_beat_x, 0.0, f_beat_x, f_total_height, f_beat_pen)
                self.beat_line_list.append(f_line)
                if _shared.SEQ_LINES_ENABLED:
                    for f_i4 in range(1, _shared.SEQ_SNAP_RANGE):
                        f_sub_x = f_beat_x + (
                            _shared.SEQUENCER_QUANTIZE_PX * f_i4
                        )
                        f_line = self.scene.addLine(
                            f_sub_x, _shared.REGION_EDITOR_HEADER_HEIGHT,
                            f_sub_x, f_total_height, f_16th_pen)
                        self.beat_line_list.append(f_line)
            i3 += _shared.SEQUENCER_PX_PER_BEAT
        self.scene.addLine(
            i3, _shared.REGION_EDITOR_HEADER_HEIGHT, i3, f_total_height, f_reg_pen)
        for i2 in range(_shared.REGION_EDITOR_TRACK_COUNT):
            f_y = (shared.REGION_EDITOR_TRACK_HEIGHT *
                (i2 + 1)) + _shared.REGION_EDITOR_HEADER_HEIGHT
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
        if a_point.index not in shared.TRACK_PANEL.plugin_uid_map:
            print("{} not in {}".format(
                a_point.index, shared.TRACK_PANEL.plugin_uid_map))
            return
        f_track = shared.TRACK_PANEL.plugin_uid_map[a_point.index]
        f_min = (f_track *
            shared.REGION_EDITOR_TRACK_HEIGHT) + _shared.REGION_EDITOR_HEADER_HEIGHT
        f_max = (
            f_min
            +
            shared.REGION_EDITOR_TRACK_HEIGHT
            -
            _shared.ATM_POINT_DIAMETER
        )
        f_item = SeqAtmItem(
            a_point, self.automation_save_callback, f_min, f_max)
        self.scene.addItem(f_item)
        f_item.setPos(self.get_pos_from_point(a_point))
        self.automation_points.append(f_item)
        if str(a_point) in self.selected_point_strings:
            f_item.setSelected(True)
        return f_item

    def get_pos_from_point(self, a_point):
        f_track_height = (
            shared.REGION_EDITOR_TRACK_HEIGHT
            -
            _shared.ATM_POINT_DIAMETER
        )
        f_track = shared.TRACK_PANEL.plugin_uid_map[a_point.index]
        return QtCore.QPointF(
            (a_point.beat * _shared.SEQUENCER_PX_PER_BEAT),
            (f_track_height * (1.0 - (a_point.cc_val / 127.0))) +
            (shared.REGION_EDITOR_TRACK_HEIGHT * f_track) +
            _shared.REGION_EDITOR_HEADER_HEIGHT)

    def automation_save_callback(self, a_open=True):
        shared.PROJECT.save_atm_region(shared.ATM_REGION)
        if a_open:
            self.open_region()

