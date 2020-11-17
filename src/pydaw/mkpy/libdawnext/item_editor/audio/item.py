from . import (
    item_context_menu,
    _shared,
)
from mkpy import libmk
from mkpy.libdawnext import shared
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

class AudioSeqItem(pydaw_widgets.QGraphicsRectItemNDL):
    """ This is an individual audio item within the AudioItemSeq """
    def __init__(
        self,
        a_track_num,
        a_audio_item,
        a_graph,
    ):
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
            0.0,
            shared.AUDIO_ITEM_HANDLE_HEIGHT,
            0.0,
            (
                shared.AUDIO_ITEM_HEIGHT * -1.0
            ) + shared.AUDIO_ITEM_HANDLE_HEIGHT,
            self.start_handle,
        )

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
        shared.CC_EDITOR.clipboard = envelope_to_automation(
            self.graph_object,
            True,
            TRANSPORT.tempo_spinbox.value(),
        )

    def copy_as_pb_automation(self):
        shared.PB_EDITOR.clipboard = envelope_to_automation(
            self.graph_object,
            False,
            TRANSPORT.tempo_spinbox.value(),
        )

    def copy_as_notes(self):
        shared.PIANO_ROLL_EDITOR.clipboard = envelope_to_notes(
            self.graph_object,
            TRANSPORT.tempo_spinbox.value(),
        )

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
            TRACK_COUNT_ALL,
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


