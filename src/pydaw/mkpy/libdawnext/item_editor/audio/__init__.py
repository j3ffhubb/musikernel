"""

"""
from . import _shared
from ..abstract import AbstractItemEditor
from mkpy import libmk
from mkpy.libdawnext import project, shared
from mkpy.libdawnext.filedragdrop import FileDragDropper
from mkpy.libdawnext.project import *
from mkpy.libdawnext.shared import *
from mkpy.libmk import mk_project
from mkpy.libpydaw import (
    pydaw_util,
    pydaw_widgets,
)
from mkpy.libpydaw.pydaw_util import *
from mkpy.libpydaw.translate import _
from mkpy.mkqt import *


PAINTER_PATH_CACHE = {}


LAST_AUDIO_ITEM_DIR = global_home

def global_paif_val_callback(a_port, a_val):
    if (
        shared.CURRENT_ITEM is not None
        and
        _shared.CURRENT_AUDIO_ITEM_INDEX is not None
    ):
        shared.PROJECT.IPC.pydaw_audio_per_item_fx(
            shared.CURRENT_ITEM.uid,
            _shared.CURRENT_AUDIO_ITEM_INDEX,
            a_port,
            a_val,
        )

def global_paif_rel_callback(a_port, a_val):
    if (
        shared.CURRENT_ITEM is not None
        and
        _shared.CURRENT_AUDIO_ITEM_INDEX is not None
    ):
        f_index_list = shared.AUDIO_SEQ_WIDGET.modulex.get_list()
        shared.CURRENT_ITEM.set_row(
            _shared.CURRENT_AUDIO_ITEM_INDEX,
            f_index_list,
        )
        shared.PROJECT.save_item(
            shared.CURRENT_ITEM_NAME,
            shared.CURRENT_ITEM,
        )

class AudioSeqItem(pydaw_widgets.QGraphicsRectItemNDL):
    """ This is an individual audio item within the AudioItemSeq """
    def __init__(self, a_track_num, a_audio_item, a_graph):
        QGraphicsRectItem.__init__(self)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemClipsChildrenToShape)

        self.sample_length = a_graph.length_in_seconds
        self.graph_object = a_graph
        self.audio_item = a_audio_item
        self.orig_string = str(a_audio_item)
        self.track_num = a_track_num

        f_uid = self.audio_item.uid
        if f_uid in PAINTER_PATH_CACHE:
            self.painter_paths = PAINTER_PATH_CACHE[f_uid]
        else:
            self.painter_paths = a_graph.create_sample_graph(True)
            PAINTER_PATH_CACHE[f_uid] = self.painter_paths

        self.y_inc = shared.AUDIO_ITEM_HEIGHT / len(self.painter_paths)
        f_y_pos = 0.0
        self.path_items = []
        for f_painter_path in self.painter_paths:
            f_path_item = QGraphicsPathItem(f_painter_path)
            f_path_item.setBrush(QtCore.Qt.darkGray)
            f_path_item.setPen(shared.NO_PEN)
            f_path_item.setParentItem(self)
            f_path_item.mapToParent(0.0, 0.0)
            self.path_items.append(f_path_item)
            f_y_pos += self.y_inc
        f_file_name = libmk.PROJECT.get_wav_name_by_uid(
            self.audio_item.uid)
        f_file_name = libmk.PROJECT.timestretch_lookup_orig_path(
            f_file_name)
        f_name_arr = f_file_name.rsplit("/", 1)
        f_name = f_name_arr[-1]
        self.label = QGraphicsSimpleTextItem(f_name, parent=self)
        self.label.setPos(10, (shared.AUDIO_ITEM_HEIGHT * 0.5) -
            (self.label.boundingRect().height() * 0.5))
        self.label.setFlag(QGraphicsItem.ItemIgnoresTransformations)

        self.start_handle = QGraphicsRectItem(parent=self)
        self.start_handle.setAcceptHoverEvents(True)
        self.start_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.start_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.start_handle.setRect(
            QtCore.QRectF(0.0, 0.0, shared.AUDIO_ITEM_HANDLE_SIZE,
                          shared.AUDIO_ITEM_HANDLE_HEIGHT))
        self.start_handle.mousePressEvent = self.start_handle_mouseClickEvent
        self.start_handle_line = QGraphicsLineItem(
            0.0, shared.AUDIO_ITEM_HANDLE_HEIGHT, 0.0,
            (shared.AUDIO_ITEM_HEIGHT * -1.0) + shared.AUDIO_ITEM_HANDLE_HEIGHT,
            self.start_handle)

        self.start_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)

        self.length_handle = QGraphicsRectItem(parent=self)
        self.length_handle.setAcceptHoverEvents(True)
        self.length_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.length_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.length_handle.setRect(
            QtCore.QRectF(0.0, 0.0, shared.AUDIO_ITEM_HANDLE_SIZE,
                          shared.AUDIO_ITEM_HANDLE_HEIGHT))
        self.length_handle.mousePressEvent = self.length_handle_mouseClickEvent
        self.length_handle_line = QGraphicsLineItem(
            shared.AUDIO_ITEM_HANDLE_SIZE, shared.AUDIO_ITEM_HANDLE_HEIGHT,
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (shared.AUDIO_ITEM_HEIGHT * -1.0) + shared.AUDIO_ITEM_HANDLE_HEIGHT,
            self.length_handle)

        self.fade_in_handle = QGraphicsRectItem(parent=self)
        self.fade_in_handle.setAcceptHoverEvents(True)
        self.fade_in_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.fade_in_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.fade_in_handle.setRect(
            QtCore.QRectF(0.0, 0.0, shared.AUDIO_ITEM_HANDLE_SIZE,
                          shared.AUDIO_ITEM_HANDLE_HEIGHT))
        self.fade_in_handle.mousePressEvent = \
            self.fade_in_handle_mouseClickEvent
        self.fade_in_handle_line = QGraphicsLineItem(
            0.0, 0.0, 0.0, 0.0, self)

        self.fade_out_handle = QGraphicsRectItem(parent=self)
        self.fade_out_handle.setAcceptHoverEvents(True)
        self.fade_out_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.fade_out_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.fade_out_handle.setRect(
            QtCore.QRectF(0.0, 0.0, shared.AUDIO_ITEM_HANDLE_SIZE,
                          shared.AUDIO_ITEM_HANDLE_HEIGHT))
        self.fade_out_handle.mousePressEvent = \
            self.fade_out_handle_mouseClickEvent
        self.fade_out_handle_line = QGraphicsLineItem(
            0.0, 0.0, 0.0, 0.0, self)

        self.stretch_handle = QGraphicsRectItem(parent=self)
        self.stretch_handle.setAcceptHoverEvents(True)
        self.stretch_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.stretch_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.stretch_handle.setRect(
            QtCore.QRectF(0.0, 0.0, shared.AUDIO_ITEM_HANDLE_SIZE,
                          shared.AUDIO_ITEM_HANDLE_HEIGHT))
        self.stretch_handle.mousePressEvent = \
            self.stretch_handle_mouseClickEvent
        self.stretch_handle_line = QGraphicsLineItem(
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5) - (shared.AUDIO_ITEM_HEIGHT * 0.5),
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (shared.AUDIO_ITEM_HEIGHT * 0.5) + (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5),
            self.stretch_handle)
        self.stretch_handle.hide()

        self.split_line = QGraphicsLineItem(
            0.0, 0.0, 0.0, shared.AUDIO_ITEM_HEIGHT, self)
        self.split_line.mapFromParent(0.0, 0.0)
        self.split_line.hide()
        self.split_line_is_shown = False

        self.setAcceptHoverEvents(True)

        self.is_start_resizing = False
        self.is_resizing = False
        self.is_copying = False
        self.is_fading_in = False
        self.is_fading_out = False
        self.is_stretching = False
        self.set_brush()
        self.waveforms_scaled = False
        self.is_amp_curving = False
        self.is_amp_dragging = False
        self.event_pos_orig = None
        self.width_orig = None
        self.vol_linear = pydaw_db_to_lin(self.audio_item.vol)
        self.quantize_offset = 0.0
        if libmk.TOOLTIPS_ENABLED:
            self.set_tooltips(True)
        self.draw()

    def generic_hoverEnterEvent(self, a_event):
        QApplication.setOverrideCursor(
            QCursor(QtCore.Qt.SizeHorCursor))

    def generic_hoverLeaveEvent(self, a_event):
        QApplication.restoreOverrideCursor()

    def draw(self):
        f_temp_seconds = self.sample_length

        if self.audio_item.time_stretch_mode == 1 and \
        (self.audio_item.pitch_shift_end == self.audio_item.pitch_shift):
            f_temp_seconds /= pydaw_pitch_to_ratio(self.audio_item.pitch_shift)
        elif self.audio_item.time_stretch_mode == 2 and \
        (self.audio_item.timestretch_amt_end ==
        self.audio_item.timestretch_amt):
            f_temp_seconds *= self.audio_item.timestretch_amt

        f_start = self.audio_item.start_beat
        f_start *= shared.AUDIO_PX_PER_BEAT

        f_length_seconds = pydaw_seconds_to_beats(
            f_temp_seconds) * shared.AUDIO_PX_PER_BEAT
        self.length_seconds_orig_px = f_length_seconds
        self.rect_orig = QtCore.QRectF(
            0.0, 0.0, f_length_seconds, shared.AUDIO_ITEM_HEIGHT)
        self.length_px_start = (self.audio_item.sample_start *
            0.001 * f_length_seconds)
        self.length_px_minus_start = f_length_seconds - self.length_px_start
        self.length_px_minus_end = (self.audio_item.sample_end *
            0.001 * f_length_seconds)
        f_length = self.length_px_minus_end - self.length_px_start

        f_track_num = (shared.AUDIO_RULER_HEIGHT +
            shared.AUDIO_ITEM_HEIGHT * self.audio_item.lane_num)

        f_fade_in = self.audio_item.fade_in * 0.001
        f_fade_out = self.audio_item.fade_out * 0.001
        self.setRect(0.0, 0.0, f_length, shared.AUDIO_ITEM_HEIGHT)
        f_fade_in_handle_pos = (f_length * f_fade_in)
        f_fade_in_handle_pos = pydaw_clip_value(
            f_fade_in_handle_pos, 0.0, (f_length - 6.0))
        f_fade_out_handle_pos = \
            (f_length * f_fade_out) - shared.AUDIO_ITEM_HANDLE_SIZE
        f_fade_out_handle_pos = pydaw_clip_value(
            f_fade_out_handle_pos, (f_fade_in_handle_pos + 6.0), f_length)
        self.fade_in_handle.setPos(f_fade_in_handle_pos, 0.0)
        self.fade_out_handle.setPos(f_fade_out_handle_pos, 0.0)
        self.update_fade_in_line()
        self.update_fade_out_line()
        self.setPos(f_start, f_track_num)
        self.is_moving = False
        if self.audio_item.time_stretch_mode >= 3 or \
        (self.audio_item.time_stretch_mode == 2 and \
        (self.audio_item.timestretch_amt_end ==
        self.audio_item.timestretch_amt)):
            self.stretch_width_default = \
                f_length / self.audio_item.timestretch_amt

        self.sample_start_offset_px = (self.audio_item.sample_start *
            -0.001 * self.length_seconds_orig_px)

        self.start_handle_scene_min = f_start + self.sample_start_offset_px
        self.start_handle_scene_max = (self.start_handle_scene_min +
            self.length_seconds_orig_px)

        if not self.waveforms_scaled:
            f_channels = len(self.painter_paths)
            f_i_inc = 1.0 / f_channels
            f_i = f_i_inc
            f_y_inc = 0.0
            # Kludge to fix the problem, there must be a better way...
            if f_channels == 1:
                f_y_offset = \
                    (1.0 - self.vol_linear) * (shared.AUDIO_ITEM_HEIGHT * 0.5)
            else:
                f_y_offset = (1.0 - self.vol_linear) * self.y_inc * f_i_inc
            for f_path_item in self.path_items:
                if self.audio_item.reversed:
                    f_path_item.setPos(
                        self.sample_start_offset_px +
                        self.length_seconds_orig_px,
                        self.y_inc + (f_y_offset * -1.0) + (f_y_inc * f_i))
                    f_path_item.setRotation(-180.0)
                else:
                    f_path_item.setPos(
                        self.sample_start_offset_px,
                        f_y_offset + (f_y_inc * f_i))
                f_x_scale, f_y_scale = pydaw_util.scale_to_rect(
                    mk_project.pydaw_audio_item_scene_rect, self.rect_orig)
                f_y_scale *= self.vol_linear
                f_scale_transform = QTransform()
                f_scale_transform.scale(f_x_scale, f_y_scale)
                f_path_item.setTransform(f_scale_transform)
                f_i += f_i_inc
                f_y_inc += self.y_inc
        self.waveforms_scaled = True

        self.length_handle.setPos(
            f_length - shared.AUDIO_ITEM_HANDLE_SIZE,
            shared.AUDIO_ITEM_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT)
        self.start_handle.setPos(
            0.0, shared.AUDIO_ITEM_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT)
        if self.audio_item.time_stretch_mode >= 2 and \
        (((self.audio_item.time_stretch_mode != 5) and \
        (self.audio_item.time_stretch_mode != 2)) \
        or (self.audio_item.timestretch_amt_end ==
        self.audio_item.timestretch_amt)):
            self.stretch_handle.show()
            self.stretch_handle.setPos(
                f_length - shared.AUDIO_ITEM_HANDLE_SIZE,
                (shared.AUDIO_ITEM_HEIGHT * 0.5) - (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5))

    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip(mk_strings.AudioSeqItem)
            self.start_handle.setToolTip(
                _("Use this handle to resize the item by changing "
                "the start point."))
            self.length_handle.setToolTip(
                _("Use this handle to resize the item by "
                "changing the end point."))
            self.fade_in_handle.setToolTip(
                _("Use this handle to change the fade in."))
            self.fade_out_handle.setToolTip(
                _("Use this handle to change the fade out."))
            self.stretch_handle.setToolTip(
                _("Use this handle to resize the item by "
                "time-stretching it."))
        else:
            self.setToolTip("")
            self.start_handle.setToolTip("")
            self.length_handle.setToolTip("")
            self.fade_in_handle.setToolTip("")
            self.fade_out_handle.setToolTip("")
            self.stretch_handle.setToolTip("")

    def clip_at_region_end(self):
        f_max_x = shared.CURRENT_ITEM_LEN * shared.AUDIO_PX_PER_BEAT
        f_pos_x = self.pos().x()
        f_end = f_pos_x + self.rect().width()
        if f_end > f_max_x:
            f_end_px = f_max_x - f_pos_x
            self.setRect(0.0, 0.0, f_end_px, shared.AUDIO_ITEM_HEIGHT)
            self.audio_item.sample_end = \
                ((self.rect().width() + self.length_px_start) /
                self.length_seconds_orig_px) * 1000.0
            self.audio_item.sample_end = pydaw_util.pydaw_clip_value(
                self.audio_item.sample_end, 1.0, 1000.0, True)
            self.draw()
            return True
        else:
            return False

    def set_brush(self, a_index=None):
        if self.isSelected():
            self.setBrush(shared.SELECTED_ITEM_COLOR)
            self.start_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.length_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.fade_in_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.fade_out_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.stretch_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.split_line.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)

            self.start_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)
            self.length_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)
            self.fade_in_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)
            self.fade_out_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)
            self.stretch_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)

            self.label.setBrush(QtCore.Qt.darkGray)
            self.start_handle.setBrush(shared.AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.length_handle.setBrush(shared.AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.fade_in_handle.setBrush(shared.AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.fade_out_handle.setBrush(shared.AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.stretch_handle.setBrush(shared.AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
        else:
            self.start_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.length_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.fade_in_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.fade_out_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.stretch_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.split_line.setPen(shared.AUDIO_ITEM_HANDLE_PEN)

            self.start_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)
            self.length_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)
            self.fade_in_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)
            self.fade_out_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)
            self.stretch_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)

            self.label.setBrush(QtCore.Qt.white)
            self.start_handle.setBrush(shared.AUDIO_ITEM_HANDLE_BRUSH)
            self.length_handle.setBrush(shared.AUDIO_ITEM_HANDLE_BRUSH)
            self.fade_in_handle.setBrush(shared.AUDIO_ITEM_HANDLE_BRUSH)
            self.fade_out_handle.setBrush(shared.AUDIO_ITEM_HANDLE_BRUSH)
            self.stretch_handle.setBrush(shared.AUDIO_ITEM_HANDLE_BRUSH)
            if a_index is None:
                self.setBrush(libmk.DEFAULT_TRACK_COLORS[
                self.audio_item.lane_num % len(libmk.DEFAULT_TRACK_COLORS)])
            else:
                self.setBrush(libmk.DEFAULT_TRACK_COLORS[
                    a_index % len(libmk.DEFAULT_TRACK_COLORS)])

    def pos_to_musical_time(self, a_pos):
        return a_pos / shared.AUDIO_PX_PER_BEAT

    def start_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.length_handle, a_event)
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.min_start = f_item.pos().x() * -1.0
                f_item.is_start_resizing = True
                f_item.setFlag(QGraphicsItem.ItemClipsChildrenToShape,
                               False)

    def length_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.length_handle, a_event)
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.is_resizing = True
                f_item.setFlag(QGraphicsItem.ItemClipsChildrenToShape,
                               False)

    def fade_in_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.fade_in_handle, a_event)
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.is_fading_in = True

    def fade_out_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.fade_out_handle, a_event)
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.is_fading_out = True

    def stretch_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.stretch_handle, a_event)
        f_max_region_pos = shared.AUDIO_PX_PER_BEAT * shared.CURRENT_ITEM_LEN
        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected() and \
            f_item.audio_item.time_stretch_mode >= 2:
                f_item.is_stretching = True
                f_item.max_stretch = f_max_region_pos - f_item.pos().x()
                f_item.setFlag(
                    QGraphicsItem.ItemClipsChildrenToShape, False)
                #for f_path in f_item.path_items:
                #    f_path.hide()

    def check_selected_status(self):
        """ If a handle is clicked and not selected, clear the selection
            and select only this item
        """
        if not self.isSelected():
            shared.AUDIO_SEQ.scene.clearSelection()
            self.setSelected(True)

    def copy_as_cc_automation(self):
        shared.CC_EDITOR.clipboard = en_project.envelope_to_automation(
            self.graph_object, True, TRANSPORT.tempo_spinbox.value())

    def copy_as_pb_automation(self):
        shared.PB_EDITOR.clipboard = en_project.envelope_to_automation(
            self.graph_object, False, TRANSPORT.tempo_spinbox.value())

    def copy_as_notes(self):
        shared.PIANO_ROLL_EDITOR.clipboard = en_project.envelope_to_notes(
            self.graph_object, TRANSPORT.tempo_spinbox.value())

    def crisp_menu_triggered(self, a_action):
        f_index = CRISPNESS_SETTINGS.index(a_action.crisp_mode)
        f_list = [x.audio_item for x in shared.AUDIO_SEQ.get_selected() if
            x.audio_item.time_stretch_mode in (3, 4)]
        for f_item in f_list:
            f_item.crispness = f_index
        self.timestretch_items(f_list)

    def timestretch_items(self, a_list):
        f_stretched_items = []
        for f_item in a_list:
            if f_item.time_stretch_mode >= 3:
                f_ts_result = libmk.PROJECT.timestretch_audio_item(f_item)
                if f_ts_result is not None:
                    f_stretched_items.append(f_ts_result)

        libmk.PROJECT.save_stretch_dicts()

        for f_stretch_item in f_stretched_items:
            f_stretch_item[2].wait()
            libmk.PROJECT.get_wav_uid_by_name(
                f_stretch_item[0], a_uid=f_stretch_item[1])
        for f_audio_item in shared.AUDIO_SEQ.get_selected():
            f_new_graph = libmk.PROJECT.get_sample_graph_by_uid(
                f_audio_item.audio_item.uid)
            f_audio_item.audio_item.clip_at_region_end(
                pydaw_get_current_region_length(),
                shared.CURRENT_REGION.get_tempo_at_pos(
                    shared.CURRENT_ITEM_REF.start_beat,
                ),
                f_new_graph.length_in_seconds)

        shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
        shared.PROJECT.commit(_("Change timestretch mode for audio item(s)"))
        global_open_audio_items()

    def set_paif_for_all_instance(self):
        f_paif = shared.PROJECT.get_audio_per_item_fx_region(
            shared.CURRENT_REGION.uid,
        )
        f_paif_row = f_paif.get_row(self.track_num)
        shared.PROJECT.set_paif_for_all_audio_items(
            self.audio_item.uid, f_paif_row)

    def set_fades_for_all_instances(self):
        shared.PROJECT.set_fades_for_all_audio_items(self.audio_item)
        global_open_audio_items()

    def set_vol_for_all_instances(self):
        def ok_handler():
            f_index = f_reverse_combobox.currentIndex()
            f_reverse_val = None
            if f_index == 1:
                f_reverse_val = False
            elif f_index == 2:
                f_reverse_val = True
            shared.PROJECT.set_vol_for_all_audio_items(
                self.audio_item.uid, get_vol(), f_reverse_val,
                f_same_vol_checkbox.isChecked(), self.audio_item.vol)
            f_dialog.close()
            global_open_audio_items()

        def cancel_handler():
            f_dialog.close()

        def vol_changed(a_val=None):
            f_vol_label.setText("{}dB".format(get_vol()))

        def get_vol():
            return round(f_vol_slider.value() * 0.1, 1)

        f_dialog = QDialog(shared.MAIN_WINDOW)
        f_dialog.setWindowTitle(_("Set Volume for all Instance of File"))
        f_layout = QGridLayout(f_dialog)
        f_layout.setAlignment(QtCore.Qt.AlignCenter)
        f_vol_slider = QSlider(QtCore.Qt.Vertical)
        f_vol_slider.setRange(-240, 240)
        f_vol_slider.setMinimumHeight(360)
        f_vol_slider.valueChanged.connect(vol_changed)
        f_layout.addWidget(f_vol_slider, 0, 1, QtCore.Qt.AlignCenter)
        f_vol_label = QLabel("0dB")
        f_layout.addWidget(f_vol_label, 1, 1)
        f_vol_slider.setValue(self.audio_item.vol)
        f_reverse_combobox = QComboBox()
        f_reverse_combobox.addItems(
            [_("Either"), _("Not-Reversed"), _("Reversed")])
        f_reverse_combobox.setMinimumWidth(105)
        f_layout.addWidget(QLabel(_("Reversed Items?")), 2, 0)
        f_layout.addWidget(f_reverse_combobox, 2, 1)
        f_same_vol_checkbox = QCheckBox(
            _("Only items with same volume?"))
        f_layout.addWidget(f_same_vol_checkbox, 3, 1)
        f_ok_cancel_layout = QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout, 10, 1)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_handler)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.exec_()

    def normalize(self, a_value):
        f_val = self.graph_object.normalize(a_value)
        self.audio_item.vol = f_val

    def get_file_path(self):
        return libmk.PROJECT.get_wav_path_by_uid(self.audio_item.uid)

    def mousePressEvent(self, a_event):
        if libmk.IS_PLAYING:
            return

        if a_event.modifiers() == (QtCore.Qt.AltModifier |
        QtCore.Qt.ShiftModifier):
            self.setSelected((not self.isSelected()))
            return

        if not self.isSelected():
            shared.AUDIO_SEQ.scene.clearSelection()
            self.setSelected(True)

        if a_event.button() == QtCore.Qt.RightButton:
            _shared.CURRENT_ITEM = self
            item_context_menu.show()
            return

        if shared.EDITOR_MODE == shared.EDITOR_MODE_SPLIT:
            f_item = self.audio_item
            f_item_old = f_item.clone()
            f_item.fade_in = 0.0
            f_item_old.fade_out = 999.0
            f_width_percent = a_event.pos().x() / self.rect().width()
            f_item.fade_out = pydaw_clip_value(
                f_item.fade_out, (f_item.fade_in + 90.0), 999.0, True)
            f_item_old.fade_in /= f_width_percent
            f_item_old.fade_in = pydaw_clip_value(
                f_item_old.fade_in, 0.0, (f_item_old.fade_out - 90.0), True)

            f_index = shared.CURRENT_ITEM.get_next_index()
            if f_index == -1:
                QMessageBox.warning(
                    self, _("Error"),
                    _("No more available audio item slots, max per region "
                    "is {}").format(MAX_AUDIO_ITEM_COUNT))
                return
            else:
                shared.CURRENT_ITEM.add_item(f_index, f_item_old)
                f_per_item_fx = shared.CURRENT_ITEM.get_row(self.track_num)
                if f_per_item_fx is not None:
                    shared.CURRENT_ITEM.set_row(f_index, f_per_item_fx)

            f_event_pos = a_event.pos().x()
            # for items that are not quantized
            f_pos = f_event_pos - (f_event_pos - self.quantize(f_event_pos))
            f_scene_pos = self.quantize(a_event.scenePos().x())
            f_musical_pos = self.pos_to_musical_time(f_scene_pos)
            f_sample_shown = f_item.sample_end - f_item.sample_start
            f_sample_rect_pos = f_pos / self.rect().width()
            f_item.sample_start = \
                (f_sample_rect_pos * f_sample_shown) + f_item.sample_start
            f_item.sample_start = pydaw_clip_value(
                f_item.sample_start, 0.0, 999.0, True)
            f_item.start_beat = f_musical_pos
            f_item_old.sample_end = f_item.sample_start
            shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
            shared.PROJECT.commit(_("Split audio item"))
            global_open_audio_items(True)
        elif a_event.modifiers() == \
        QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier:
            self.is_amp_dragging = True
        elif a_event.modifiers() == \
        QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier:
            self.is_amp_curving = True
            f_list = [((x.audio_item.start_bar * 4.0) +
                x.audio_item.start_beat)
                for x in shared.AUDIO_SEQ.audio_items if x.isSelected()]
            f_list.sort()
            self.vc_start = f_list[0]
            self.vc_mid = (self.audio_item.start_bar *
                4.0) + self.audio_item.start_beat
            self.vc_end = f_list[-1]
        else:
            QGraphicsRectItem.mousePressEvent(self, a_event)
            self.event_pos_orig = a_event.pos().x()
            for f_item in shared.AUDIO_SEQ.get_selected():
                f_item.setZValue(2400.0)
                f_item_pos = f_item.pos().x()
                f_item.quantize_offset = \
                    f_item_pos - f_item.quantize_all(f_item_pos)
                if a_event.modifiers() == QtCore.Qt.ControlModifier:
                    f_item.is_copying = True
                    f_item.width_orig = f_item.rect().width()
                    f_item.per_item_fx = shared.CURRENT_ITEM.get_row(
                        f_item.track_num)
                    shared.AUDIO_SEQ.draw_item(
                        f_item.track_num, f_item.audio_item,
                        f_item.graph_object)
                if self.is_fading_out:
                    f_item.fade_orig_pos = f_item.fade_out_handle.pos().x()
                elif self.is_fading_in:
                    f_item.fade_orig_pos = f_item.fade_in_handle.pos().x()
                if self.is_start_resizing:
                    f_item.width_orig = 0.0
                else:
                    f_item.width_orig = f_item.rect().width()
        if self.is_amp_curving or self.is_amp_dragging:
            a_event.setAccepted(True)
            self.setSelected(True)
            self.event_pos_orig = a_event.pos().x()
            QGraphicsRectItem.mousePressEvent(self, a_event)
            self.orig_y = a_event.pos().y()
            QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)
            for f_item in shared.AUDIO_SEQ.get_selected():
                f_item.orig_value = f_item.audio_item.vol
                f_item.add_vol_line()

    def hoverEnterEvent(self, a_event):
        f_item_pos = self.pos().x()
        self.quantize_offset = f_item_pos - self.quantize_all(f_item_pos)

    def hoverMoveEvent(self, a_event):
        if shared.EDITOR_MODE == shared.EDITOR_MODE_SPLIT:
            if not self.split_line_is_shown:
                self.split_line_is_shown = True
                self.split_line.show()
            f_x = a_event.pos().x()
            f_x = self.quantize_all(f_x)
            f_x -= self.quantize_offset
            self.split_line.setPos(f_x, 0.0)
        else:
            if self.split_line_is_shown:
                self.split_line_is_shown = False
                self.split_line.hide()

    def hoverLeaveEvent(self, a_event):
        if self.split_line_is_shown:
            self.split_line_is_shown = False
            self.split_line.hide()

    def y_pos_to_lane_number(self, a_y_pos):
        f_lane_num = int((a_y_pos - shared.AUDIO_RULER_HEIGHT) / shared.AUDIO_ITEM_HEIGHT)
        f_lane_num = pydaw_clip_value(
            f_lane_num, 0, shared.AUDIO_ITEM_MAX_LANE)
        f_y_pos = (f_lane_num * shared.AUDIO_ITEM_HEIGHT) + shared.AUDIO_RULER_HEIGHT
        return f_lane_num, f_y_pos

    def lane_number_to_y_pos(self, a_lane_num):
        a_lane_num = pydaw_util.pydaw_clip_value(
            a_lane_num,
            0,
            project.TRACK_COUNT_ALL,
        )
        return (a_lane_num * shared.AUDIO_ITEM_HEIGHT) + shared.AUDIO_RULER_HEIGHT

    def quantize_all(self, a_x):
        f_x = a_x
        if shared.AUDIO_QUANTIZE:
            f_x = round(f_x / shared.AUDIO_QUANTIZE_PX) * shared.AUDIO_QUANTIZE_PX
        return f_x

    def quantize(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        if shared.AUDIO_QUANTIZE and f_x < shared.AUDIO_QUANTIZE_PX:
            f_x = shared.AUDIO_QUANTIZE_PX
        return f_x

    def quantize_start(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        if f_x >= self.length_handle.pos().x():
            f_x -= shared.AUDIO_QUANTIZE_PX
        return f_x

    def quantize_scene(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        return f_x

    def update_fade_in_line(self):
        f_pos = self.fade_in_handle.pos()
        self.fade_in_handle_line.setLine(
            f_pos.x(), 0.0, 0.0, shared.AUDIO_ITEM_HEIGHT)

    def update_fade_out_line(self):
        f_pos = self.fade_out_handle.pos()
        self.fade_out_handle_line.setLine(
            f_pos.x() + shared.AUDIO_ITEM_HANDLE_SIZE, 0.0,
            self.rect().width(), shared.AUDIO_ITEM_HEIGHT)

    def add_vol_line(self):
        self.vol_line = QGraphicsLineItem(
            0.0, 0.0, self.rect().width(), 0.0, self)
        self.vol_line.setPen(QPen(QtCore.Qt.red, 2.0))
        self.set_vol_line()

    def set_vol_line(self):
        f_pos = (float(48 - (self.audio_item.vol + 24))
            * 0.020833333) * shared.AUDIO_ITEM_HEIGHT # 1.0 / 48.0
        self.vol_line.setPos(0, f_pos)
        self.label.setText("{}dB".format(self.audio_item.vol))

    def mouseMoveEvent(self, a_event):
        if libmk.IS_PLAYING or self.event_pos_orig is None:
            return
        if self.is_amp_curving or self.is_amp_dragging:
            f_pos = a_event.pos()
            f_y = f_pos.y()
            f_diff_y = self.orig_y - f_y
            f_val = (f_diff_y * 0.05)
        f_event_pos = a_event.pos().x()
        f_event_diff = f_event_pos - self.event_pos_orig
        if self.is_resizing:
            for f_item in shared.AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_x = f_item.width_orig + f_event_diff + \
                        f_item.quantize_offset
                    f_x = pydaw_clip_value(
                        f_x, shared.AUDIO_ITEM_HANDLE_SIZE,
                        f_item.length_px_minus_start)
                    if f_x < f_item.length_px_minus_start:
                        f_x = f_item.quantize(f_x)
                        f_x -= f_item.quantize_offset
                    f_item.length_handle.setPos(
                        f_x - shared.AUDIO_ITEM_HANDLE_SIZE,
                        shared.AUDIO_ITEM_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT)
        elif self.is_start_resizing:
            for f_item in shared.AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_x = f_item.width_orig + f_event_diff + \
                        f_item.quantize_offset
                    f_x = pydaw_clip_value(
                        f_x, f_item.sample_start_offset_px,
                        f_item.length_handle.pos().x())
                    f_x = pydaw_clip_min(f_x, f_item.min_start)
                    if f_x > f_item.min_start:
                        f_x = f_item.quantize_start(f_x)
                        f_x -= f_item.quantize_offset
                    f_item.start_handle.setPos(
                        f_x, shared.AUDIO_ITEM_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT)
        elif self.is_fading_in:
            for f_item in shared.AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    #f_x = f_event_pos #f_item.width_orig + f_event_diff
                    f_x = f_item.fade_orig_pos + f_event_diff
                    f_x = pydaw_clip_value(
                        f_x, 0.0, f_item.fade_out_handle.pos().x() - 4.0)
                    f_item.fade_in_handle.setPos(f_x, 0.0)
                    f_item.update_fade_in_line()
        elif self.is_fading_out:
            for f_item in shared.AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_x = f_item.fade_orig_pos + f_event_diff
                    f_x = pydaw_clip_value(
                        f_x, f_item.fade_in_handle.pos().x() + 4.0,
                        f_item.width_orig - shared.AUDIO_ITEM_HANDLE_SIZE)
                    f_item.fade_out_handle.setPos(f_x, 0.0)
                    f_item.update_fade_out_line()
        elif self.is_stretching:
            for f_item in shared.AUDIO_SEQ.audio_items:
                if f_item.isSelected() and \
                f_item.audio_item.time_stretch_mode >= 2:
                    f_x = f_item.width_orig + f_event_diff + \
                        f_item.quantize_offset
                    f_x = pydaw_clip_value(
                        f_x, f_item.stretch_width_default * 0.1,
                        f_item.stretch_width_default * 200.0)
                    f_x = pydaw_clip_max(f_x, f_item.max_stretch)
                    f_x = f_item.quantize(f_x)
                    f_x -= f_item.quantize_offset
                    f_item.stretch_handle.setPos(
                        f_x - shared.AUDIO_ITEM_HANDLE_SIZE,
                        (shared.AUDIO_ITEM_HEIGHT * 0.5) -
                        (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5))
        elif self.is_amp_dragging:
            for f_item in shared.AUDIO_SEQ.get_selected():
                f_new_vel = pydaw_util.pydaw_clip_value(
                    f_val + f_item.orig_value, -24.0, 24.0)
                f_new_vel = round(f_new_vel, 1)
                f_item.audio_item.vol = f_new_vel
                f_item.set_vol_line()
        elif self.is_amp_curving:
            shared.AUDIO_SEQ.setUpdatesEnabled(False)
            for f_item in shared.AUDIO_SEQ.get_selected():
                f_start = ((f_item.audio_item.start_bar * 4.0) +
                    f_item.audio_item.start_beat)
                if f_start == self.vc_mid:
                    f_new_vel = f_val + f_item.orig_value
                else:
                    if f_start > self.vc_mid:
                        f_frac =  (f_start -
                            self.vc_mid) / (self.vc_end - self.vc_mid)
                        f_new_vel = pydaw_util.linear_interpolate(
                            f_val, 0.3 * f_val, f_frac)
                    else:
                        f_frac = (f_start -
                            self.vc_start) / (self.vc_mid - self.vc_start)
                        f_new_vel = pydaw_util.linear_interpolate(
                            0.3 * f_val, f_val, f_frac)
                    f_new_vel += f_item.orig_value
                f_new_vel = pydaw_util.pydaw_clip_value(f_new_vel, -24.0, 24.0)
                f_new_vel = round(f_new_vel, 1)
                f_item.audio_item.vol = f_new_vel
                f_item.set_vol_line()
            shared.AUDIO_SEQ.setUpdatesEnabled(True)
            shared.AUDIO_SEQ.update()
        else:
            QGraphicsRectItem.mouseMoveEvent(self, a_event)
            if shared.AUDIO_QUANTIZE:
                f_max_x = (shared.CURRENT_ITEM_LEN *
                    shared.AUDIO_PX_PER_BEAT) - shared.AUDIO_QUANTIZE_PX
            else:
                f_max_x = (shared.CURRENT_ITEM_LEN *
                    shared.AUDIO_PX_PER_BEAT) - shared.AUDIO_ITEM_HANDLE_SIZE
            f_new_lane, f_ignored = self.y_pos_to_lane_number(
                a_event.scenePos().y())
            f_lane_offset = f_new_lane - self.audio_item.lane_num
            for f_item in shared.AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_pos_x = f_item.pos().x()
                    f_pos_x = pydaw_clip_value(f_pos_x, 0.0, f_max_x)
                    f_pos_x = f_item.quantize_scene(f_pos_x)
                    f_pos_y = self.lane_number_to_y_pos(
                        f_lane_offset + f_item.audio_item.lane_num)
                    f_item.setPos(f_pos_x, f_pos_y)
                    if not f_item.is_moving:
                        f_item.setGraphicsEffect(
                            QGraphicsOpacityEffect())
                        f_item.is_moving = True

    def mouseReleaseEvent(self, a_event):
        if libmk.IS_PLAYING or self.event_pos_orig is None:
            return
        QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        QApplication.restoreOverrideCursor()
        f_audio_items = shared.CURRENT_ITEM
        #Set to True when testing, set to False for better UI performance...
        f_reset_selection = True
        f_did_change = False
        f_was_stretching = False
        f_stretched_items = []
        f_event_pos = a_event.pos().x()
        f_event_diff = f_event_pos - self.event_pos_orig

        for f_audio_item in shared.AUDIO_SEQ.get_selected():
            f_item = f_audio_item.audio_item
            f_pos_x = f_audio_item.pos().x()
            if f_audio_item.is_resizing:
                f_x = f_audio_item.width_orig + f_event_diff + \
                    f_audio_item.quantize_offset
                f_x = pydaw_clip_value(
                    f_x, shared.AUDIO_ITEM_HANDLE_SIZE,
                    f_audio_item.length_px_minus_start)
                f_x = f_audio_item.quantize(f_x)
                f_x -= f_audio_item.quantize_offset
                f_audio_item.setRect(0.0, 0.0, f_x, shared.AUDIO_ITEM_HEIGHT)
                f_item.sample_end = ((f_audio_item.rect().width() +
                f_audio_item.length_px_start) /
                f_audio_item.length_seconds_orig_px) * 1000.0
                f_item.sample_end = pydaw_util.pydaw_clip_value(
                    f_item.sample_end, 1.0, 1000.0, True)
            elif f_audio_item.is_start_resizing:
                f_x = f_audio_item.start_handle.scenePos().x()
                f_x = pydaw_clip_min(f_x, 0.0)
                f_x = self.quantize_all(f_x)
                if f_x < f_audio_item.sample_start_offset_px:
                    f_x = f_audio_item.sample_start_offset_px
                f_start_result = self.pos_to_musical_time(f_x)
                f_item.start_beat = f_start_result
                f_item.sample_start = ((f_x -
                    f_audio_item.start_handle_scene_min) /
                    (f_audio_item.start_handle_scene_max -
                    f_audio_item.start_handle_scene_min)) * 1000.0
                f_item.sample_start = pydaw_clip_value(
                    f_item.sample_start, 0.0, 999.0, True)
            elif f_audio_item.is_fading_in:
                f_pos = f_audio_item.fade_in_handle.pos().x()
                f_val = (f_pos / f_audio_item.rect().width()) * 1000.0
                f_item.fade_in = pydaw_clip_value(f_val, 0.0, 997.0, True)
            elif f_audio_item.is_fading_out:
                f_pos = f_audio_item.fade_out_handle.pos().x()
                f_val = ((f_pos + shared.AUDIO_ITEM_HANDLE_SIZE) /
                    (f_audio_item.rect().width())) * 1000.0
                f_item.fade_out = pydaw_clip_value(f_val, 1.0, 998.0, True)
            elif f_audio_item.is_stretching and f_item.time_stretch_mode >= 2:
                f_reset_selection = True
                f_x = f_audio_item.width_orig + f_event_diff + \
                    f_audio_item.quantize_offset
                f_x = pydaw_clip_value(
                    f_x, f_audio_item.stretch_width_default * 0.1,
                    f_audio_item.stretch_width_default * 200.0)
                f_x = pydaw_clip_max(f_x, f_audio_item.max_stretch)
                f_x = f_audio_item.quantize(f_x)
                f_x -= f_audio_item.quantize_offset
                f_item.timestretch_amt = \
                    f_x / f_audio_item.stretch_width_default
                f_item.timestretch_amt_end = f_item.timestretch_amt
                if f_item.time_stretch_mode >= 3 and \
                f_audio_item.orig_string != str(f_item):
                    f_was_stretching = True
                    f_ts_result = libmk.PROJECT.timestretch_audio_item(f_item)
                    if f_ts_result is not None:
                        f_stretched_items.append(f_ts_result)
                f_audio_item.setRect(0.0, 0.0, f_x, shared.AUDIO_ITEM_HEIGHT)
            elif self.is_amp_curving or self.is_amp_dragging:
                f_did_change = True
            else:
                f_pos_y = f_audio_item.pos().y()
                if f_audio_item.is_copying:
                    f_reset_selection = True
                    f_item_old = f_item.clone()
                    f_index = f_audio_items.get_next_index()
                    if f_index == -1:
                        QMessageBox.warning(self, _("Error"),
                        _("No more available audio item slots, max per "
                        "region is {}").format(MAX_AUDIO_ITEM_COUNT))
                        break
                    else:
                        f_audio_items.add_item(f_index, f_item_old)
                        if f_audio_item.per_item_fx is not None:
                            shared.CURRENT_ITEM.set_row(
                                f_index, f_audio_item.per_item_fx)
                else:
                    f_audio_item.set_brush(f_item.lane_num)
                f_pos_x = self.quantize_all(f_pos_x)
                f_item.lane_num, f_pos_y = self.y_pos_to_lane_number(f_pos_y)
                f_audio_item.setPos(f_pos_x, f_pos_y)
                f_start_result = f_audio_item.pos_to_musical_time(f_pos_x)
                f_item.set_pos(0, f_start_result)
            f_audio_item.clip_at_region_end()
            f_item_str = str(f_item)
            if f_item_str != f_audio_item.orig_string:
                f_audio_item.orig_string = f_item_str
                f_did_change = True
                if not f_reset_selection:
                    f_audio_item.draw()
            f_audio_item.is_moving = False
            f_audio_item.is_resizing = False
            f_audio_item.is_start_resizing = False
            f_audio_item.is_copying = False
            f_audio_item.is_fading_in = False
            f_audio_item.is_fading_out = False
            f_audio_item.is_stretching = False
            f_audio_item.setGraphicsEffect(None)
            f_audio_item.setFlag(QGraphicsItem.ItemClipsChildrenToShape)
        if f_did_change:
            f_audio_items.deduplicate_items()
            if f_was_stretching:
                libmk.PROJECT.save_stretch_dicts()
                for f_stretch_item in f_stretched_items:
                    f_stretch_item[2].wait()
                    libmk.PROJECT.get_wav_uid_by_name(
                        f_stretch_item[0], a_uid=f_stretch_item[1])
#                for f_audio_item in shared.AUDIO_SEQ.get_selected():
#                    f_new_graph = libmk.PROJECT.get_sample_graph_by_uid(
#                        f_audio_item.audio_item.uid)
#                    f_audio_item.audio_item.clip_at_region_end(
#                        pydaw_get_current_region_length(),
#                        TRANSPORT.tempo_spinbox.value(),
#                        f_new_graph.length_in_seconds)
            shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
            shared.PROJECT.commit(_("Update audio items"))
        global_open_audio_items(f_reset_selection)


class AudioItemSeq(AbstractItemEditor):
    """ This is the QGraphicsView and QGraphicsScene for editing audio
        items within a SequencerItem on the "Items" tab.
    """
    def __init__(self):
        AbstractItemEditor.__init__(self)
        self.reset_line_lists()
        self.h_zoom = 1.0
        self.v_zoom = 1.0
        self.scene = QGraphicsScene(self)
        self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.scene.dropEvent = self.sceneDropEvent
        self.scene.dragEnterEvent = self.sceneDragEnterEvent
        self.scene.dragMoveEvent = self.sceneDragMoveEvent
        self.scene.contextMenuEvent = self.sceneContextMenuEvent
        self.scene.setBackgroundBrush(pydaw_widgets.SCENE_BACKGROUND_BRUSH)
        self.scene.selectionChanged.connect(self.scene_selection_changed)
        self.setAcceptDrops(True)
        self.setScene(self.scene)
        self.audio_items = []
        self.track = 0
        self.gradient_index = 0
        self.playback_px = 0.0
        self.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.is_playing = False
        self.reselect_on_stop = []
        #Somewhat slow on my AMD 5450 using the FOSS driver
        #self.setRenderHint(QPainter.Antialiasing)
        self.context_menu_enabled = True

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

    def scrollContentsBy(self, x, y):
        QGraphicsView.scrollContentsBy(self, x, y)
        self.set_header_y_pos()

    def set_header_y_pos(self):
        f_point = self.get_scene_pos()
        self.header.setPos(0.0, f_point.y())
        self.verticalScrollBar().setMinimum(0)

    def get_scene_pos(self):
        return QtCore.QPointF(
            self.horizontalScrollBar().value(),
            self.verticalScrollBar().value())

    def get_selected(self):
        return [x for x in self.audio_items if x.isSelected()]

    def delete_selected(self):
        if self.check_running():
            return
        f_items = shared.CURRENT_ITEM
        f_paif = shared.CURRENT_ITEM
        for f_item in self.get_selected():
            f_items.remove_item(f_item.track_num)
            f_paif.clear_row_if_exists(f_item.track_num)
        shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
        shared.PROJECT.commit(_("Delete audio item(s)"))
        global_open_audio_items(True)

    def crossfade_selected(self):
        f_list = self.get_selected()
        if len(f_list) < 2:
            QMessageBox.warning(
                shared.MAIN_WINDOW, _("Error"),
                _("You must have at least 2 items selected to crossfade"))
            return

        f_tempo = shared.CURRENT_REGION.get_tempo_at_pos(
            shared.CURRENT_ITEM_REF.start_beat,
        )
        f_changed = False

        for f_item in f_list:
            f_start_sec = pydaw_util.musical_time_to_seconds(
                f_tempo, f_item.audio_item.start_bar,
                f_item.audio_item.start_beat)
            f_time_frac = f_item.audio_item.sample_end - \
                f_item.audio_item.sample_start
            f_time_frac *= 0.001
            f_time = f_item.graph_object.length_in_seconds * f_time_frac
            f_end_sec = f_start_sec + f_time
            f_list2 = [x for x in f_list if x.audio_item != f_item.audio_item]

            for f_item2 in f_list2:
                f_start_sec2 = pydaw_util.musical_time_to_seconds(
                    f_tempo, f_item2.audio_item.start_bar,
                    f_item2.audio_item.start_beat)
                f_time_frac2 = f_item2.audio_item.sample_end - \
                    f_item2.audio_item.sample_start
                f_time_frac2 *= 0.001
                f_time2 = f_item2.graph_object.length_in_seconds * f_time_frac2
                f_end_sec2 = f_start_sec2 + f_time2

                if f_start_sec > f_start_sec2 and \
                f_end_sec > f_end_sec2 and \
                f_end_sec2 > f_start_sec:  # item1 is after item2
                    f_changed = True
                    f_diff_sec = f_end_sec2 - f_start_sec
                    f_val = (f_diff_sec / f_time) * 1000.0
                    f_item.audio_item.set_fade_in(f_val)
                elif f_start_sec < f_start_sec2 and \
                f_end_sec < f_end_sec2 and \
                f_end_sec > f_start_sec2: # item1 is before item2
                    f_changed = True
                    f_diff_sec = f_start_sec2 - f_start_sec
                    f_val = (f_diff_sec / f_time) * 1000.0
                    f_item.audio_item.set_fade_out(f_val)

        if f_changed:
            shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
            shared.PROJECT.commit(_("Crossfade audio items"))
            global_open_audio_items(True)


    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip(mk_strings.AudioItemSeq)
        else:
            self.setToolTip("")
        for f_item in self.audio_items:
            f_item.set_tooltips(a_on)

    def resizeEvent(self, a_event):
        QGraphicsView.resizeEvent(self, a_event)
        pydaw_set_audio_seq_zoom(self.h_zoom, self.v_zoom)
        global_open_audio_items(a_reload=False)

    def sceneContextMenuEvent(self, a_event):
        if self.check_running():
            return
        if not self.context_menu_enabled:
            self.context_menu_enabled = True
            return
        QGraphicsScene.contextMenuEvent(self.scene, a_event)
        self.context_menu_pos = a_event.scenePos()
        f_menu = QMenu(shared.MAIN_WINDOW)
        f_paste_action = QAction(
            _("Paste file path from clipboard"), self)
        f_paste_action.triggered.connect(self.on_scene_paste_paths)
        f_menu.addAction(f_paste_action)
        f_menu.exec_(a_event.screenPos())

    def on_scene_paste_paths(self):
        f_path = global_get_audio_file_from_clipboard()
        if f_path:
            self.add_items(
                self.context_menu_pos.x(), self.context_menu_pos.y(),
                [f_path])

    def scene_selection_changed(self):
        f_selected_items = []
        for f_item in self.audio_items:
            f_item.set_brush()
            if f_item.isSelected():
                f_selected_items.append(f_item)
        if len(f_selected_items) == 1:
            _shared.CURRENT_AUDIO_ITEM_INDEX = f_selected_items[0].track_num
            shared.AUDIO_SEQ_WIDGET.modulex.widget.setEnabled(True)
            shared.AUDIO_SEQ_WIDGET.modulex.set_from_list(
                shared.CURRENT_ITEM.get_row(_shared.CURRENT_AUDIO_ITEM_INDEX))
        elif len(f_selected_items) == 0:
            _shared.CURRENT_AUDIO_ITEM_INDEX = None
            shared.AUDIO_SEQ_WIDGET.modulex.widget.setDisabled(True)
        else:
            shared.AUDIO_SEQ_WIDGET.modulex.widget.setDisabled(True)

    def sceneDragEnterEvent(self, a_event):
        a_event.setAccepted(True)

    def sceneDragMoveEvent(self, a_event):
        a_event.setDropAction(QtCore.Qt.CopyAction)

    def check_running(self):
        if not shared.CURRENT_ITEM or libmk.IS_PLAYING:
            return True
        return False

    def sceneDropEvent(self, a_event):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return
        if shared.AUDIO_ITEMS_TO_DROP:
            f_x = a_event.scenePos().x()
            f_y = a_event.scenePos().y()
            self.add_items(f_x, f_y, shared.AUDIO_ITEMS_TO_DROP)

    def add_items(self, f_x, f_y, a_item_list):
        if self.check_running():
            return

        f_beat_frac = f_x / shared.AUDIO_PX_PER_BEAT
        f_beat_frac = pydaw_clip_min(f_beat_frac, 0.0)
        print("f_beat_frac: {}".format(f_beat_frac))
        if shared.AUDIO_QUANTIZE:
            f_beat_frac = int(
                f_beat_frac * shared.AUDIO_QUANTIZE_AMT) / shared.AUDIO_QUANTIZE_AMT

        f_lane_num = int((f_y - shared.AUDIO_RULER_HEIGHT) / shared.AUDIO_ITEM_HEIGHT)
        f_lane_num = pydaw_clip_value(f_lane_num, 0, shared.AUDIO_ITEM_MAX_LANE)

        f_items = shared.CURRENT_ITEM

        for f_file_name in a_item_list:
            f_file_name_str = str(f_file_name)
            if not f_file_name_str is None and not f_file_name_str == "":
                f_index = f_items.get_next_index()
                if f_index == -1:
                    QMessageBox.warning(self, _("Error"),
                    _("No more available audio item slots, "
                    "max per region is {}").format(MAX_AUDIO_ITEM_COUNT))
                    break
                else:
                    f_uid = libmk.PROJECT.get_wav_uid_by_name(f_file_name_str)
                    f_item = pydaw_audio_item(
                        f_uid, a_start_bar=0, a_start_beat=f_beat_frac,
                        a_lane_num=f_lane_num)
                    f_items.add_item(f_index, f_item)
                    f_graph = libmk.PROJECT.get_sample_graph_by_uid(f_uid)
                    f_audio_item = shared.AUDIO_SEQ.draw_item(
                        f_index, f_item, f_graph)
                    f_audio_item.clip_at_region_end()
        shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
        shared.PROJECT.commit(
            _("Added audio items to item {}").format(shared.CURRENT_ITEM.uid))
        global_open_audio_items()
        self.last_open_dir = os.path.dirname(f_file_name_str)

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
        pydaw_set_audio_seq_zoom(self.h_zoom, self.v_zoom)

    def check_line_count(self):
        """ Check that there are not too many vertical
            lines on the screen
        """
        f_num_count = len(self.text_list)
        if f_num_count == 0:
            return
        f_num_visible_count = int(f_num_count /
            pydaw_clip_min(self.h_zoom, 1))

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


    def draw_header(self):
        f_region_length = shared.CURRENT_ITEM_LEN
        f_size = shared.AUDIO_PX_PER_BEAT * f_region_length
        self.total_height = (shared.AUDIO_ITEM_LANE_COUNT *
            (shared.AUDIO_ITEM_HEIGHT)) + shared.AUDIO_RULER_HEIGHT
        AbstractItemEditor.draw_header(self, f_size, shared.AUDIO_RULER_HEIGHT)
        self.header.setZValue(1500.0)
        self.scene.addItem(self.header)
        if shared.ITEM_REF_POS:
            f_start, f_end = shared.ITEM_REF_POS
            f_start_x = f_start * shared.AUDIO_PX_PER_BEAT
            f_end_x = f_end * shared.AUDIO_PX_PER_BEAT
            f_start_line = QGraphicsLineItem(
                f_start_x, 0.0, f_start_x, shared.AUDIO_RULER_HEIGHT, self.header)
            f_start_line.setPen(shared.START_PEN)
            f_end_line = QGraphicsLineItem(
                f_end_x, 0.0, f_end_x, shared.AUDIO_RULER_HEIGHT, self.header)
            f_end_line.setPen(shared.END_PEN)
        f_v_pen = QPen(QtCore.Qt.black)
        #f_beat_pen = QPen(QColor(210, 210, 210))
        f_16th_pen = QPen(QColor(120, 120, 120))
        f_reg_pen = QPen(QtCore.Qt.white)
        i3 = 0.0
        for i in range(int(f_region_length)):
            f_number = QGraphicsSimpleTextItem(
                "{}".format(i + 1), self.header)
            f_number.setFlag(QGraphicsItem.ItemIgnoresTransformations)
            f_number.setBrush(QtCore.Qt.white)
            f_number.setZValue(1000.0)
            self.text_list.append(f_number)
            self.scene.addLine(i3, 0.0, i3, self.total_height, f_v_pen)
            f_number.setPos(i3 + 3.0, 2)
            if shared.AUDIO_LINES_ENABLED:
                for f_i4 in range(1, shared.AUDIO_SNAP_RANGE):
                    f_sub_x = i3 + (shared.AUDIO_QUANTIZE_PX * f_i4)
                    f_line = self.scene.addLine(
                        f_sub_x, shared.AUDIO_RULER_HEIGHT,
                        f_sub_x, self.total_height, f_16th_pen)
                    self.beat_line_list.append(f_line)
#            for f_beat_i in range(1, 4):
#                f_beat_x = i3 + (shared.AUDIO_PX_PER_BEAT * f_beat_i)
#                f_line = self.scene.addLine(
#                    f_beat_x, 0.0, f_beat_x, self.total_height, f_beat_pen)
#                self.beat_line_list.append(f_line)
#                if shared.AUDIO_LINES_ENABLED:
#                    for f_i4 in range(1, shared.AUDIO_SNAP_RANGE):
#                        f_sub_x = f_beat_x + (shared.AUDIO_QUANTIZE_PX * f_i4)
#                        f_line = self.scene.addLine(
#                            f_sub_x, shared.AUDIO_RULER_HEIGHT,
#                            f_sub_x, self.total_height, f_16th_pen)
#                        self.beat_line_list.append(f_line)
            i3 += shared.AUDIO_PX_PER_BEAT
        self.scene.addLine(
            i3, shared.AUDIO_RULER_HEIGHT, i3, self.total_height, f_reg_pen)
        for i2 in range(shared.AUDIO_ITEM_LANE_COUNT):
            f_y = ((shared.AUDIO_ITEM_HEIGHT) * (i2 + 1)) + shared.AUDIO_RULER_HEIGHT
            self.scene.addLine(0, f_y, f_size, f_y)
        self.check_line_count()
        self.set_header_y_pos()

    def clear_drawn_items(self):
        if self.is_playing:
            f_was_playing = True
            self.is_playing = False
        else:
            f_was_playing = False
        self.reset_line_lists()
        self.audio_items = []
        self.scene.clear()
        self.draw_header()
        if f_was_playing:
            self.is_playing = True

    def draw_item(self, a_audio_item_index, a_audio_item, a_graph):
        """a_start in seconds, a_length in seconds"""
        f_audio_item = AudioSeqItem(
            a_audio_item_index, a_audio_item, a_graph)
        self.audio_items.append(f_audio_item)
        self.scene.addItem(f_audio_item)
        return f_audio_item

class AudioItemSeqWidget(FileDragDropper):
    """ The parent widget (including the file browser dialog) for the
        AudioItemSeq
    """
    def __init__(self):
        FileDragDropper.__init__(self, pydaw_util.is_audio_file)

        self.modulex = pydaw_widgets.pydaw_per_audio_item_fx_widget(
            global_paif_rel_callback, global_paif_val_callback)

        self.modulex_widget = QWidget()
        self.modulex_widget.setObjectName("plugin_ui")
        self.modulex_vlayout = QVBoxLayout(self.modulex_widget)
        self.folders_tab_widget.addTab(self.modulex_widget, _("Per-Item FX"))
        self.modulex.widget.setDisabled(True)
        self.modulex_vlayout.addWidget(self.modulex.scroll_area)

        self.widget = QWidget()
        self.vlayout = QVBoxLayout()
        self.widget.setLayout(self.vlayout)
        self.controls_grid_layout = QGridLayout()
        self.controls_grid_layout.addItem(
            QSpacerItem(10, 10, QSizePolicy.Expanding), 0, 30)
        self.vlayout.addLayout(self.controls_grid_layout)
        self.vlayout.addWidget(shared.AUDIO_SEQ)

        self.menu_button = QPushButton(_("Menu"))
        self.controls_grid_layout.addWidget(self.menu_button, 0, 3)
        self.action_menu = QMenu(self.widget)
        self.menu_button.setMenu(self.action_menu)
        self.copy_action = self.action_menu.addAction(_("Copy"))
        self.copy_action.triggered.connect(self.on_copy)
        self.copy_action.setShortcut(QKeySequence.Copy)
        self.cut_action = self.action_menu.addAction(_("Cut"))
        self.cut_action.triggered.connect(self.on_cut)
        self.cut_action.setShortcut(QKeySequence.Cut)
        self.paste_action = self.action_menu.addAction(_("Paste"))
        self.paste_action.triggered.connect(self.on_paste)
        self.paste_action.setShortcut(QKeySequence.Paste)
        self.select_all_action = self.action_menu.addAction(_("Select All"))
        self.select_all_action.triggered.connect(self.on_select_all)
        self.select_all_action.setShortcut(QKeySequence.SelectAll)
        self.clear_selection_action = self.action_menu.addAction(
            _("Clear Selection"))
        self.clear_selection_action.triggered.connect(
            shared.AUDIO_SEQ.scene.clearSelection)
        self.clear_selection_action.setShortcut(
            QKeySequence.fromString("Esc"))
        self.action_menu.addSeparator()
        self.delete_selected_action = self.action_menu.addAction(_("Delete"))
        self.delete_selected_action.triggered.connect(self.on_delete_selected)
        self.delete_selected_action.setShortcut(QKeySequence.Delete)
        self.action_menu.addSeparator()
        self.crossfade_action = self.action_menu.addAction(
            _("Crossfade Selected"))
        self.crossfade_action.triggered.connect(shared.AUDIO_SEQ.crossfade_selected)
        self.crossfade_action.setShortcut(
            QKeySequence.fromString("CTRL+F"))

        self.action_menu.addSeparator()
        self.open_last_action = self.action_menu.addAction(
            _("Open Last Item(s)"))
        self.open_last_action.triggered.connect(open_last)
        self.open_last_action.setShortcut(QKeySequence.fromString("ALT+F"))

        self.v_zoom_slider = QSlider(QtCore.Qt.Horizontal)
        self.v_zoom_slider.setObjectName("zoom_slider")
        self.v_zoom_slider.setRange(10, 100)
        self.v_zoom_slider.setValue(10)
        self.v_zoom_slider.setSingleStep(1)
        self.v_zoom_slider.setMaximumWidth(150)
        self.v_zoom_slider.valueChanged.connect(self.set_v_zoom)
        self.controls_grid_layout.addWidget(QLabel(_("V")), 0, 45)
        self.controls_grid_layout.addWidget(self.v_zoom_slider, 0, 46)

        self.audio_items_clipboard = []
        self.disable_on_play = (self.menu_button,)
        self.set_multiselect(False)

    def on_play(self):
        for f_item in self.disable_on_play:
            f_item.setEnabled(False)

    def on_stop(self):
        for f_item in self.disable_on_play:
            f_item.setEnabled(True)

    def set_tooltips(self, a_on):
        if a_on:
            self.folders_widget.setToolTip(
                mk_strings.audio_viewer_widget_folders)
            self.modulex.widget.setToolTip(
                mk_strings.audio_viewer_widget_modulex)
        else:
            self.folders_widget.setToolTip("")
            self.modulex.widget.setToolTip("")

    def on_select_all(self):
        if (
            shared.CURRENT_REGION is None
            or
            libmk.IS_PLAYING
        ):
            return
        for f_item in shared.AUDIO_SEQ.audio_items:
            f_item.setSelected(True)

    def on_glue_selected(self):
        if (
            shared.CURRENT_REGION is None
            or
            libmk.IS_PLAYING
        ):
            return
        shared.AUDIO_SEQ.glue_selected()

    def on_delete_selected(self):
        if (
            shared.CURRENT_REGION is None
            or
            libmk.IS_PLAYING
        ):
            return
        shared.AUDIO_SEQ.delete_selected()

    def on_modulex_copy(self):
        if (
            _shared.CURRENT_AUDIO_ITEM_INDEX is not None
            and
            shared.CURRENT_ITEM
        ):
            f_paif = shared.CURRENT_ITEM
            self.modulex_clipboard = f_paif.get_row(
                _shared.CURRENT_AUDIO_ITEM_INDEX,
            )

    def on_modulex_paste(self):
        if self.modulex_clipboard is not None and shared.CURRENT_ITEM:
            f_paif = shared.CURRENT_ITEM
            for f_item in shared.AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_paif.set_row(f_item.track_num, self.modulex_clipboard)
            shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
            shared.AUDIO_SEQ_WIDGET.modulex.set_from_list(self.modulex_clipboard)

    def on_modulex_clear(self):
        if shared.CURRENT_ITEM:
            f_paif = shared.CURRENT_ITEM
            for f_item in shared.AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_paif.clear_row(f_item.track_num)
            shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
            self.modulex.clear_effects()

    def on_copy(self):
        if not shared.CURRENT_ITEM or libmk.IS_PLAYING:
            return 0
        self.audio_items_clipboard = []
        f_per_item_fx_dict = shared.CURRENT_ITEM
        f_count = False
        for f_item in shared.AUDIO_SEQ.get_selected():
            f_count = True
            self.audio_items_clipboard.append(
                (str(f_item.audio_item),
                 f_per_item_fx_dict.get_row(f_item.track_num, True)))
        if not f_count:
            QMessageBox.warning(
                self.widget, _("Error"), _("Nothing selected."))
        return f_count

    def on_cut(self):
        if self.on_copy():
            self.on_delete_selected()

    def on_paste(self):
        if not shared.CURRENT_ITEM or libmk.IS_PLAYING:
            return
        if not self.audio_items_clipboard:
            QMessageBox.warning(
                self.widget, _("Error"),
                _("Nothing copied to the clipboard."))
        shared.AUDIO_SEQ.reselect_on_stop = []
        f_per_item_fx_dict = shared.CURRENT_ITEM
#        f_global_tempo = float(TRANSPORT.tempo_spinbox.value())
        for f_str, f_list in self.audio_items_clipboard:
            shared.AUDIO_SEQ.reselect_on_stop.append(f_str)
            f_index = shared.CURRENT_ITEM.get_next_index()
            if f_index == -1:
                break
            f_item = pydaw_audio_item.from_str(f_str)
            f_start = f_item.start_beat
            if f_start < shared.CURRENT_ITEM_LEN:
#                f_graph = libmk.PROJECT.get_sample_graph_by_uid(f_item.uid)
#                f_item.clip_at_region_end(
#                    shared.CURRENT_ITEM_LEN, f_global_tempo,
#                    f_graph.length_in_seconds)
                shared.CURRENT_ITEM.add_item(f_index, f_item)
                if f_list is not None:
                    f_per_item_fx_dict.set_row(f_index, f_list)
        shared.CURRENT_ITEM.deduplicate_items()
        shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
        shared.PROJECT.commit(_("Paste audio items"))
        global_open_audio_items(True)
        shared.AUDIO_SEQ.scene.clearSelection()
        shared.AUDIO_SEQ.reset_selection()

    def set_v_zoom(self, a_val=None):
        shared.AUDIO_SEQ.set_v_zoom(float(a_val) * 0.1)
        global_open_audio_items(a_reload=False)

def global_get_audio_file_from_clipboard():
    f_clipboard = QApplication.clipboard()
    f_path = f_clipboard.text()
    if not f_path:
        QMessageBox.warning(
            shared.MAIN_WINDOW, _("Error"), _("No text in the system clipboard"))
    else:
        f_path = str(f_path).strip()
        if os.path.isfile(f_path):
            print(f_path)
            return f_path
        else:
            f_path = f_path[:100]
            QMessageBox.warning(
                shared.MAIN_WINDOW, _("Error"),
                _("{} is not a valid file").format(f_path))
    return None

def pydaw_set_audio_seq_zoom(a_horizontal, a_vertical):
    f_width = float(shared.AUDIO_SEQ.rect().width()) - \
        float(shared.AUDIO_SEQ.verticalScrollBar().width()) - 6.0
    f_region_length = shared.CURRENT_ITEM_LEN
    f_region_px = f_region_length * 100.0
    f_region_scale = f_width / f_region_px

    shared.AUDIO_PX_PER_BEAT = 100.0 * a_horizontal * f_region_scale
    shared.AUDIO_SEQ.px_per_beat = shared.AUDIO_PX_PER_BEAT
    pydaw_set_audio_snap(shared.AUDIO_SNAP_VAL)
    shared.AUDIO_ITEM_HEIGHT = 75.0 * a_vertical


