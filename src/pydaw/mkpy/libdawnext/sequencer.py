"""

"""
from mkpy import libmk
from mkpy.libdawnext import project, shared
from mkpy.libdawnext.project import *
from mkpy.libdawnext.shared import *
from mkpy.libpydaw import (
    pydaw_util,
    pydaw_widgets,
)
from mkpy.libpydaw.pydaw_util import *
from mkpy.libpydaw.translate import _
from mkpy.mkplugins import *
from mkpy.mkqt import *


DRAW_SEQUENCER_GRAPHS = True
REGION_EDITOR_SNAP = True
REGION_EDITOR_GRID_WIDTH = 1000.0
REGION_TRACK_WIDTH = 180  #Width of the tracks in px
MREC_EVENTS = []

REGION_EDITOR_TRACK_COUNT = 32

REGION_EDITOR_HEADER_ROW_HEIGHT = 18
REGION_EDITOR_HEADER_HEIGHT = REGION_EDITOR_HEADER_ROW_HEIGHT * 3
#gets updated by the region editor to it's real value:
REGION_EDITOR_TOTAL_HEIGHT = (REGION_EDITOR_TRACK_COUNT *
    shared.REGION_EDITOR_TRACK_HEIGHT)
REGION_EDITOR_QUANTIZE_INDEX = 4

REGION_EDITOR_MODE = 0

ATM_CLIPBOARD = []
REGION_CLIPBOARD = []

CACHED_SEQ_LEN = 32

ATM_POINT_DIAMETER = 10.0
ATM_POINT_RADIUS = ATM_POINT_DIAMETER * 0.5

ATM_GRADIENT = QtCore.Qt.white

LAST_ITEM_LENGTH = 4
SEQUENCER_PX_PER_BEAT = 24
SEQUENCER_SNAP_VAL = 3
SEQUENCER_QUANTIZE_PX = SEQUENCER_PX_PER_BEAT
SEQUENCER_QUANTIZE_64TH = SEQUENCER_PX_PER_BEAT / 16.0
SEQ_QUANTIZE = True
SEQ_QUANTIZE_AMT = 1.0
SEQ_LINES_ENABLED = False
SEQ_SNAP_RANGE = 8

TRACK_COLOR_CLIPBOARD = None

REGION_EDITOR_MIN_NOTE_LENGTH = REGION_EDITOR_GRID_WIDTH / 128.0
REGION_EDITOR_DELETE_MODE = False

def pydaw_set_seq_snap(a_val=None):
    global SEQUENCER_QUANTIZE_PX, SEQ_QUANTIZE, SEQ_QUANTIZE_AMT, \
        SEQ_LINES_ENABLED, SEQ_SNAP_RANGE, SEQUENCER_SNAP_VAL, \
        SEQUENCER_QUANTIZE_64TH
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

class SeqAtmItem(QGraphicsEllipseItem):
    """ This is an automation point within the ItemSequencer, these are only
        drawn when "Automation" mode is selected in RegionSettings
    """
    def __init__(self, a_item, a_save_callback, a_min_y, a_max_y):
        QGraphicsEllipseItem.__init__(
            self, 0, 0, ATM_POINT_DIAMETER, ATM_POINT_DIAMETER)
        self.setPen(shared.NO_PEN)
        self.save_callback = a_save_callback
        self.item = a_item
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setZValue(1100.0)
        self.set_brush()
        self.min_y = a_min_y
        self.max_y = a_max_y
        self.is_deleted = False

    def itemChange(self, a_change, a_value):
        if a_change == QGraphicsItem.ItemSelectedHasChanged:
            self.set_brush()
        return QGraphicsItem.itemChange(self, a_change, a_value)

    def set_brush(self):
        if self.isSelected():
            self.setBrush(QtCore.Qt.black)
        else:
            self.setBrush(ATM_GRADIENT)

    def mousePressEvent(self, a_event):
        shared.SEQUENCER.remove_atm_path(self.item.index)
        a_event.setAccepted(True)
        QGraphicsEllipseItem.mousePressEvent(self, a_event)
        self.quantize(a_event.scenePos())

    def mouseMoveEvent(self, a_event):
        QGraphicsEllipseItem.mouseMoveEvent(self, a_event)
        self.quantize(a_event.scenePos())

    def quantize(self, a_pos):
        f_pos = a_pos
        f_x = f_pos.x()
        if SEQ_QUANTIZE:
            f_x = round(f_x / SEQUENCER_QUANTIZE_PX) * SEQUENCER_QUANTIZE_PX
        else:
            f_x = round(
                f_x / SEQUENCER_QUANTIZE_64TH) * SEQUENCER_QUANTIZE_64TH
        f_x = pydaw_util.pydaw_clip_min(f_x, 0.0)
        f_y = pydaw_util.pydaw_clip_value(f_pos.y(), self.min_y, self.max_y)
        self.setPos(f_x, f_y)

    def mouseReleaseEvent(self, a_event):
        a_event.setAccepted(True)
        QGraphicsEllipseItem.mouseReleaseEvent(self, a_event)
        self.quantize(a_event.scenePos())
        self.set_point_value()
        self.save_callback()

    def set_point_value(self):
        f_pos = self.pos()
        f_point = self.item
        (track, beat, cc_val) = shared.SEQUENCER.get_item_coord(f_pos, a_clip=True)
        beat = pydaw_util.pydaw_clip_min(beat, 0.0)
        cc_val = pydaw_util.pydaw_clip_value(cc_val, 0.0, 127.0, True)
        f_point.beat, f_point.cc_val = (beat, cc_val)

    def __lt__(self, other):
        return self.pos().x() < other.pos().x()

class SequencerItem(pydaw_widgets.QGraphicsRectItemNDL):
    """ This is an individual sequencer item within the ItemSequencer
    """
    def __init__(self, a_name, a_audio_item):
        QGraphicsRectItem.__init__(self)
        self.name = str(a_name)
        self.is_deleted = False

        if REGION_EDITOR_MODE == 0:
            self.setFlag(QGraphicsItem.ItemIsMovable)
            self.setFlag(QGraphicsItem.ItemIsSelectable)
            self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
            self.setFlag(QGraphicsItem.ItemDoesntPropagateOpacityToChildren)
        else:
            self.setEnabled(False)
            self.setOpacity(0.2)

        self.setFlag(QGraphicsItem.ItemClipsChildrenToShape)

        self.audio_item = a_audio_item
        self.orig_string = str(a_audio_item)
        self.track_num = a_audio_item.track_num

        self.pixmap_items = []
        self.should_draw = DRAW_SEQUENCER_GRAPHS or \
            a_audio_item.length_beats > CACHED_SEQ_LEN * 0.02

        if self.should_draw:
            f_pixmaps, f_transform, self.x_scale, self.y_scale = \
                shared.PROJECT.get_item_path(
                    a_audio_item.item_uid, SEQUENCER_PX_PER_BEAT,
                    shared.REGION_EDITOR_TRACK_HEIGHT - 20,
                    shared.CURRENT_REGION.get_tempo_at_pos(a_audio_item.start_beat))
            for f_pixmap in f_pixmaps:
                f_pixmap_item = QGraphicsPixmapItem(self)
                f_pixmap_item.setCacheMode(
                    QGraphicsItem.DeviceCoordinateCache)
                f_pixmap_item.setPixmap(f_pixmap)
                f_pixmap_item.setTransform(f_transform)
                f_pixmap_item.setZValue(1900.0)
                self.pixmap_items.append(f_pixmap_item)

        self.label_bg = QGraphicsRectItem(parent=self)
        self.label_bg.setPen(shared.NO_PEN)
        self.label_bg.setPos(1.0, 1.0)
        self.label_bg.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.label_bg.setZValue(2050.00)

        self.label = QGraphicsSimpleTextItem(str(a_name), parent=self)
        self.label.setPen(shared.NO_PEN)
        self.label.setBrush(QtCore.Qt.white)

        self.label.setPos(1.0, 1.0)
        self.label.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.label.setZValue(2100.00)

        self.start_handle = QGraphicsRectItem(parent=self)
        self.start_handle.setZValue(2200.0)
        self.start_handle.setAcceptHoverEvents(True)
        self.start_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.start_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.start_handle.setRect(
            QtCore.QRectF(
                0.0,
                0.0,
                shared.AUDIO_ITEM_HANDLE_SIZE,
                shared.AUDIO_ITEM_HANDLE_HEIGHT,
            ),
        )
        self.start_handle.mousePressEvent = self.start_handle_mouseClickEvent
        self.start_handle_line = QGraphicsLineItem(
            0.0,
            shared.AUDIO_ITEM_HANDLE_HEIGHT,
            0.0,
            (
                shared.REGION_EDITOR_TRACK_HEIGHT * -1.0
            ) + shared.AUDIO_ITEM_HANDLE_HEIGHT,
            self.start_handle,
        )

        self.start_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)

        self.length_handle = QGraphicsRectItem(parent=self)
        self.length_handle.setZValue(2200.0)
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
            (shared.REGION_EDITOR_TRACK_HEIGHT * -1.0) + shared.AUDIO_ITEM_HANDLE_HEIGHT,
            self.length_handle)

        self.stretch_handle = QGraphicsRectItem(parent=self)
        self.stretch_handle.setAcceptHoverEvents(True)
        self.stretch_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.stretch_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.stretch_handle.setRect(
            QtCore.QRectF(
                0.0,
                0.0,
                shared.AUDIO_ITEM_HANDLE_SIZE,
                shared.AUDIO_ITEM_HANDLE_HEIGHT,
            ),
        )
        self.stretch_handle.mousePressEvent = \
            self.stretch_handle_mouseClickEvent
        self.stretch_handle_line = QGraphicsLineItem(
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5) -
                (shared.REGION_EDITOR_TRACK_HEIGHT * 0.5),
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (shared.REGION_EDITOR_TRACK_HEIGHT * 0.5) +
                (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5),
            self.stretch_handle)
        self.stretch_handle.hide()

        self.split_line = QGraphicsLineItem(
            0.0, 0.0, 0.0, shared.REGION_EDITOR_TRACK_HEIGHT, self)
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
        self.event_pos_orig = None
        self.width_orig = None
        self.quantize_offset = 0.0
        if libmk.TOOLTIPS_ENABLED:
            self.set_tooltips(True)
        self.draw()

    def itemChange(self, a_change, a_value):
        if a_change == QGraphicsItem.ItemSelectedHasChanged:
            self.set_brush()
        return QGraphicsItem.itemChange(self, a_change, a_value)

    def get_selected_string(self):
        return str(self.audio_item)

    def mouseDoubleClickEvent(self, a_event):
        a_event.setAccepted(True)
        QGraphicsRectItem.mouseDoubleClickEvent(self, a_event)
        global_open_items(
            self.name, a_reset_scrollbar=True, a_new_ref=self.audio_item)
        editors = (shared.CURRENT_ITEM.items, shared.CURRENT_ITEM.notes,
             shared.CURRENT_ITEM.ccs, shared.CURRENT_ITEM.pitchbends)
        current_index = shared.ITEM_EDITOR.tab_widget.currentIndex()
        if current_index < len(editors) and not editors[current_index]:
            for i in range(len(editors)):
                if editors[i]:
                    current_index = i
                    shared.ITEM_EDITOR.tab_widget.setCurrentIndex(current_index)
                    break
        shared.MAIN_WINDOW.main_tabwidget.setCurrentIndex(
            shared.TAB_ITEM_EDITOR,
        )
        #Ensure that notes are visible
        if current_index == 1 and shared.CURRENT_ITEM.notes:
            height = PIANO_ROLL_EDITOR.geometry().height()
            average = sum(
                x.pos().y() for x in PIANO_ROLL_EDITOR.note_items
                ) / len(PIANO_ROLL_EDITOR.note_items)
            val = int(average - (height * 0.5))
            PIANO_ROLL_EDITOR.verticalScrollBar().setValue(val)

    def generic_hoverEnterEvent(self, a_event):
        if not libmk.IS_PLAYING:
            QApplication.setOverrideCursor(QCursor(QtCore.Qt.SizeHorCursor))

    def generic_hoverLeaveEvent(self, a_event):
        QApplication.restoreOverrideCursor()

    def draw(self):
        f_start = self.audio_item.start_beat * SEQUENCER_PX_PER_BEAT
        f_length = (self.audio_item.length_beats * SEQUENCER_PX_PER_BEAT)

        self.length_orig = f_length
        self.length_px_start = (self.audio_item.start_offset *
            SEQUENCER_PX_PER_BEAT)
        self.length_px_minus_start = f_length - self.length_px_start

        self.rect_orig = QtCore.QRectF(
            0.0, 0.0, f_length, shared.REGION_EDITOR_TRACK_HEIGHT)
        self.setRect(self.rect_orig)

        label_rect = QtCore.QRectF(0.0, 0.0, f_length, 20)
        self.label_bg.setRect(label_rect)

        f_track_num = REGION_EDITOR_HEADER_HEIGHT + (
            shared.REGION_EDITOR_TRACK_HEIGHT * self.audio_item.track_num)

        self.setPos(f_start, f_track_num)
        self.is_moving = False
#        if self.audio_item.time_stretch_mode >= 3 or \
#        (self.audio_item.time_stretch_mode == 2 and \
#        (self.audio_item.timestretch_amt_end ==
#        self.audio_item.timestretch_amt)):
#            self.stretch_width_default = \
#                f_length / self.audio_item.timestretch_amt

        self.sample_start_offset_px = -self.length_px_start

        if self.should_draw:
            f_offset = 0
            f_offset_inc = project.PIXMAP_TILE_WIDTH * self.x_scale
            for f_pixmap_item in self.pixmap_items:
                f_pixmap_item.setPos(
                    f_offset + self.sample_start_offset_px, 20.0)
                f_offset += f_offset_inc

        self.start_handle_scene_min = f_start + self.sample_start_offset_px
        self.start_handle_scene_max = self.start_handle_scene_min + f_length

        self.length_handle.setPos(
            f_length - shared.AUDIO_ITEM_HANDLE_SIZE,
            shared.REGION_EDITOR_TRACK_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT)
        self.start_handle.setPos(
            0.0, shared.REGION_EDITOR_TRACK_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT)
#        if self.audio_item.time_stretch_mode >= 2 and \
#        (((self.audio_item.time_stretch_mode != 5) and \
#        (self.audio_item.time_stretch_mode != 2)) \
#        or (self.audio_item.timestretch_amt_end ==
#        self.audio_item.timestretch_amt)):
#            self.stretch_handle.show()
#            self.stretch_handle.setPos(
#                f_length - shared.AUDIO_ITEM_HANDLE_SIZE,
#                (shared.REGION_EDITOR_TRACK_HEIGHT * 0.5) - \
#                (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5))

    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip(dn_strings.sequencer_item)
            self.start_handle.setToolTip(
                _("Use this handle to resize the item by changing "
                "the start point."))
            self.length_handle.setToolTip(
                _("Use this handle to resize the item by "
                "changing the end point."))
            self.stretch_handle.setToolTip(
                _("Use this handle to resize the item by "
                "time-stretching it."))
        else:
            self.setToolTip("")
            self.start_handle.setToolTip("")
            self.length_handle.setToolTip("")
            self.stretch_handle.setToolTip("")

    def clip_at_region_end(self):
        f_current_region_length = pydaw_get_current_region_length()
        f_max_x = f_current_region_length * SEQUENCER_PX_PER_BEAT
        f_pos_x = self.pos().x()
        f_end = f_pos_x + self.rect().width()
        if f_end > f_max_x:
            f_end_px = f_max_x - f_pos_x
            self.setRect(0.0, 0.0, f_end_px, shared.REGION_EDITOR_TRACK_HEIGHT)
            self.audio_item.sample_end = \
                ((self.rect().width() + self.length_px_start) /
                self.length_orig) * 1000.0
            self.audio_item.sample_end = pydaw_util.pydaw_clip_value(
                self.audio_item.sample_end, 1.0, 1000.0, True)
            self.draw()
            return True
        else:
            return False

    def set_brush(self, a_index=None):
        if self.isSelected():
            if REGION_EDITOR_MODE == 0:
                self.setOpacity(1.0)
            self.setBrush(shared.SELECTED_ITEM_COLOR)
            self.label_bg.setBrush(shared.SELECTED_ITEM_COLOR)
            self.start_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.length_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.stretch_handle.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.split_line.setPen(shared.AUDIO_ITEM_HANDLE_SELECTED_PEN)

            self.start_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)
            self.length_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)
            self.stretch_handle_line.setPen(shared.AUDIO_ITEM_LINE_SELECTED_PEN)

            self.label.setBrush(QtCore.Qt.black)
            self.start_handle.setBrush(shared.AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.length_handle.setBrush(shared.AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.stretch_handle.setBrush(shared.AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
        else:
            if REGION_EDITOR_MODE == 0:
                self.setOpacity(0.3)
            self.start_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.length_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.stretch_handle.setPen(shared.AUDIO_ITEM_HANDLE_PEN)
            self.split_line.setPen(shared.AUDIO_ITEM_HANDLE_PEN)

            self.start_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)
            self.length_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)
            self.stretch_handle_line.setPen(shared.AUDIO_ITEM_LINE_PEN)

            self.label.setBrush(QtCore.Qt.white)
            self.start_handle.setBrush(shared.AUDIO_ITEM_HANDLE_BRUSH)
            self.length_handle.setBrush(shared.AUDIO_ITEM_HANDLE_BRUSH)
            self.stretch_handle.setBrush(shared.AUDIO_ITEM_HANDLE_BRUSH)
            brush = shared.TRACK_COLORS.get_brush(self.audio_item.track_num)
            self.label_bg.setBrush(brush)
            self.setBrush(brush)

    def pos_to_musical_time(self, a_pos):
        return a_pos / SEQUENCER_PX_PER_BEAT

    def start_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.length_handle, a_event)
        for f_item in shared.SEQUENCER.audio_items:
            if f_item.isSelected():
                f_item.min_start = f_item.pos().x() * -1.0
                f_item.is_start_resizing = True
                f_item.setFlag(
                    QGraphicsItem.ItemClipsChildrenToShape, False)

    def length_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.length_handle, a_event)
        for f_item in shared.SEQUENCER.audio_items:
            if f_item.isSelected():
                f_item.is_resizing = True
                f_item.setFlag(
                    QGraphicsItem.ItemClipsChildrenToShape, False)

    def stretch_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QGraphicsRectItem.mousePressEvent(self.stretch_handle, a_event)
        f_max_region_pos = (SEQUENCER_PX_PER_BEAT *
            pydaw_get_current_region_length())
        for f_item in shared.SEQUENCER.audio_items:
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
            shared.SEQUENCER.scene.clearSelection()
            self.setSelected(True)

    def select_file_instance(self):
        shared.SEQUENCER.scene.clearSelection()
        f_uid = self.audio_item.uid
        for f_item in shared.SEQUENCER.audio_items:
            if f_item.audio_item.uid == f_uid:
                f_item.setSelected(True)

    def sends_dialog(self):
        def ok_handler():
            f_list = [x.audio_item for x in shared.SEQUENCER.audio_items
                if x.isSelected()]
            for f_item in f_list:
                f_item.output_track = f_track_cboxes[0].currentIndex()
                f_item.vol = get_vol(f_track_vols[0].value())
                f_item.s0_sc = f_sc_checkboxes[0].isChecked()
                f_item.send1 = f_track_cboxes[1].currentIndex() - 1
                f_item.s1_vol = get_vol(f_track_vols[1].value())
                f_item.s1_sc = f_sc_checkboxes[1].isChecked()
                f_item.send2 = f_track_cboxes[2].currentIndex() - 1
                f_item.s2_vol = get_vol(f_track_vols[2].value())
                f_item.s2_sc = f_sc_checkboxes[2].isChecked()
            shared.PROJECT.save_region(shared.CURRENT_REGION)
            shared.PROJECT.commit(_("Update sends for sequencer item(s)"))
            f_dialog.close()

        def cancel_handler():
            f_dialog.close()

        def vol_changed(a_val=None):
            for f_vol_label, f_vol_slider in zip(f_vol_labels, f_track_vols):
                f_vol_label.setText(
                    "{}dB".format(get_vol(f_vol_slider.value())))

        def get_vol(a_val):
            return round(a_val * 0.1, 1)

        f_dialog = QDialog(shared.MAIN_WINDOW)
        f_dialog.setWindowTitle(_("Set Volume for all Instance of File"))
        f_layout = QGridLayout(f_dialog)
        f_layout.setAlignment(QtCore.Qt.AlignCenter)
        f_track_cboxes = []
        f_sc_checkboxes = []
        f_track_vols = []
        f_vol_labels = []
        f_current_vals = [
            (self.audio_item.output_track, self.audio_item.vol,
             self.audio_item.s0_sc),
            (self.audio_item.send1, self.audio_item.s1_vol,
             self.audio_item.s1_sc),
            (self.audio_item.send2, self.audio_item.s2_vol,
             self.audio_item.s2_sc)]
        for f_i in range(3):
            f_out, f_vol, f_sc = f_current_vals[f_i]
            f_tracks_combobox = QComboBox()
            f_track_cboxes.append(f_tracks_combobox)
            if f_i == 0:
                f_tracks_combobox.addItems(shared.TRACK_NAMES)
                f_tracks_combobox.setCurrentIndex(f_out)
            else:
                f_tracks_combobox.addItems(["None"] + shared.TRACK_NAMES)
                f_tracks_combobox.setCurrentIndex(f_out + 1)
            f_tracks_combobox.setMinimumWidth(105)
            f_layout.addWidget(f_tracks_combobox, 0, f_i)
            f_sc_checkbox = QCheckBox(_("Sidechain"))
            f_sc_checkboxes.append(f_sc_checkbox)
            if f_sc:
                f_sc_checkbox.setChecked(True)
            f_layout.addWidget(f_sc_checkbox, 1, f_i)
            f_vol_slider = QSlider(QtCore.Qt.Vertical)
            f_track_vols.append(f_vol_slider)
            f_vol_slider.setRange(-240, 240)
            f_vol_slider.setMinimumHeight(360)
            f_vol_slider.valueChanged.connect(vol_changed)
            f_layout.addWidget(f_vol_slider, 2, f_i, QtCore.Qt.AlignCenter)
            f_vol_label = QLabel("0.0dB")
            f_vol_labels.append(f_vol_label)
            f_layout.addWidget(f_vol_label, 3, f_i)
            f_vol_slider.setValue(f_vol * 10.0)

        f_ok_cancel_layout = QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout, 10, 2)
        f_ok_button = QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_handler)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.exec_()

    def reset_end(self):
        f_list = shared.SEQUENCER.get_selected()
        for f_item in f_list:
            f_old = f_item.audio_item.start_offset
            f_item.audio_item.start_offset = 0.0
            f_item.audio_item.length_beats += f_old
            self.draw()
            self.clip_at_region_end()
        shared.PROJECT.save_region(shared.CURRENT_REGION)
        shared.PROJECT.commit(_("Reset sample ends for item(s)"))
        global_open_audio_items()

    def mousePressEvent(self, a_event):
        if libmk.IS_PLAYING or a_event.button() == QtCore.Qt.RightButton:
            return

        if a_event.modifiers() == (
        QtCore.Qt.AltModifier | QtCore.Qt.ShiftModifier):
            self.setSelected((not self.isSelected()))
            return

        if not self.isSelected():
            shared.SEQUENCER.scene.clearSelection()
            self.setSelected(True)

        if shared.EDITOR_MODE == shared.EDITOR_MODE_SPLIT:
            f_item = self.audio_item
            f_item_old = f_item.clone()
            shared.CURRENT_REGION.add_item(f_item_old)
            f_scene_pos = self.quantize(a_event.scenePos().x())
            f_musical_pos = self.pos_to_musical_time(
                f_scene_pos) - f_item_old.start_beat
            f_item.start_beat = f_item.start_beat + f_musical_pos
            f_item.length_beats = f_item_old.length_beats - f_musical_pos
            f_item.start_offset = f_musical_pos + f_item_old.start_offset
            f_item_old.length_beats = f_musical_pos
            shared.PROJECT.save_region(shared.CURRENT_REGION)
            shared.PROJECT.commit(_("Split sequencer item"))
            shared.REGION_SETTINGS.open_region()
        else:
            if a_event.modifiers() == QtCore.Qt.ControlModifier:
                a_event.accept()
            QGraphicsRectItem.mousePressEvent(self, a_event)
            self.event_pos_orig = a_event.pos().x()
            for f_item in shared.SEQUENCER.get_selected():
                f_item_pos = f_item.pos().x()
                f_item.setZValue(2400.0)
                f_item.quantize_offset = \
                    f_item_pos - f_item.quantize_all(f_item_pos)
                if a_event.modifiers() == QtCore.Qt.ControlModifier:
                    f_item.is_copying = True
                    f_item.width_orig = f_item.rect().width()
                    shared.SEQUENCER.draw_item(f_item.name, f_item.audio_item)
                if self.is_start_resizing:
                    f_item.width_orig = 0.0
                else:
                    f_item.width_orig = f_item.rect().width()

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
        f_lane_num = int((a_y_pos - REGION_EDITOR_HEADER_HEIGHT) /
            shared.REGION_EDITOR_TRACK_HEIGHT)
        f_lane_num = pydaw_clip_value(
            f_lane_num, 0, project.TRACK_COUNT_ALL)
        f_y_pos = (f_lane_num *
            shared.REGION_EDITOR_TRACK_HEIGHT) + REGION_EDITOR_HEADER_HEIGHT
        return f_lane_num, f_y_pos

    def lane_number_to_y_pos(self, a_lane_num):
        a_lane_num = pydaw_util.pydaw_clip_value(
            a_lane_num, 0, project.TRACK_COUNT_ALL)
        return (a_lane_num *
            shared.REGION_EDITOR_TRACK_HEIGHT) + REGION_EDITOR_HEADER_HEIGHT

    def quantize_all(self, a_x):
        f_x = a_x
        if SEQ_QUANTIZE:
            f_x = round(f_x / SEQUENCER_QUANTIZE_PX) * SEQUENCER_QUANTIZE_PX
        return f_x

    def quantize(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        if SEQ_QUANTIZE and f_x < SEQUENCER_QUANTIZE_PX:
            f_x = SEQUENCER_QUANTIZE_PX
        return f_x

    def quantize_start(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        if f_x >= self.length_handle.pos().x():
            f_x -= SEQUENCER_QUANTIZE_PX
        return f_x

    def quantize_scene(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        return f_x

    def mouseMoveEvent(self, a_event):
        if libmk.IS_PLAYING or self.event_pos_orig is None:
            return

        f_event_pos = a_event.pos().x()
        f_event_diff = f_event_pos - self.event_pos_orig

        if self.is_resizing:
            for f_item in shared.SEQUENCER.get_selected():
                f_x = f_item.width_orig + f_event_diff + \
                    f_item.quantize_offset
                f_x = pydaw_clip_min(f_x, shared.AUDIO_ITEM_HANDLE_SIZE)
                f_x = f_item.quantize(f_x)
                f_x -= f_item.quantize_offset
                f_item.length_handle.setPos(
                    f_x - shared.AUDIO_ITEM_HANDLE_SIZE,
                    shared.REGION_EDITOR_TRACK_HEIGHT - shared.AUDIO_ITEM_HANDLE_HEIGHT)
        elif self.is_start_resizing:
            for f_item in shared.SEQUENCER.get_selected():
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
                    f_x, shared.REGION_EDITOR_TRACK_HEIGHT -
                        shared.AUDIO_ITEM_HANDLE_HEIGHT)
        elif self.is_stretching:
            for f_item in shared.SEQUENCER.audio_items:
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
                        (shared.REGION_EDITOR_TRACK_HEIGHT * 0.5) -
                        (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5))
        else:
            QGraphicsRectItem.mouseMoveEvent(self, a_event)
            if SEQ_QUANTIZE:
                f_max_x = (pydaw_get_current_region_length() *
                    SEQUENCER_PX_PER_BEAT) - SEQUENCER_QUANTIZE_PX
            else:
                f_max_x = (pydaw_get_current_region_length() *
                    SEQUENCER_PX_PER_BEAT) - shared.AUDIO_ITEM_HANDLE_SIZE
            f_new_lane, f_ignored = self.y_pos_to_lane_number(
                a_event.scenePos().y())
            f_lane_offset = f_new_lane - self.audio_item.track_num
            for f_item in shared.SEQUENCER.get_selected():
                f_pos_x = f_item.pos().x()
                f_pos_x = pydaw_clip_value(f_pos_x, 0.0, f_max_x)
                f_pos_y = self.lane_number_to_y_pos(
                    f_lane_offset + f_item.audio_item.track_num)
                f_pos_x = f_item.quantize_scene(f_pos_x)
                f_item.setPos(f_pos_x, f_pos_y)
                if not f_item.is_moving:
                    f_item.is_moving = True
                    # Triggers a bug in Qt5 where the pixmaps in a long
                    # tiled item disappear
                    #f_item.setGraphicsEffect(QGraphicsOpacityEffect())

    def mouseReleaseEvent(self, a_event):
        if libmk.IS_PLAYING or self.event_pos_orig is None:
            return
        f_was_resizing = self.is_resizing
        QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        QApplication.restoreOverrideCursor()
        #Set to True when testing, set to False for better UI performance...
        f_reset_selection = True
        f_did_change = False
        f_was_stretching = False
        f_stretched_items = []
        f_event_pos = a_event.pos().x()
        f_event_diff = f_event_pos - self.event_pos_orig
        f_was_copying = self.is_copying
        if f_was_copying:
            a_event.accept()
        for f_audio_item in shared.SEQUENCER.get_selected():
            f_item = f_audio_item.audio_item
            f_pos_x = pydaw_util.pydaw_clip_min(f_audio_item.pos().x(), 0.0)
            if f_audio_item.is_resizing:
                f_x = (f_audio_item.width_orig + f_event_diff +
                    f_audio_item.quantize_offset)
                f_x = pydaw_clip_min(f_x, shared.AUDIO_ITEM_HANDLE_SIZE)
                f_x = f_audio_item.quantize(f_x)
                f_x -= f_audio_item.quantize_offset
                f_audio_item.setRect(
                    0.0, 0.0, f_x, shared.REGION_EDITOR_TRACK_HEIGHT)
                f_item.length_beats = f_x /SEQUENCER_PX_PER_BEAT
                print(f_item.length_beats)
                f_did_change = True
            elif f_audio_item.is_start_resizing:
                f_x = f_audio_item.start_handle.scenePos().x()
                f_x = pydaw_clip_min(f_x, 0.0)
                f_x = self.quantize_all(f_x)
                if f_x < f_audio_item.sample_start_offset_px:
                    f_x = f_audio_item.sample_start_offset_px
                f_old_start = f_item.start_beat
                f_item.start_beat = self.pos_to_musical_time(f_x)
                f_item.start_offset = ((f_x -
                    f_audio_item.start_handle_scene_min) /
                    (f_audio_item.start_handle_scene_max -
                    f_audio_item.start_handle_scene_min)) * \
                    f_item.length_beats
                f_item.start_offset = pydaw_clip_min(
                    f_item.start_offset, 0.0)
                f_item.length_beats -= f_item.start_beat - f_old_start
            elif f_audio_item.is_stretching and \
            f_item.time_stretch_mode >= 2:
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
                f_audio_item.setRect(0.0, 0.0, f_x, shared.REGION_EDITOR_TRACK_HEIGHT)
            else:
                f_item.modified = True
                f_pos_y = f_audio_item.pos().y()
                if f_audio_item.is_copying:
                    f_reset_selection = True
                    f_item_old = f_item.clone()
                    shared.CURRENT_REGION.add_item(f_item_old)
                else:
                    f_audio_item.set_brush(f_item.track_num)
                f_pos_x = self.quantize_all(f_pos_x)
                f_item.track_num, f_pos_y = self.y_pos_to_lane_number(f_pos_y)
                f_audio_item.setPos(f_pos_x, f_pos_y)
                f_item.start_beat = f_audio_item.pos_to_musical_time(f_pos_x)
                f_did_change = True
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
        if f_was_resizing:
            global LAST_ITEM_LENGTH
            LAST_ITEM_LENGTH = self.audio_item.length_beats

        if f_did_change:
            #f_audio_items.deduplicate_items()
            if f_was_stretching:
                pass
            shared.PROJECT.save_region(shared.CURRENT_REGION)
            shared.PROJECT.commit(_("Update sequencer items"))
        shared.SEQUENCER.set_selected_strings()
        shared.REGION_SETTINGS.open_region()

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
        self.scene.setBackgroundBrush(pydaw_widgets.SCENE_BACKGROUND_BRUSH)
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

        self.menu = QMenu(self)
        self.atm_menu = QMenu(self)

        self.copy_action = self.menu.addAction(_("Copy"))
        self.copy_action.triggered.connect(self.copy_selected)
        self.copy_action.setShortcut(QKeySequence.Copy)
        self.addAction(self.copy_action)
        self.atm_menu.addAction(self.copy_action)

        self.cut_action = self.menu.addAction(_("Cut"))
        self.cut_action.triggered.connect(self.cut_selected)
        self.cut_action.setShortcut(QKeySequence.Cut)
        self.addAction(self.cut_action)

        self.paste_action = self.atm_menu.addAction(_("Paste"))
        self.paste_action.triggered.connect(self.paste_clipboard)

        self.paste_orig_action = self.menu.addAction(
            _("Paste to Original Track"))
        self.paste_orig_action.triggered.connect(self.paste_clipboard)

        self.paste_ctrl_action = self.atm_menu.addAction(
            _("Paste Plugin Control"))
        self.paste_ctrl_action.triggered.connect(self.paste_atm_point)

        self.track_atm_menu = self.atm_menu.addMenu(
            _("All Plugins for Track"))
        self.track_atm_clipboard = []

        self.copy_track_region_action = self.track_atm_menu.addAction(
            _("Copy Region"))
        self.copy_track_region_action.triggered.connect(
            self.copy_track_region)
        self.paste_track_region_action = self.track_atm_menu.addAction(
            _("Paste Region"))
        self.paste_track_region_action.triggered.connect(
            self.paste_track_region)
        self.track_atm_menu.addSeparator()
        self.clear_track_region_action = self.track_atm_menu.addAction(
            _("Clear Region"))
        self.clear_track_region_action.triggered.connect(
            self.clear_track_region)

        self.atm_clear_menu = self.atm_menu.addMenu(_("Clear All"))

        #self.clear_port_action = self.atm_clear_menu.addAction(
        #    _("Current Control"))
        #self.clear_port_action.triggered.connect(self.clear_port)

        self.atm_clear_menu.addSeparator()
        self.clear_plugin_action = self.atm_clear_menu.addAction(
            _("Current Plugin"))
        self.clear_plugin_action.triggered.connect(self.clear_plugin)

        self.atm_clear_menu.addSeparator()
        self.clear_track_action = self.atm_clear_menu.addAction(
            _("Track"))
        self.clear_track_action.triggered.connect(self.clear_track)

        self.transform_atm_action = self.atm_menu.addAction(_("Transform..."))
        self.transform_atm_action.triggered.connect(self.transform_atm)

        self.lfo_atm_action = self.atm_menu.addAction(_("LFO Tool..."))
        self.lfo_atm_action.triggered.connect(self.lfo_atm)

        self.atm_menu.addSeparator()

        self.break_atm_action = self.atm_menu.addAction(
            _("Break after selected automation point(s)"))
        self.break_atm_action.triggered.connect(self.break_atm)
        self.break_atm_action.setShortcut(QKeySequence.fromString("CTRL+B"))
        self.addAction(self.break_atm_action)

        self.unbreak_atm_action = self.atm_menu.addAction(
            _("Un-break after selected automation point(s)"))
        self.unbreak_atm_action.triggered.connect(self.unbreak_atm)
        self.unbreak_atm_action.setShortcut(
            QKeySequence.fromString("CTRL+SHIFT+B"))
        self.addAction(self.unbreak_atm_action)

        self.atm_menu.addSeparator()

        self.delete_action = self.menu.addAction(_("Delete"))
        self.delete_action.triggered.connect(self.delete_selected)
        self.delete_action.setShortcut(QKeySequence.Delete)
        self.addAction(self.delete_action)
        self.atm_menu.addAction(self.delete_action)

        self.menu.addSeparator()

        self.takes_menu = self.menu.addMenu(_("Takes"))
        self.takes_menu.triggered.connect(self.takes_menu_triggered)

        self.unlink_selected_action = self.menu.addAction(
            _("Create New Take for Item(s)"))
        self.unlink_selected_action.setShortcut(
            QKeySequence.fromString("CTRL+U"))
        self.unlink_selected_action.triggered.connect(
            self.on_auto_unlink_selected)
        self.addAction(self.unlink_selected_action)

        self.unlink_unique_action = self.menu.addAction(
            _("Create New Take for Unique Item(s)"))
        self.unlink_unique_action.setShortcut(
            QKeySequence.fromString("ALT+U"))
        self.unlink_unique_action.triggered.connect(self.on_auto_unlink_unique)
        self.addAction(self.unlink_unique_action)

        self.unlink_action = self.menu.addAction(
            _("Create Named Take for Single Item..."))
        self.unlink_action.triggered.connect(self.on_unlink_item)
        self.addAction(self.unlink_action)

        self.menu.addSeparator()

        self.rename_action = self.menu.addAction(
            _("Rename Selected Item(s)..."))
        self.rename_action.triggered.connect(self.on_rename_items)
        self.addAction(self.rename_action)

        self.transpose_action = self.menu.addAction(_("Transpose..."))
        self.transpose_action.triggered.connect(self.transpose_dialog)
        self.addAction(self.transpose_action)

        self.glue_action = self.menu.addAction(_("Glue Selected"))
        self.glue_action.triggered.connect(self.glue_selected)
        self.glue_action.setShortcut(
            QKeySequence.fromString("CTRL+G"))
        self.addAction(self.glue_action)
        self.context_menu_enabled = True

    def break_atm(self, checked=False, new_val=1):
        if REGION_EDITOR_MODE != 1:
            return
        assert new_val in (0, 1), "Unexpected value '{}'".format(new_val)
        points = [x.item for x in self.get_selected_points()]
        if points:
            for point in points:
                point.break_after = new_val
            self.automation_save_callback()

    def unbreak_atm(self):
        self.break_atm(new_val=0)

    def clear_port(self):
        if not self.current_coord:
            return
        f_track = self.current_coord[0]
        f_track_port_num, f_track_index = shared.TRACK_PANEL.has_automation(f_track)
        if f_track_port_num is None:
            QMessageBox.warning(
                self, _("Error"),
                _("No automation selected for this track"))
            return
        f_index, f_plugin = shared.TRACK_PANEL.get_atm_params(f_track)
        ATM_REGION.clear_port(f_index, f_track_port_num)
        self.automation_save_callback()

    def clear_plugin(self):
        if not self.current_coord:
            return
        f_track = self.current_coord[0]
        f_track_port_num, f_track_index = shared.TRACK_PANEL.has_automation(f_track)
        if f_track_port_num is None:
            QMessageBox.warning(
                self, _("Error"),
                _("No automation selected for this track"))
            return
        f_index, f_plugin = shared.TRACK_PANEL.get_atm_params(f_track)
        ATM_REGION.clear_plugins([f_index])
        self.automation_save_callback()

    def clear_track(self):
        if not self.current_coord:
            return
        f_track = self.current_coord[0]
        f_plugins = shared.PROJECT.get_track_plugin_uids(f_track)
        if not f_plugins:
            return
        ATM_REGION.clear_plugins(f_plugins)
        self.automation_save_callback()

    def copy_track_region(self):
        if not self.current_coord:
            return
        f_range = self.get_loop_pos()
        if not f_range:
            return
        f_start, f_end = f_range
        f_track = self.current_coord[0]
        f_plugins = shared.PROJECT.get_track_plugin_uids(f_track)
        if not f_plugins:
            return
        self.track_atm_clipboard = ATM_REGION.copy_range_by_plugins(
            f_start, f_end, f_plugins)
        self.automation_save_callback()

    def paste_track_region(self):
        if not self.current_coord or not self.track_atm_clipboard:
            return
        f_beat = self.quantize(self.current_coord[1])
        for f_point in (x.clone() for x in self.track_atm_clipboard):
            f_point.beat += f_beat
            ATM_REGION.add_point(f_point)
        self.automation_save_callback()

    def clear_track_region(self):
        if not self.current_coord:
            return
        f_range = self.get_loop_pos()
        if not f_range:
            return
        f_start, f_end = f_range
        f_track, f_beat = self.current_coord[:2]
        f_plugins = shared.PROJECT.get_track_plugin_uids(f_track)
        if not f_plugins:
            return
        ATM_REGION.clear_range_by_plugins(f_start, f_end, f_plugins)
        self.automation_save_callback()

    def takes_menu_triggered(self, a_action):
        f_uid = self.current_item.audio_item.item_uid
        f_new_uid = a_action.item_uid
        for f_item in self.get_selected_items():
            if f_item.audio_item.item_uid == f_uid:
                f_item_obj = f_item.audio_item
                shared.CURRENT_REGION.remove_item_ref(f_item_obj)
                f_item_obj.uid = f_new_uid
                self.selected_item_strings.add(str(f_item_obj))
                f_item_ref = f_item_obj.clone()
                f_item_ref.item_uid = f_new_uid
                shared.CURRENT_REGION.add_item_ref_by_uid(f_item_ref)
        shared.PROJECT.save_region(shared.CURRENT_REGION)
        shared.PROJECT.commit(_("Change active take"))
        shared.REGION_SETTINGS.open_region()

    def populate_takes_menu(self):
        self.takes_menu.clear()
        if self.current_item:
            f_takes = shared.PROJECT.get_takes()
            f_take_list = f_takes.get_take(
                self.current_item.audio_item.item_uid)
            if f_take_list:
                f_items_dict = shared.PROJECT.get_items_dict()
                for f_uid in f_take_list[1]:
                    f_name = f_items_dict.get_name_by_uid(f_uid)
                    f_action = self.takes_menu.addAction(f_name)
                    f_action.item_uid = f_uid

    def show_context_menu(self):
        if libmk.IS_PLAYING:
            return
        if not self.context_menu_enabled:
            self.context_menu_enabled = True
            return
        if REGION_EDITOR_MODE == 0:
            self.populate_takes_menu()
            self.menu.exec_(QCursor.pos())
        elif REGION_EDITOR_MODE == 1:
            self.atm_menu.exec_(QCursor.pos())
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
        if libmk.IS_PLAYING:
            return
        f_pos = self.mapToScene(a_event.pos())
        self.current_coord = self.get_item_coord(f_pos)

        if f_pos.x() > self.max_x:
            return

        if self.check_header(f_pos):
            if a_event.button() == QtCore.Qt.LeftButton:
                f_beat = int(f_pos.x() / SEQUENCER_PX_PER_BEAT)
                global_set_playback_pos(f_beat)
            return

        if a_event.button() == QtCore.Qt.RightButton:
            if self.current_coord:
                if REGION_EDITOR_MODE == 0:
                    self.current_item = self.get_item(f_pos)
                    if self.current_item and \
                    not self.current_item.isSelected():
                        self.scene.clearSelection()
                        self.current_item.setSelected(True)
                        self.selected_item_strings = {
                            self.current_item.get_selected_string()}
                self.show_context_menu()
        elif REGION_EDITOR_MODE == 0:
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
                f_pos_y = f_pos.y() - REGION_EDITOR_HEADER_HEIGHT
                f_beat = float(f_pos_x // SEQUENCER_PX_PER_BEAT)
                f_track = int(f_pos_y // shared.REGION_EDITOR_TRACK_HEIGHT)
                f_item_name = "{}-1".format(shared.TRACK_NAMES[f_track])
                f_uid = shared.PROJECT.create_empty_item(f_item_name)
                f_item_ref = project.pydaw_sequencer_item(
                    f_track, f_beat, LAST_ITEM_LENGTH, f_uid)
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

        elif REGION_EDITOR_MODE == 1:
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
                    f_point = pydaw_atm_point(
                        f_beat, f_port, f_val,
                        *shared.TRACK_PANEL.get_atm_params(f_track))
                    ATM_REGION.add_point(f_point)
                    point_item = self.draw_point(f_point)
                    point_item.setSelected(True)
                    self.current_atm_point = point_item
                    QGraphicsView.mousePressEvent(self, a_event)
                    return
        a_event.accept()
        QGraphicsView.mousePressEvent(self, a_event)

    def sceneMouseMoveEvent(self, a_event):
        QGraphicsScene.mouseMoveEvent(self.scene, a_event)
        if REGION_EDITOR_MODE == 0:
            if REGION_EDITOR_DELETE_MODE:
                f_item = self.get_item(a_event.scenePos())
                if f_item and not f_item.audio_item in self.deleted_items:
                    f_item.hide()
                    self.deleted_items.append(f_item.audio_item)
        elif REGION_EDITOR_MODE == 1:
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
        if REGION_EDITOR_MODE == 0:
            if REGION_EDITOR_DELETE_MODE:
                region_editor_set_delete_mode(False)
                self.scene.clearSelection()
                self.selected_item_strings = set()
                for f_item in self.deleted_items:
                    shared.CURRENT_REGION.remove_item_ref(f_item)
                shared.PROJECT.save_region(shared.CURRENT_REGION)
                shared.PROJECT.commit("Delete sequencer items")
                self.open_region()
                libmk.clean_wav_pool()
            else:
                QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        elif REGION_EDITOR_MODE == 1:
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
        f_pos_y = a_pos.y() - REGION_EDITOR_HEADER_HEIGHT
        if a_clip or (
        f_pos_x > 0 and
        f_pos_y > 0 and
        f_pos_y < REGION_EDITOR_TOTAL_HEIGHT):
            f_pos_x = pydaw_util.pydaw_clip_min(f_pos_x, 0.0)
            f_pos_y = pydaw_util.pydaw_clip_value(
                f_pos_y, 0.0, REGION_EDITOR_TOTAL_HEIGHT)
            f_track_height = shared.REGION_EDITOR_TRACK_HEIGHT - ATM_POINT_DIAMETER
            f_track = int(f_pos_y / shared.REGION_EDITOR_TRACK_HEIGHT)
            f_val = (1.0 - ((f_pos_y - (f_track * shared.REGION_EDITOR_TRACK_HEIGHT))
                / f_track_height)) * 127.0
            f_beat = f_pos_x / SEQUENCER_PX_PER_BEAT
            return f_track, round(f_beat, 6), round(f_val, 6)
        else:
            return None

    def delete_selected_atm(self, a_track):
        self.copy_selected()
        f_selected = list(self.get_selected_points(a_track))
        self.scene.clearSelection()
        self.selected_point_strings = set()
        for f_point in f_selected:
            self.automation_points.remove(f_point)
            ATM_REGION.remove_point(f_point.item)
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
        if REGION_EDITOR_MODE == 0:
            shared.SEQUENCER.setDragMode(QGraphicsView.NoDrag)
        elif REGION_EDITOR_MODE == 1:
            shared.SEQUENCER.setDragMode(QGraphicsView.RubberBandDrag)
        self.enabled = False
        global ATM_REGION, CACHED_SEQ_LEN
        ATM_REGION = shared.PROJECT.get_atm_region()
        f_items_dict = shared.PROJECT.get_items_dict()
        f_scrollbar = self.horizontalScrollBar()
        f_scrollbar_value = f_scrollbar.value()
        self.setUpdatesEnabled(False)
        self.clear_drawn_items()
        self.ignore_selection_change = True
        #, key=lambda x: x.bar_num,
        CACHED_SEQ_LEN = pydaw_get_current_region_length()
        for f_item in sorted(shared.CURRENT_REGION.items, reverse=True):
            if f_item.start_beat < pydaw_get_current_region_length():
                f_item_name = f_items_dict.get_name_by_uid(f_item.item_uid)
                f_new_item = self.draw_item(f_item_name, f_item)
                if f_new_item.get_selected_string() in \
                self.selected_item_strings:
                    f_new_item.setSelected(True)
        self.ignore_selection_change = False
        if REGION_EDITOR_MODE == 1:
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
                points = ATM_REGION.get_points(f_index, f_port)
                if points:
                    point_items = [self.draw_point(x) for x in points]
                    self.draw_atm_lines(f_track, point_items)

    def draw_atm_lines(self, a_track_num, a_points):
        plugin_uid = a_points[0].item.index
        path = QPainterPath()
        point = a_points[0]
        pos = point.scenePos()
        x = pos.x() + ATM_POINT_RADIUS
        y = pos.y() + ATM_POINT_RADIUS
        path.moveTo(0.0, y)
        path.lineTo(x, y)
        break_after = point.item.break_after

        for point in a_points[1:]:
            pos = point.scenePos()
            x = pos.x() + ATM_POINT_RADIUS
            y = pos.y() + ATM_POINT_RADIUS
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

    def delete_selected(self):
        if self.check_running():
            return
        if REGION_EDITOR_MODE == 0:
            f_item_list = self.get_selected()
            self.clear_selected_item_strings()
            if f_item_list:
                for f_item in f_item_list:
                    shared.CURRENT_REGION.remove_item_ref(f_item.audio_item)
                shared.PROJECT.save_region(shared.CURRENT_REGION)
                shared.PROJECT.commit(_("Delete item(s)"))
                shared.REGION_SETTINGS.open_region()
                libmk.clean_wav_pool()
        elif REGION_EDITOR_MODE == 1:
            for f_point in self.get_selected_points():
                ATM_REGION.remove_point(f_point.item)
            self.automation_save_callback()

    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip(dn_strings.sequencer)
        else:
            self.setToolTip("")
        for f_item in self.audio_items:
            f_item.set_tooltips(a_on)

    def resizeEvent(self, a_event):
        QGraphicsView.resizeEvent(self, a_event)

    def sceneContextMenuEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        QGraphicsScene.contextMenuEvent(self.scene, a_event)
        self.show_context_menu()

    def highlight_selected(self):
        self.setUpdatesEnabled(False)
        self.has_selected = False
        if REGION_EDITOR_MODE == 0:
            for f_item in self.audio_items:
                f_item.set_brush()
                self.has_selected = True
        elif REGION_EDITOR_MODE == 1:
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
        if libmk.IS_PLAYING:
            return True
        return False

    def sceneDropEvent(self, a_event):
        f_pos = a_event.scenePos()
        if shared.AUDIO_ITEMS_TO_DROP:
            self.add_items(f_pos, shared.AUDIO_ITEMS_TO_DROP)
        elif MIDI_FILES_TO_DROP:
            f_midi_path = MIDI_FILES_TO_DROP[0]
            f_beat, f_lane_num = self.pos_to_beat_and_track(f_pos)
            f_midi = project.DawNextMidiFile(f_midi_path, shared.PROJECT)
            shared.PROJECT.import_midi_file(f_midi, f_beat, f_lane_num)
            shared.PROJECT.commit("Import MIDI file")
            shared.REGION_SETTINGS.open_region()

    def quantize(self, a_beat):
        if SEQ_QUANTIZE:
            return int(a_beat * SEQ_QUANTIZE_AMT) / SEQ_QUANTIZE_AMT
        else:
            return a_beat

    def pos_to_beat_and_track(self, a_pos):
        f_beat_frac = (a_pos.x() / SEQUENCER_PX_PER_BEAT)
        f_beat_frac = pydaw_clip_min(f_beat_frac, 0.0)
        f_beat_frac = self.quantize(f_beat_frac)

        f_lane_num = int((a_pos.y() - REGION_EDITOR_HEADER_HEIGHT) /
            shared.REGION_EDITOR_TRACK_HEIGHT)
        f_lane_num = pydaw_clip_value(
            f_lane_num, 0, project.TRACK_COUNT_ALL - 1)

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

        libmk.APP.setOverrideCursor(QtCore.Qt.WaitCursor)

        f_beat_frac, f_track_num = self.pos_to_beat_and_track(a_pos)

        f_seconds_per_beat = (60.0 /
            shared.CURRENT_REGION.get_tempo_at_pos(f_beat_frac))

        f_restart = False

        if a_single_item:
            lane_num = 0
            f_item_name = "{}-1".format(shared.TRACK_NAMES[f_track_num])
            f_item_uid = shared.PROJECT.create_empty_item(f_item_name)
            f_items = shared.PROJECT.get_item_by_uid(f_item_uid)
            f_item_ref = project.pydaw_sequencer_item(
                f_track_num, f_beat_frac, 1.0, f_item_uid)

        for f_file_name in a_item_list:
            libmk.APP.processEvents()
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

                f_uid = libmk.PROJECT.get_wav_uid_by_name(f_file_name_str)
                f_graph = libmk.PROJECT.get_sample_graph_by_uid(f_uid)
                f_delta = datetime.timedelta(
                    seconds=f_graph.length_in_seconds)
                if not f_restart and libmk.add_entropy(f_delta):
                    f_restart = True
                f_length = f_graph.length_in_seconds / f_seconds_per_beat
                if a_single_item:
                    f_item = pydaw_audio_item(
                        f_uid, a_start_bar=0, a_start_beat=0.0,
                        a_lane_num=lane_num)
                    lane_num += 1
                    f_items.add_item(f_index, f_item)
                    if f_length > f_item_ref.length_beats:
                        f_item_ref.length_beats = f_length
                else:
                    f_item_ref = project.pydaw_sequencer_item(
                        f_track_num, f_beat_frac, f_length, f_item_uid)
                    shared.CURRENT_REGION.add_item_ref_by_uid(f_item_ref)
                    f_item = pydaw_audio_item(
                        f_uid, a_start_bar=0, a_start_beat=0.0, a_lane_num=0)
                    f_items.add_item(f_index, f_item)
                    shared.PROJECT.save_item_by_uid(f_item_uid, f_items)
                    f_track_num += 1
                    if f_track_num >= project.TRACK_COUNT_ALL:
                        break

        if a_single_item:
            shared.CURRENT_REGION.add_item_ref_by_uid(f_item_ref)
            shared.PROJECT.save_item_by_uid(f_item_uid, f_items)

        shared.PROJECT.save_region(shared.CURRENT_REGION, a_notify=not f_restart)
        shared.PROJECT.commit("Added audio items")
        shared.REGION_SETTINGS.open_region()
        self.last_open_dir = os.path.dirname(f_file_name_str)

        if f_restart:
            libmk.restart_engine()

        libmk.APP.restoreOverrideCursor()

    def get_beat_value(self):
        return self.playback_pos

    def set_playback_pos(self, a_beat=0.0):
        f_right = self.sceneRect().right()
        self.playback_pos = float(a_beat)
        if self.playback_pos > f_right:
            return
        f_pos = (self.playback_pos * SEQUENCER_PX_PER_BEAT)
        self.playback_cursor.setPos(f_pos, 0.0)
        if libmk.IS_PLAYING and shared.REGION_SETTINGS.follow_checkbox.isChecked():
            f_port_rect = self.viewport().rect()
            f_rect = self.mapToScene(f_port_rect).boundingRect()
            if not (f_pos > f_rect.left() and f_pos < f_rect.right()):
                f_pos = int(self.playback_pos) * SEQUENCER_PX_PER_BEAT
                shared.REGION_SETTINGS.scrollbar.setValue(int(f_pos))

    def start_playback(self):
        self.playback_pos_orig = self.playback_pos
        if REGION_EDITOR_MODE == 0:
            self.set_selected_strings()
        elif REGION_EDITOR_MODE == 1:
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
        if not libmk.IS_PLAYING and \
        a_event.button() != QtCore.Qt.RightButton:
            f_beat = int(a_event.scenePos().x() / SEQUENCER_PX_PER_BEAT)
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

    def header_time_modify(self):
        def ok_handler():
            f_marker = project.pydaw_tempo_marker(
                self.header_event_pos, f_tempo.value(),
                f_tsig_num.value(), int(str(f_tsig_den.currentText())))
            shared.CURRENT_REGION.set_marker(f_marker)
            shared.PROJECT.save_region(shared.CURRENT_REGION)
            shared.PROJECT.commit(_("Set tempo marker"))
            shared.REGION_SETTINGS.open_region()
            f_window.close()

        def cancel_handler():
            f_marker = shared.CURRENT_REGION.has_marker(self.header_event_pos, 2)
            if f_marker and self.header_event_pos:
                shared.CURRENT_REGION.delete_marker(f_marker)
                shared.PROJECT.save_region(shared.CURRENT_REGION)
                shared.PROJECT.commit(_("Delete tempo marker"))
                shared.REGION_SETTINGS.open_region()
            f_window.close()

        f_window = QDialog(shared.MAIN_WINDOW)
        f_window.setWindowTitle(_("Tempo / Time Signature"))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)

        f_marker = shared.CURRENT_REGION.has_marker(self.header_event_pos, 2)

        f_tempo = QSpinBox()
        f_tempo.setRange(30, 240)
        f_layout.addWidget(QLabel(_("Tempo")), 0, 0)
        f_layout.addWidget(f_tempo, 0, 1)
        f_tsig_layout = QHBoxLayout()
        f_layout.addLayout(f_tsig_layout, 1, 1)
        f_tsig_num = QSpinBox()
        f_tsig_num.setRange(1, 16)
        f_layout.addWidget(QLabel(_("Time Signature")), 1, 0)
        f_tsig_layout.addWidget(f_tsig_num)
        f_tsig_layout.addWidget(QLabel("/"))

        f_tsig_den = QComboBox()
        f_tsig_den.setMinimumWidth(60)
        f_tsig_layout.addWidget(f_tsig_den)
        f_tsig_den.addItems(["2", "4", "8", "16"])

        if f_marker:
            f_tempo.setValue(f_marker.tempo)
            f_tsig_num.setValue(f_marker.tsig_num)
            f_tsig_den.setCurrentIndex(
                f_tsig_den.findText(str(f_marker.tsig_den)))
        else:
            f_tempo.setValue(128)
            f_tsig_num.setValue(4)
            f_tsig_den.setCurrentIndex(1)

        f_ok = QPushButton(_("Save"))
        f_ok.pressed.connect(ok_handler)
        f_layout.addWidget(f_ok, 6, 0)
        if self.header_event_pos:
            f_cancel = QPushButton(_("Delete"))
        else:
            f_cancel = QPushButton(_("Cancel"))
        f_cancel.pressed.connect(cancel_handler)
        f_layout.addWidget(f_cancel, 6, 1)
        f_window.exec_()

    def header_marker_modify(self):
        def ok_handler():
            f_marker = project.pydaw_sequencer_marker(
                self.header_event_pos, f_text.text())
            shared.CURRENT_REGION.set_marker(f_marker)
            shared.PROJECT.save_region(shared.CURRENT_REGION)
            shared.PROJECT.commit(_("Add text marker"))
            shared.REGION_SETTINGS.open_region()
            f_window.close()

        def cancel_handler():
            f_marker = shared.CURRENT_REGION.has_marker(self.header_event_pos, 3)
            if f_marker:
                shared.CURRENT_REGION.delete_marker(f_marker)
                shared.PROJECT.save_region(shared.CURRENT_REGION)
                shared.PROJECT.commit(_("Delete text marker"))
                shared.REGION_SETTINGS.open_region()
            f_window.close()

        f_window = QDialog(shared.MAIN_WINDOW)
        f_window.setWindowTitle(_("Marker"))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)

        f_marker = shared.CURRENT_REGION.has_marker(self.header_event_pos, 3)

        f_text = QLineEdit()
        f_text.setMaxLength(21)

        if f_marker:
            f_text.setText(f_marker.text)

        f_layout.addWidget(QLabel(_("Text")), 0, 0)
        f_layout.addWidget(f_text, 0, 1)
        f_ok_cancel_layout = QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout, 6, 1)
        f_ok = QPushButton(_("Save"))
        f_ok.pressed.connect(ok_handler)
        f_ok_cancel_layout.addWidget(f_ok)
        if shared.CURRENT_REGION.has_marker(self.header_event_pos, 3):
            f_cancel = QPushButton(_("Delete"))
        else:
            f_cancel = QPushButton(_("Cancel"))
        f_cancel.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec_()

    def header_loop_start(self):
        f_tsig_beats = shared.CURRENT_REGION.get_tsig_at_pos(self.header_event_pos)
        if shared.CURRENT_REGION.loop_marker:
            f_end = pydaw_util.pydaw_clip_min(
                shared.CURRENT_REGION.loop_marker.beat,
                self.header_event_pos + f_tsig_beats)
        else:
            f_end = self.header_event_pos + f_tsig_beats

        f_marker = project.pydaw_loop_marker(f_end, self.header_event_pos)
        shared.CURRENT_REGION.set_loop_marker(f_marker)
        shared.PROJECT.save_region(shared.CURRENT_REGION)
        shared.PROJECT.commit(_("Set region start"))
        shared.REGION_SETTINGS.open_region()

    def header_loop_end(self):
        f_tsig_beats = shared.CURRENT_REGION.get_tsig_at_pos(self.header_event_pos)
        shared.CURRENT_REGION.loop_marker.beat = pydaw_util.pydaw_clip_min(
            self.header_event_pos, f_tsig_beats)
        shared.CURRENT_REGION.loop_marker.start_beat = pydaw_util.pydaw_clip_max(
            shared.CURRENT_REGION.loop_marker.start_beat,
            shared.CURRENT_REGION.loop_marker.beat - f_tsig_beats)
        shared.PROJECT.save_region(shared.CURRENT_REGION)
        shared.PROJECT.commit(_("Set region end"))
        shared.REGION_SETTINGS.open_region()

    def headerContextMenuEvent(self, a_event):
        self.context_menu_enabled = False
        self.header_event_pos = int(a_event.pos().x() / SEQUENCER_PX_PER_BEAT)
        f_menu = QMenu(self)
        f_marker_action = f_menu.addAction(_("Text Marker..."))
        f_marker_action.triggered.connect(self.header_marker_modify)
        f_time_modify_action = f_menu.addAction(_("Time/Tempo Marker..."))
        f_time_modify_action.triggered.connect(self.header_time_modify)
        f_menu.addSeparator()
        f_loop_start_action = f_menu.addAction(_("Set Region Start"))
        f_loop_start_action.triggered.connect(self.header_loop_start)
        if shared.CURRENT_REGION.loop_marker:
            f_loop_end_action = f_menu.addAction(_("Set Region End"))
            f_loop_end_action.triggered.connect(self.header_loop_end)
            f_select_region = f_menu.addAction(_("Select Items in Region"))
            f_select_region.triggered.connect(self.select_region_items)
            f_copy_region_action = f_menu.addAction(_("Copy Region"))
            f_copy_region_action.triggered.connect(self.copy_region)
            if self.region_clipboard:
                f_insert_region_action = f_menu.addAction(_("Insert Region"))
                f_insert_region_action.triggered.connect(self.insert_region)
        f_menu.exec_(QCursor.pos())

    def copy_region(self):
        f_region_start = shared.CURRENT_REGION.loop_marker.start_beat
        f_region_end = shared.CURRENT_REGION.loop_marker.beat
        f_region_length = f_region_end - f_region_start
        f_list = [x.audio_item.clone() for x in self.get_region_items()]
        f_atm_list = ATM_REGION.copy_range_all(f_region_start, f_region_end)
        for f_item in f_list:
            f_item.start_beat -= f_region_start
        for f_point in f_atm_list:
            f_point.beat -= f_region_start
        self.region_clipboard = (f_region_length, f_list, f_atm_list)

    def insert_region(self):
        f_region_length, f_list, f_atm_list = self.region_clipboard
        f_list = [x.clone() for x in f_list]
        f_atm_list = [x.clone() for x in f_atm_list]
        shared.CURRENT_REGION.insert_space(self.header_event_pos, f_region_length)
        for f_item in f_list:
            f_item.start_beat += self.header_event_pos
            shared.CURRENT_REGION.add_item_ref_by_uid(f_item)
        for f_point in f_atm_list:
            f_point.beat += self.header_event_pos
            ATM_REGION.add_point(f_point)
        self.automation_save_callback()
        shared.PROJECT.save_region(shared.CURRENT_REGION)
        shared.PROJECT.commit(_("Insert region"))
        shared.REGION_SETTINGS.open_region()

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
        f_size = SEQUENCER_PX_PER_BEAT * f_region_length
        self.max_x = f_size
        self.setSceneRect(
            -3.0, 0.0, f_size + self.width() + 3.0, REGION_EDITOR_TOTAL_HEIGHT)
        self.header = QGraphicsRectItem(
            0, 0, f_size, REGION_EDITOR_HEADER_HEIGHT)
        self.header.setZValue(1500.0)
        self.header.setBrush(shared.SEQUENCER_HEADER_BRUSH)
        self.header.mousePressEvent = self.header_click_event
        self.header.contextMenuEvent = self.headerContextMenuEvent
        self.scene.addItem(self.header)
        for f_marker in shared.CURRENT_REGION.get_markers():
            if f_marker.type == 1:
                self.loop_start = f_marker.start_beat
                self.loop_end = f_marker.beat
                f_x = f_marker.start_beat * SEQUENCER_PX_PER_BEAT
                f_start = QGraphicsLineItem(
                    f_x, 0, f_x, REGION_EDITOR_HEADER_HEIGHT, self.header)
                f_start.setPen(shared.START_PEN)

                f_x = f_marker.beat * SEQUENCER_PX_PER_BEAT
                f_end = QGraphicsLineItem(
                    f_x, 0, f_x, REGION_EDITOR_HEADER_HEIGHT, self.header)
                f_end.setPen(shared.END_PEN)
            elif f_marker.type == 2:
                f_text = "{} : {}/{}".format(
                    f_marker.tempo, f_marker.tsig_num, f_marker.tsig_den)
                f_item = QGraphicsSimpleTextItem(f_text, self.header)
                f_item.setBrush(QtCore.Qt.white)
                f_item.setPos(
                    f_marker.beat * SEQUENCER_PX_PER_BEAT,
                    REGION_EDITOR_HEADER_ROW_HEIGHT)
                self.draw_region(f_marker)
            elif f_marker.type == 3:
                f_item = QGraphicsSimpleTextItem(
                    f_marker.text, self.header)
                f_item.setBrush(QtCore.Qt.white)
                f_item.setPos(
                    f_marker.beat * SEQUENCER_PX_PER_BEAT,
                    REGION_EDITOR_HEADER_ROW_HEIGHT * 2)
            else:
                assert False, "Invalid marker type"

        f_total_height = (REGION_EDITOR_TRACK_COUNT *
            (shared.REGION_EDITOR_TRACK_HEIGHT)) + REGION_EDITOR_HEADER_HEIGHT
        self.playback_cursor = self.scene.addLine(
            0.0, 0.0, 0.0, f_total_height, QPen(QtCore.Qt.red, 2.0))
        self.playback_cursor.setZValue(1000.0)

        self.set_playback_pos(self.playback_pos)
        self.check_line_count()
        self.set_header_y_pos()

    def draw_region(self, a_marker):
        f_region_length = pydaw_get_current_region_length()
        f_size = SEQUENCER_PX_PER_BEAT * f_region_length
        f_v_pen = QPen(QtCore.Qt.black)
        f_beat_pen = QPen(QColor(210, 210, 210))
        f_16th_pen = QPen(QColor(120, 120, 120))
        f_reg_pen = QPen(QtCore.Qt.white)
        f_total_height = (REGION_EDITOR_TRACK_COUNT *
            (shared.REGION_EDITOR_TRACK_HEIGHT)) + REGION_EDITOR_HEADER_HEIGHT

        f_x_offset = a_marker.beat * SEQUENCER_PX_PER_BEAT
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
                if SEQ_LINES_ENABLED and DRAW_SEQUENCER_GRAPHS:
                    for f_i4 in range(1, SEQ_SNAP_RANGE):
                        f_sub_x = i3 + (SEQUENCER_QUANTIZE_PX * f_i4)
                        f_line = self.scene.addLine(
                            f_sub_x, REGION_EDITOR_HEADER_HEIGHT,
                            f_sub_x, f_total_height, f_16th_pen)
                        self.beat_line_list.append(f_line)
            elif DRAW_SEQUENCER_GRAPHS:
                f_beat_x = i3
                f_line = self.scene.addLine(
                    f_beat_x, 0.0, f_beat_x, f_total_height, f_beat_pen)
                self.beat_line_list.append(f_line)
                if SEQ_LINES_ENABLED:
                    for f_i4 in range(1, SEQ_SNAP_RANGE):
                        f_sub_x = f_beat_x + (SEQUENCER_QUANTIZE_PX * f_i4)
                        f_line = self.scene.addLine(
                            f_sub_x, REGION_EDITOR_HEADER_HEIGHT,
                            f_sub_x, f_total_height, f_16th_pen)
                        self.beat_line_list.append(f_line)
            i3 += SEQUENCER_PX_PER_BEAT
        self.scene.addLine(
            i3, REGION_EDITOR_HEADER_HEIGHT, i3, f_total_height, f_reg_pen)
        for i2 in range(REGION_EDITOR_TRACK_COUNT):
            f_y = (shared.REGION_EDITOR_TRACK_HEIGHT *
                (i2 + 1)) + REGION_EDITOR_HEADER_HEIGHT
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
            shared.REGION_EDITOR_TRACK_HEIGHT) + REGION_EDITOR_HEADER_HEIGHT
        f_max = f_min + shared.REGION_EDITOR_TRACK_HEIGHT - ATM_POINT_DIAMETER
        f_item = SeqAtmItem(
            a_point, self.automation_save_callback, f_min, f_max)
        self.scene.addItem(f_item)
        f_item.setPos(self.get_pos_from_point(a_point))
        self.automation_points.append(f_item)
        if str(a_point) in self.selected_point_strings:
            f_item.setSelected(True)
        return f_item

    def get_pos_from_point(self, a_point):
        f_track_height = shared.REGION_EDITOR_TRACK_HEIGHT - ATM_POINT_DIAMETER
        f_track = shared.TRACK_PANEL.plugin_uid_map[a_point.index]
        return QtCore.QPointF(
            (a_point.beat * SEQUENCER_PX_PER_BEAT),
            (f_track_height * (1.0 - (a_point.cc_val / 127.0))) +
            (shared.REGION_EDITOR_TRACK_HEIGHT * f_track) +
            REGION_EDITOR_HEADER_HEIGHT)

    def automation_save_callback(self, a_open=True):
        shared.PROJECT.save_atm_region(ATM_REGION)
        if a_open:
            self.open_region()

    def transform_atm_callback(self, a_add, a_mul):
        self.setUpdatesEnabled(False)
        for f_point, f_val in zip(self.atm_selected, self.atm_selected_vals):
            f_val = (f_val * a_mul) + a_add
            f_val = pydaw_util.pydaw_clip_value(f_val, 0.0, 127.0, True)
            f_point.item.cc_val = f_val
            f_point.setPos(self.get_pos_from_point(f_point.item))
        self.setUpdatesEnabled(True)
        self.update()

    def transform_atm(self):
        self.atm_selected = sorted(self.get_selected_points())
        if not self.atm_selected:
            QMessageBox.warning(
                self, _("Error"), _("No automation points selected"))
            return
        f_start_beat = self.atm_selected[0].item.beat
        self.set_playback_pos(f_start_beat)
        f_scrollbar = self.horizontalScrollBar()
        f_scrollbar.setValue(SEQUENCER_PX_PER_BEAT * f_start_beat)

        self.atm_selected_vals = [x.item.cc_val for x in self.atm_selected]

        f_result = pydaw_widgets.add_mul_dialog(
            self.transform_atm_callback,
            lambda : self.automation_save_callback(a_open=False))

        if not f_result:
            for f_point, f_val in zip(
            self.atm_selected, self.atm_selected_vals):
                f_point.item.cc_val = f_val
            self.automation_save_callback()
        else:
            self.open_region()

    def lfo_atm_callback(
            self, a_phase, a_start_freq, a_start_amp, a_start_center,
            a_start_fade, a_end_fade, a_end_freq, a_end_amp, a_end_center):
        a_phase, a_start_freq, a_start_fade, a_end_freq, a_end_fade = (
            x * 0.01 for x in
            (a_phase, a_start_freq, a_start_fade, a_end_freq, a_end_fade))
        a_phase *= math.pi
        f_start_beat, f_end_beat = self.get_loop_pos()

        f_length_beats = f_end_beat - f_start_beat
        two_pi = 2.0 * math.pi
        f_start_radians_p64, f_end_radians_p64 = (
            (x * two_pi) / 8.0 for x in (a_start_freq, a_end_freq))
        f_length_beats_recip = 1.0 / f_length_beats

        self.setUpdatesEnabled(False)

        for f_point in self.atm_selected:
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
            f_point.setPos(self.get_pos_from_point(f_point.item))

            a_phase += pydaw_util.linear_interpolate(
                f_start_radians_p64, f_end_radians_p64, f_pos)
            if a_phase >= two_pi:
                a_phase -= two_pi

        self.setUpdatesEnabled(True)
        self.update()

    def lfo_atm(self):
        if not self.current_coord:
            return
        f_range = self.get_loop_pos()
        if not f_range:
            return
        f_start_beat, f_end_beat = f_range
        if f_end_beat - f_start_beat > 64:
            QMessageBox.warning(
                self, _("Error"),
                _("LFO patterns are limited to 64 beats in length"))
            return
        f_scrollbar = self.horizontalScrollBar()
        f_scrollbar.setValue(SEQUENCER_PX_PER_BEAT * f_start_beat)
        self.set_playback_pos(f_start_beat)
        f_step = 1.0 / 16.0
        f_track, f_beat, f_val = self.current_coord
        f_index, f_plugin = shared.TRACK_PANEL.get_atm_params(f_track)
        if f_index is None:
            QMessageBox.warning(
                self, _("Error"), _("Track has no automation selected"))
            return

        f_port, f_atm_uid = shared.TRACK_PANEL.has_automation(f_track)
        f_old = ATM_REGION.clear_range(
            f_index, f_port, f_start_beat, f_end_beat)
        if f_old:
            self.automation_save_callback()
        f_pos = f_start_beat
        self.scene.clearSelection()
        self.atm_selected = []

        for f_i in range(int((f_end_beat - f_start_beat) / f_step)):
            f_point = project.pydaw_atm_point(
                f_pos, f_port, 64.0, f_index, f_plugin)
            ATM_REGION.add_point(f_point)
            f_item = self.draw_point(f_point)
            self.atm_selected.append(f_item)
            f_pos += f_step

        f_result = pydaw_widgets.lfo_dialog(
            self.lfo_atm_callback,
            lambda : self.automation_save_callback(a_open=False))

        if not f_result:
            for f_point in self.atm_selected:
                ATM_REGION.remove_point(f_point.item)
            if f_old:
                for f_point in f_old:
                    ATM_REGION.add_point(f_point)
            self.automation_save_callback()
        else:
            self.open_region()

    def transpose_dialog(self):
        if REGION_EDITOR_MODE != 0:
            return
        f_item_set = {x.name for x in self.get_selected_items()}
        if len(f_item_set) == 0:
            QMessageBox.warning(
                shared.MAIN_WINDOW, _("Error"), _("No items selected"))
            return

        def transpose_ok_handler():
            for f_item_name in f_item_set:
                f_item = shared.PROJECT.get_item_by_name(f_item_name)
                f_item.transpose(
                    f_semitone.value(), f_octave.value(),
                    a_selected_only=False,
                    a_duplicate=f_duplicate_notes.isChecked())
                shared.PROJECT.save_item(f_item_name, f_item)
            shared.PROJECT.commit(_("Transpose item(s)"))
            if shared.CURRENT_ITEM:
                global_open_items(shared.CURRENT_ITEM_NAME)
            if f_duplicate_notes.isChecked():
                shared.REGION_SETTINGS.open_region()
            f_window.close()

        def transpose_cancel_handler():
            f_window.close()

        f_window = QDialog(shared.MAIN_WINDOW)
        f_window.setWindowTitle(_("Transpose"))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)

        f_semitone = QSpinBox()
        f_semitone.setRange(-12, 12)
        f_layout.addWidget(QLabel(_("Semitones")), 0, 0)
        f_layout.addWidget(f_semitone, 0, 1)
        f_octave = QSpinBox()
        f_octave.setRange(-5, 5)
        f_layout.addWidget(QLabel(_("Octaves")), 1, 0)
        f_layout.addWidget(f_octave, 1, 1)
        f_duplicate_notes = QCheckBox(_("Duplicate notes?"))
        f_duplicate_notes.setToolTip(
            _("Checking this box causes the transposed "
            "notes to be added rather than moving the existing notes."))
        f_layout.addWidget(f_duplicate_notes, 2, 1)
        f_ok = QPushButton(_("OK"))
        f_ok.pressed.connect(transpose_ok_handler)
        f_layout.addWidget(f_ok, 6, 0)
        f_cancel = QPushButton(_("Cancel"))
        f_cancel.pressed.connect(transpose_cancel_handler)
        f_layout.addWidget(f_cancel, 6, 1)
        f_window.exec_()

    def glue_selected(self):
        if libmk.IS_PLAYING:
            return
        f_did_something = False
        f_selected = [x.audio_item for x in self.get_selected()]
        for f_i in range(project.TRACK_COUNT_ALL):
            f_track_items = [x for x in f_selected if x.track_num == f_i]
            if len(f_track_items) > 1:
                f_did_something = True
                f_track_items.sort()
                f_new_ref = f_track_items[0].clone()
                f_items_dict = shared.PROJECT.get_items_dict()
                f_old_name = f_items_dict.get_name_by_uid(f_new_ref.item_uid)
                f_new_name = shared.PROJECT.get_next_default_item_name(
                    f_old_name, f_items_dict)
                f_new_uid = shared.PROJECT.create_empty_item(f_new_name)
                f_new_item = shared.PROJECT.get_item_by_uid(f_new_uid)
                f_tempo = shared.CURRENT_REGION.get_tempo_at_pos(f_new_ref.start_beat)
                f_last_ref = f_track_items[-1]
                f_new_ref.item_uid = f_new_uid
                f_new_ref.length_beats = (f_last_ref.start_beat -
                    f_new_ref.start_beat) + f_last_ref.length_beats
                shared.CURRENT_REGION.add_item_ref_by_uid(f_new_ref)
                f_first = True
                for f_ref in f_track_items:
                    f_tempo = shared.CURRENT_REGION.get_tempo_at_pos(f_ref.start_beat)
                    f_item = shared.PROJECT.get_item_by_uid(f_ref.item_uid)
                    f_new_item.extend(f_new_ref, f_ref, f_item, f_tempo)
                    if not f_first:
                        shared.CURRENT_REGION.remove_item_ref(f_ref)
                    else:
                        f_first = False
                pydaw_util.print_sorted_dict(locals())
                shared.PROJECT.save_item(f_new_name, f_new_item)
        if f_did_something:
            shared.PROJECT.save_region(shared.CURRENT_REGION)
            shared.PROJECT.commit(_("Glue sequencer items"))
            shared.REGION_SETTINGS.open_region()
        else:
            QMessageBox.warning(
                shared.MAIN_WINDOW, _("Error"),
                _("You must select at least 2 items on one or more tracks"))


    def cut_selected(self):
        self.copy_selected()
        self.delete_selected()

    def on_rename_items(self):
        if REGION_EDITOR_MODE != 0:
            return
        f_result = []
        for f_item_name in (x.name for x in self.get_selected_items()):
            if not f_item_name in f_result:
                f_result.append(f_item_name)
        if not f_result:
            return

        def ok_handler():
            f_new_name = str(f_new_lineedit.text())
            if f_new_name == "":
                QMessageBox.warning(
                    self.group_box, _("Error"), _("Name cannot be blank"))
                return
            global REGION_CLIPBOARD
            #Clear the clipboard, otherwise the names could be invalid
            REGION_CLIPBOARD = []
            shared.PROJECT.rename_items(f_result, f_new_name)
            shared.PROJECT.commit(_("Rename items"))
            shared.REGION_SETTINGS.open_region()
            if shared.DRAW_LAST_ITEMS:
                global_open_items()
            f_window.close()

        def cancel_handler():
            f_window.close()

        def on_name_changed():
            f_new_lineedit.setText(
                pydaw_remove_bad_chars(f_new_lineedit.text()))

        f_window = QDialog(shared.MAIN_WINDOW)
        f_window.setWindowTitle(_("Rename selected items..."))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)
        f_new_lineedit = QLineEdit()
        f_new_lineedit.editingFinished.connect(on_name_changed)
        f_new_lineedit.setMaxLength(24)
        f_layout.addWidget(QLabel(_("New name:")), 0, 0)
        f_layout.addWidget(f_new_lineedit, 0, 1)
        f_ok_button = QPushButton(_("OK"))
        f_layout.addWidget(f_ok_button, 5, 0)
        f_ok_button.clicked.connect(ok_handler)
        f_cancel_button = QPushButton(_("Cancel"))
        f_layout.addWidget(f_cancel_button, 5, 1)
        f_cancel_button.clicked.connect(cancel_handler)
        f_window.exec_()

    def on_unlink_item(self):
        """ Rename a single instance of an item and
            make it into a new item
        """
        if REGION_EDITOR_MODE != 0:
            return

        if not self.current_coord or not self.current_item:
            return

        f_uid_dict = shared.PROJECT.get_items_dict()
        f_current_item = self.current_item.audio_item

        f_current_item_text = f_uid_dict.get_name_by_uid(
            f_current_item.item_uid)

        def note_ok_handler():
            f_cell_text = str(f_new_lineedit.text())
            if f_cell_text == f_current_item_text:
                QMessageBox.warning(
                    self.group_box, _("Error"),
                    _("You must choose a different name than the "
                    "original item"))
                return
            if shared.PROJECT.item_exists(f_cell_text):
                QMessageBox.warning(
                    self.group_box, _("Error"),
                    _("An item with this name already exists."))
                return
            f_uid = shared.PROJECT.copy_item(
                f_current_item_text, str(f_new_lineedit.text()))
            self.last_item_copied = f_cell_text

            f_item_ref = f_current_item.clone()
            f_takes = shared.PROJECT.get_takes()
            f_takes.add_item(f_current_item.item_uid, f_uid)
            f_item_ref.item_uid = f_uid
            shared.CURRENT_REGION.add_item_ref_by_uid(f_item_ref)
            shared.PROJECT.save_takes(f_takes)
            shared.PROJECT.save_region(shared.CURRENT_REGION)
            shared.PROJECT.commit(
                _("Unlink item '{}' as '{}'").format(
                f_current_item_text, f_cell_text))
            self.open_region()
            f_window.close()

        def note_cancel_handler():
            f_window.close()

        def on_name_changed():
            f_new_lineedit.setText(
                pydaw_remove_bad_chars(f_new_lineedit.text()))

        f_window = QDialog(shared.MAIN_WINDOW)
        f_window.setWindowTitle(_("Copy and unlink item..."))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)
        f_new_lineedit = QLineEdit(f_current_item_text)
        f_new_lineedit.editingFinished.connect(on_name_changed)
        f_new_lineedit.setMaxLength(24)
        f_layout.addWidget(QLabel(_("New name:")), 0, 0)
        f_layout.addWidget(f_new_lineedit, 0, 1)
        f_ok_button = QPushButton(_("OK"))
        f_layout.addWidget(f_ok_button, 5, 0)
        f_ok_button.clicked.connect(note_ok_handler)
        f_cancel_button = QPushButton(_("Cancel"))
        f_layout.addWidget(f_cancel_button, 5, 1)
        f_cancel_button.clicked.connect(note_cancel_handler)
        f_window.exec_()

    def on_auto_unlink_selected(self):
        """ Adds an automatic -N suffix """
        if REGION_EDITOR_MODE != 0:
            return
        f_selected = list(self.get_selected_items())
        if not f_selected:
            return

        f_takes = shared.PROJECT.get_takes()

        self.selected_item_strings = set()
        for f_item in sorted(
        f_selected, key=lambda x:
        (x.audio_item.track_num, x.audio_item.start_beat)):
            f_name_suffix = 1
            while shared.PROJECT.item_exists(
            "{}-{}".format(f_item.name, f_name_suffix)):
                f_name_suffix += 1
            f_cell_text = "{}-{}".format(f_item.name, f_name_suffix)
            f_uid = shared.PROJECT.copy_item(f_item.name, f_cell_text)
            f_item_obj = f_item.audio_item
            f_takes.add_item(f_item_obj.item_uid, f_uid)
            shared.CURRENT_REGION.remove_item_ref(f_item_obj)
            f_item_obj.uid = f_uid
            f_item_ref = f_item_obj.clone()
            f_item_ref.item_uid = f_uid
            self.selected_item_strings.add(str(f_item_ref))
            shared.CURRENT_REGION.add_item_ref_by_uid(f_item_ref)
        shared.PROJECT.save_region(shared.CURRENT_REGION)
        shared.PROJECT.save_takes(f_takes)
        shared.PROJECT.commit(_("Auto-Unlink items"))
        shared.REGION_SETTINGS.open_region()

    def on_auto_unlink_unique(self):
        if REGION_EDITOR_MODE != 0:
            return
        f_result = [(x.name, x.audio_item) for x in self.get_selected_items()]

        if not f_result:
            return

        old_new_map = {}

        f_takes = shared.PROJECT.get_takes()

        for f_item_name in set(x[0] for x in f_result):
            f_name_suffix = 1
            while shared.PROJECT.item_exists(
            "{}-{}".format(f_item_name, f_name_suffix)):
                f_name_suffix += 1
            f_cell_text = "{}-{}".format(f_item_name, f_name_suffix)
            f_uid = shared.PROJECT.copy_item(f_item_name, f_cell_text)
            old_new_map[f_item_name] = f_uid

        self.selected_item_strings = set()

        for k, v in f_result:
            shared.CURRENT_REGION.remove_item_ref(v)
            f_new_uid = old_new_map[k]
            f_takes.add_item(v.item_uid, f_new_uid)
            v.uid = f_new_uid
            f_item_ref = project.pydaw_sequencer_item(
                v.track_num, v.start_beat, v.length_beats, f_new_uid)
            self.selected_item_strings.add(str(f_item_ref))
            shared.CURRENT_REGION.add_item_ref_by_uid(f_item_ref)
        shared.PROJECT.save_region(shared.CURRENT_REGION)
        shared.PROJECT.save_takes(f_takes)
        shared.PROJECT.commit(_("Auto-Unlink unique items"))
        shared.REGION_SETTINGS.open_region()

    def copy_selected(self):
        if not self.enabled:
            self.warn_no_region_selected()
            return
        if REGION_EDITOR_MODE == 0:
            global REGION_CLIPBOARD
            REGION_CLIPBOARD = [x.audio_item.clone() for x in
                self.get_selected_items()]
            if REGION_CLIPBOARD:
                REGION_CLIPBOARD.sort()
                f_start = int(REGION_CLIPBOARD[0].start_beat)
                for f_item in REGION_CLIPBOARD:
                    f_item.start_beat -= f_start
        elif REGION_EDITOR_MODE == 1:
            global ATM_CLIPBOARD
            ATM_CLIPBOARD = [x.item.clone() for x in
                self.get_selected_points(self.current_coord[0])]
            if ATM_CLIPBOARD:
                ATM_CLIPBOARD.sort()
                f_start = int(ATM_CLIPBOARD[0].beat)
                for f_item in ATM_CLIPBOARD:
                    f_item.beat -= f_start

    def paste_clipboard(self):
        if libmk.IS_PLAYING or not self.current_coord:
            return
        self.scene.clearSelection()
        f_track, f_beat, f_val = self.current_coord
        f_beat = int(f_beat)
        if REGION_EDITOR_MODE == 0:
            self.selected_item_strings = set()
            for f_item in REGION_CLIPBOARD:
                f_new_item = f_item.clone()
                f_new_item.start_beat += f_beat
                shared.CURRENT_REGION.add_item_ref_by_uid(f_new_item)
                self.selected_item_strings.add(str(f_new_item))
            shared.PROJECT.save_region(shared.CURRENT_REGION)
            shared.REGION_SETTINGS.open_region()
        elif REGION_EDITOR_MODE == 1:
            f_track_port_num, f_track_index = shared.TRACK_PANEL.has_automation(
                self.current_coord[0])
            if f_track_port_num is None:
                QMessageBox.warning(
                    self, _("Error"),
                    _("No automation selected for this track"))
                return
            f_track_params = shared.TRACK_PANEL.get_atm_params(f_track)
            f_end = ATM_CLIPBOARD[-1].beat + f_beat
            f_point = ATM_CLIPBOARD[0]
            ATM_REGION.clear_range(
                f_point.index, f_point.port_num, f_beat, f_end)
            for f_point in ATM_CLIPBOARD:
                ATM_REGION.add_point(
                    pydaw_atm_point(
                        f_point.beat + f_beat, f_track_port_num,
                        f_point.cc_val, *f_track_params))
            self.automation_save_callback()

    def paste_atm_point(self):
        if libmk.IS_PLAYING:
            return
        self.context_menu_enabled = False
        if pydaw_widgets.CC_CLIPBOARD is None:
            QMessageBox.warning(
                self, _("Error"),
                _("Nothing copied to the clipboard.\n"
                "Right-click->'Copy' on any knob on any plugin."))
            return
        f_track, f_beat, f_val = self.current_coord
        f_beat = self.quantize(f_beat)
        f_val = pydaw_widgets.CC_CLIPBOARD
        f_port, f_index = shared.TRACK_PANEL.has_automation(self.current_coord[0])
        if f_port is not None:
            f_point = pydaw_atm_point(
                f_beat, f_port, f_val, *shared.TRACK_PANEL.get_atm_params(f_track))
            ATM_REGION.add_point(f_point)
            self.draw_point(f_point)
            self.automation_save_callback()

class SeqTrack:
    """ The widget that contains the controls for an individual track
    """
    def __init__(self, a_track_num, a_track_text=_("track")):
        self.suppress_osc = True
        self.automation_uid = None
        self.automation_plugin = None
        self.track_number = a_track_num
        self.group_box = QWidget()
        self.group_box.contextMenuEvent = self.context_menu_event
        self.group_box.setObjectName("track_panel")
        self.main_hlayout = QHBoxLayout()
        self.main_hlayout.setContentsMargins(2, 2, 2, 2)
        self.main_vlayout = QVBoxLayout()
        self.main_hlayout.addLayout(self.main_vlayout)
        self.peak_meter = pydaw_widgets.peak_meter()
        if a_track_num in shared.ALL_PEAK_METERS:
            shared.ALL_PEAK_METERS[a_track_num].append(self.peak_meter)
        else:
            shared.ALL_PEAK_METERS[a_track_num] = [self.peak_meter]
        self.main_hlayout.addWidget(self.peak_meter.widget)
        self.group_box.setLayout(self.main_hlayout)
        self.track_name_lineedit = QLineEdit()
        if a_track_num == 0:
            self.track_name_lineedit.setText("Master")
            self.track_name_lineedit.setDisabled(True)
        else:
            self.track_name_lineedit.setText(a_track_text)
            self.track_name_lineedit.setMaxLength(48)
            self.track_name_lineedit.editingFinished.connect(
                self.on_name_changed)
        self.main_vlayout.addWidget(self.track_name_lineedit)
        self.hlayout3 = QHBoxLayout()
        self.main_vlayout.addLayout(self.hlayout3)

        self.menu_button = QPushButton()
        self.menu_button.setFixedWidth(42)
        self.button_menu = QMenu()
        self.menu_button.setMenu(self.button_menu)
        self.hlayout3.addWidget(self.menu_button)
        self.button_menu.aboutToShow.connect(self.menu_button_pressed)
        self.menu_created = False
        self.solo_checkbox = QCheckBox()
        self.mute_checkbox = QCheckBox()
        if self.track_number == 0:
            self.hlayout3.addItem(
                QSpacerItem(1, 1, QSizePolicy.Expanding)
            )
        else:
            self.solo_checkbox.stateChanged.connect(self.on_solo)
            self.solo_checkbox.setObjectName("solo_checkbox")
            self.hlayout3.addWidget(self.solo_checkbox)
            self.mute_checkbox.stateChanged.connect(self.on_mute)
            self.mute_checkbox.setObjectName("mute_checkbox")
            self.hlayout3.addWidget(self.mute_checkbox)
        self.action_widget = None
        self.automation_plugin_name = "None"
        self.port_num = None
        self.ccs_in_use_combobox = None
        self.suppress_osc = False
        self.automation_combobox = None

    def menu_button_pressed(self):
        if not self.menu_created:
            self.create_menu()

        self.suppress_ccs_in_use = True
        index = self.automation_combobox.currentIndex()
        plugins = shared.PROJECT.get_track_plugins(self.track_number)
        if plugins:
            names = [
                PLUGIN_UIDS_REVERSE[x.plugin_index]
                for x in plugins.plugins
            ]
        else:
            names = ["None" for x in range(10)]
        self.automation_combobox.clear()
        self.automation_combobox.addItems(names)
        self.automation_combobox.setCurrentIndex(index)
        if names[index] == "None":
            self.control_combobox.clear()
        self.suppress_ccs_in_use = False

        self.update_in_use_combobox()

    def open_plugins(self):
        shared.PLUGIN_RACK.track_combobox.setCurrentIndex(self.track_number)
        shared.MAIN_WINDOW.main_tabwidget.setCurrentIndex(shared.TAB_PLUGIN_RACK)
        self.button_menu.close()

    def create_menu(self):
        if self.action_widget:
            self.button_menu.removeAction(self.action_widget)
        self.menu_created = True
        self.menu_widget = QWidget()
        self.menu_hlayout = QHBoxLayout(self.menu_widget)
        self.menu_gridlayout = QGridLayout()
        self.menu_hlayout.addLayout(self.menu_gridlayout)
        self.action_widget = QWidgetAction(self.button_menu)
        self.action_widget.setDefaultWidget(self.menu_widget)
        self.button_menu.addAction(self.action_widget)

        self.plugins_button = QPushButton(_("Show Plugins"))
        self.menu_gridlayout.addWidget(self.plugins_button, 0, 21)
        self.plugins_button.pressed.connect(self.open_plugins)

        self.menu_gridlayout.addWidget(QLabel(_("Automation")), 3, 21)
        self.automation_combobox = QComboBox()
        self.automation_combobox.setMinimumWidth(240)
        self.menu_gridlayout.addWidget(QLabel(_("Plugin:")), 5, 20)
        self.menu_gridlayout.addWidget(self.automation_combobox, 5, 21)
        self.automation_combobox.currentIndexChanged.connect(
            self.automation_callback)

        self.control_combobox = QComboBox()
        self.control_combobox.setMaxVisibleItems(30)
        self.control_combobox.setMinimumWidth(240)
        self.menu_gridlayout.addWidget(QLabel(_("Control:")), 9, 20)
        self.menu_gridlayout.addWidget(self.control_combobox, 9, 21)
        self.control_combobox.currentIndexChanged.connect(
            self.control_changed)
        self.ccs_in_use_combobox = QComboBox()
        self.ccs_in_use_combobox.setMinimumWidth(300)
        self.suppress_ccs_in_use = False
        self.ccs_in_use_combobox.currentIndexChanged.connect(
            self.ccs_in_use_combobox_changed)
        self.menu_gridlayout.addWidget(QLabel(_("In Use:")), 10, 20)
        self.menu_gridlayout.addWidget(self.ccs_in_use_combobox, 10, 21)

        self.color_hlayout = QHBoxLayout()
        self.menu_gridlayout.addWidget(QLabel(_("Color")), 28, 21)
        self.menu_gridlayout.addLayout(self.color_hlayout, 29, 21)

        self.color_button = QPushButton(_("Custom..."))
        self.color_button.pressed.connect(self.on_color_change)
        self.color_hlayout.addWidget(self.color_button)

        self.color_copy_button = QPushButton(_("Copy"))
        self.color_copy_button.pressed.connect(self.on_color_copy)
        self.color_hlayout.addWidget(self.color_copy_button)

        self.color_paste_button = QPushButton(_("Paste"))
        self.color_paste_button.pressed.connect(self.on_color_paste)
        self.color_hlayout.addWidget(self.color_paste_button)

    def on_color_change(self):
        if shared.TRACK_COLORS.pick_color(self.track_number):
            shared.PROJECT.save_track_colors(shared.TRACK_COLORS)
            shared.SEQUENCER.open_region()

    def on_color_copy(self):
        global TRACK_COLOR_CLIPBOARD
        TRACK_COLOR_CLIPBOARD = shared.TRACK_COLORS.get_brush(self.track_number)

    def on_color_paste(self):
        if not TRACK_COLOR_CLIPBOARD:
            QMessageBox.warning(
                libmk.shared.MAIN_WINDOW, _("Error"),
                _("Nothing copied to clipboard"))
        else:
            shared.TRACK_COLORS.set_color(
                self.track_number,
                TRACK_COLOR_CLIPBOARD,
            )
            shared.PROJECT.save_track_colors(shared.TRACK_COLORS)
            shared.SEQUENCER.open_region()

    def refresh(self):
        self.track_name_lineedit.setText(shared.TRACK_NAMES[self.track_number])
        if self.menu_created:
            self.create_menu()

    def plugin_changed(self, a_val=None):
        self.control_combobox.clear()
        if self.automation_plugin_name != "None":
            self.control_combobox.addItems(
                CC_NAMES[self.automation_plugin_name])
        shared.TRACK_PANEL.update_plugin_track_map()

    def control_changed(self, a_val=None):
        self.set_cc_num()
        self.ccs_in_use_combobox.setCurrentIndex(0)
        if not libmk.IS_PLAYING:
            shared.SEQUENCER.open_region()

    def set_cc_num(self, a_val=None):
        f_port_name = str(self.control_combobox.currentText())
        if f_port_name == "":
            self.port_num = None
        else:
            self.port_num = CONTROLLER_PORT_NAME_DICT[
                self.automation_plugin_name][f_port_name].port
        shared.TRACK_PANEL.update_automation()

    def ccs_in_use_combobox_changed(self, a_val=None):
        if not self.suppress_ccs_in_use:
            f_str = str(self.ccs_in_use_combobox.currentText())
            if f_str:
                self.control_combobox.setCurrentIndex(
                    self.control_combobox.findText(f_str))

    def update_in_use_combobox(self):
        if self.ccs_in_use_combobox is not None:
            self.ccs_in_use_combobox.clear()
            if self.automation_uid is not None:
                f_list = ATM_REGION.get_ports(self.automation_uid)
                self.ccs_in_use_combobox.addItems(
                    [""] +
                    [CONTROLLER_PORT_NUM_DICT[
                        self.automation_plugin_name][x].name
                    for x in f_list])

    def on_solo(self, value):
        if not self.suppress_osc:
            shared.PROJECT.IPC.pydaw_set_solo(
                self.track_number, self.solo_checkbox.isChecked())
            shared.PROJECT.save_tracks(shared.TRACK_PANEL.get_tracks())
            shared.PROJECT.commit(_("Set solo for track {} to {}").format(
                self.track_number, self.solo_checkbox.isChecked()))

    def on_mute(self, value):
        if not self.suppress_osc:
            shared.PROJECT.IPC.pydaw_set_mute(
                self.track_number, self.mute_checkbox.isChecked())
            shared.PROJECT.save_tracks(shared.TRACK_PANEL.get_tracks())
            shared.PROJECT.commit(_("Set mute for track {} to {}").format(
                self.track_number, self.mute_checkbox.isChecked()))

    def on_name_changed(self):
        f_name = pydaw_remove_bad_chars(self.track_name_lineedit.text())
        self.track_name_lineedit.setText(f_name)
        global_update_track_comboboxes(self.track_number, f_name)
        f_tracks = shared.PROJECT.get_tracks()
        f_tracks.tracks[self.track_number].name = f_name
        shared.PROJECT.save_tracks(f_tracks)
        shared.PROJECT.commit(
            _("Set name for track {} to {}").format(self.track_number,
            self.track_name_lineedit.text()))

    def context_menu_event(self, a_event=None):
        pass

    def automation_callback(self, a_val=None):
        if self.suppress_ccs_in_use:
            return
        plugins = shared.PROJECT.get_track_plugins(self.track_number)
        index = self.automation_combobox.currentIndex()
        plugin = plugins.plugins[index]
        self.automation_uid = int(plugin.plugin_uid)
        self.automation_plugin = int(plugin.plugin_index)
        self.automation_plugin_name = PLUGIN_UIDS_REVERSE[
            self.automation_plugin
        ]
        self.plugin_changed()
        if not libmk.IS_PLAYING:
            shared.SEQUENCER.open_region()

    def save_callback(self):
        shared.PROJECT.check_output(self.track_number)
        self.plugin_changed()

    def name_callback(self):
        return str(self.track_name_lineedit.text())

    def open_track(self, a_track, a_notify_osc=False):
        if not a_notify_osc:
            self.suppress_osc = True
        if self.track_number != 0:
            self.track_name_lineedit.setText(a_track.name)
            self.solo_checkbox.setChecked(a_track.solo)
            self.mute_checkbox.setChecked(a_track.mute)
        self.suppress_osc = False

    def get_track(self):
        return pydaw_track(
            self.track_number, self.solo_checkbox.isChecked(),
            self.mute_checkbox.isChecked(),
            self.track_number, self.track_name_lineedit.text())


class AudioInput:
    def __init__(self, a_num, a_layout, a_callback, a_count):
        self.input_num = int(a_num)
        self.callback = a_callback
        a_layout.addWidget(QLabel(str(a_num)), a_num + 1, 21)
        self.name_lineedit = QLineEdit(str(a_num))
        self.name_lineedit.editingFinished.connect(self.name_update)
        a_num += 1
        a_layout.addWidget(self.name_lineedit, a_num, 0)
        self.rec_checkbox = QCheckBox("")
        self.rec_checkbox.clicked.connect(self.update_engine)
        a_layout.addWidget(self.rec_checkbox, a_num, 1)

        self.monitor_checkbox = QCheckBox(_(""))
        self.monitor_checkbox.clicked.connect(self.update_engine)
        a_layout.addWidget(self.monitor_checkbox, a_num, 2)

        self.vol_layout = QHBoxLayout()
        a_layout.addLayout(self.vol_layout, a_num, 3)
        self.vol_slider = QSlider(QtCore.Qt.Horizontal)
        self.vol_slider.setRange(-240, 240)
        self.vol_slider.setValue(0)
        self.vol_slider.setMinimumWidth(240)
        self.vol_slider.valueChanged.connect(self.vol_changed)
        self.vol_slider.sliderReleased.connect(self.update_engine)
        self.vol_layout.addWidget(self.vol_slider)
        self.vol_label = QLabel("0.0dB")
        self.vol_label.setMinimumWidth(64)
        self.vol_layout.addWidget(self.vol_label)
        self.stereo_combobox = QComboBox()
        a_layout.addWidget(self.stereo_combobox, a_num, 4)
        self.stereo_combobox.setMinimumWidth(75)
        self.stereo_combobox.addItems([_("None")] +
            [str(x) for x in range(a_count + 1)])
        self.stereo_combobox.currentIndexChanged.connect(self.update_engine)
        self.output_mode_combobox = QComboBox()
        self.output_mode_combobox.setMinimumWidth(100)
        self.output_mode_combobox.addItems(
            [_("Normal"), _("Sidechain"), _("Both")])
        a_layout.addWidget(self.output_mode_combobox, a_num, 5)
        self.output_mode_combobox.currentIndexChanged.connect(
            self.update_engine)
        self.output_track_combobox = QComboBox()
        self.output_track_combobox.setMinimumWidth(140)
        shared.TRACK_NAME_COMBOBOXES.append(self.output_track_combobox)
        self.output_track_combobox.addItems(shared.TRACK_NAMES)
        self.output_track_combobox.currentIndexChanged.connect(
            self.output_track_changed)
        a_layout.addWidget(self.output_track_combobox, a_num, 6)
        self.suppress_updates = False

    def output_track_changed(self, a_val=None):
        if not self.suppress_updates and not SUPPRESS_TRACK_COMBOBOX_CHANGES:
            f_track = self.output_track_combobox.currentIndex()
            if f_track in shared.TRACK_PANEL.tracks:
                shared.PROJECT.check_output(f_track)
                self.update_engine()
            else:
                print("{} not in shared.TRACK_PANEL".format(f_track))

    def name_update(self, a_val=None):
        self.update_engine(a_notify=False)

    def update_engine(self, a_val=None, a_notify=True):
        if not self.suppress_updates:
            self.callback(a_notify)

    def vol_changed(self):
        f_vol = self.get_vol()
        self.vol_label.setText("{}dB".format(f_vol))
        if not self.suppress_updates:
            libmk.IPC.audio_input_volume(self.input_num, f_vol)

    def get_vol(self):
        return round(self.vol_slider.value() * 0.1, 1)

    def get_name(self):
        return str(self.name_lineedit.text())

    def get_value(self):
        f_on = 1 if self.rec_checkbox.isChecked() else 0
        f_vol = self.get_vol()
        f_monitor = 1 if self.monitor_checkbox.isChecked() else 0
        f_stereo = self.stereo_combobox.currentIndex() - 1
        f_mode = self.output_mode_combobox.currentIndex()
        f_output = self.output_track_combobox.currentIndex()
        f_name = self.name_lineedit.text()

        return libmk.mk_project.AudioInputTrack(
            f_on, f_monitor, f_vol, f_output, f_stereo, f_mode, f_name)

    def set_value(self, a_val):
        self.suppress_updates = True
        f_rec = True if a_val.rec else False
        f_monitor = True if a_val.monitor else False
        self.name_lineedit.setText(a_val.name)
        self.rec_checkbox.setChecked(f_rec)
        self.monitor_checkbox.setChecked(f_monitor)
        self.vol_slider.setValue(int(a_val.vol * 10.0))
        self.stereo_combobox.setCurrentIndex(a_val.stereo + 1)
        self.output_mode_combobox.setCurrentIndex(a_val.sidechain)
        self.output_track_combobox.setCurrentIndex(a_val.output)
        self.suppress_updates = False


class AudioInputWidget:
    def __init__(self):
        self.widget = QWidget()
        self.main_layout = QVBoxLayout(self.widget)
        self.layout = QGridLayout()
        self.main_layout.addWidget(QLabel(_("Audio Inputs")))
        self.main_layout.addLayout(self.layout)
        f_labels = (
            _("Name"), _("Rec."), _("Mon."), _("Gain"), _("Stereo"),
            _("Mode"), _("Output"))
        for f_i, f_label in zip(range(len(f_labels)), f_labels):
            self.layout.addWidget(QLabel(f_label), 0, f_i)
        self.inputs = []
        f_count = 0
        if "audioInputs" in pydaw_util.global_device_val_dict:
            f_count = int(pydaw_util.global_device_val_dict["audioInputs"])
        for f_i in range(f_count):
            f_input = AudioInput(f_i, self.layout, self.callback, f_count - 1)
            self.inputs.append(f_input)

    def get_inputs(self):
        f_result = libmk.mk_project.AudioInputTracks()
        for f_i, f_input in zip(range(len(self.inputs)), self.inputs):
            f_result.add_track(f_i, f_input.get_value())
        return f_result

    def callback(self, a_notify):
        f_result = self.get_inputs()
        shared.PROJECT.save_audio_inputs(f_result)
        if a_notify:
            shared.PROJECT.IPC.save_audio_inputs()

    def active(self):
        return [x.get_value() for x in self.inputs
            if x.rec_checkbox.isChecked()]

    def open_project(self):
        f_audio_inputs = shared.PROJECT.get_audio_inputs()
        for k, v in f_audio_inputs.tracks.items():
            if k < len(self.inputs):
                self.inputs[k].set_value(v)

class TransportWidget(libmk.AbstractTransport):
    def __init__(self):
        self.recording_timestamp = None
        self.suppress_osc = True
        self.last_open_dir = global_home
        self.group_box = QWidget()
        self.group_box.setObjectName("transport_panel")
        self.hlayout1 = QHBoxLayout(self.group_box)
        self.playback_menu_button = QPushButton("")
        self.playback_menu_button.setMaximumWidth(21)
        self.playback_menu_button.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.hlayout1.addWidget(self.playback_menu_button)
        self.vlayout = QVBoxLayout()
        self.hlayout1.addLayout(self.vlayout)

        self.hlayout2 = QHBoxLayout()
        self.vlayout.addLayout(self.hlayout2)

        self.playback_menu = QMenu(self.playback_menu_button)
        self.playback_menu_button.setMenu(self.playback_menu)
        self.playback_widget_action = QWidgetAction(self.playback_menu)
        self.playback_widget = QWidget()
        self.playback_widget_action.setDefaultWidget(self.playback_widget)
        self.playback_vlayout = QVBoxLayout(self.playback_widget)
        self.playback_menu.addAction(self.playback_widget_action)

        self.hlayout2.addWidget(QLabel(_("Loop Mode:")))
        self.loop_mode_combobox = QComboBox()
        self.loop_mode_combobox.addItems([_("Off"), _("Region")])
        self.loop_mode_combobox.setMinimumWidth(90)
        self.loop_mode_combobox.currentIndexChanged.connect(
            self.on_loop_mode_changed,
        )
        self.hlayout2.addWidget(self.loop_mode_combobox)

        self.hlayout3 = QHBoxLayout()
        self.vlayout.addLayout(self.hlayout3)
        self.hlayout3.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding))
        self.hlayout3.setContentsMargins(-3, 1, -3, 1)

        # Mouse tools
        self.tool_select_rb = QRadioButton()
        self.tool_select_rb.setObjectName("tool_select")
        self.tool_select_rb.setToolTip(_("Select (hotkey: a)"))
        self.hlayout3.addWidget(self.tool_select_rb)
        self.tool_select_rb.clicked.connect(self.tool_select_clicked)
        self.tool_select_rb.setChecked(True)

        self.tool_draw_rb = QRadioButton()
        self.tool_draw_rb.setObjectName("tool_draw")
        self.tool_draw_rb.setToolTip(_("Draw (hotkey: s)"))
        self.tool_draw_rb.clicked.connect(self.tool_draw_clicked)
        self.hlayout3.addWidget(self.tool_draw_rb)

        self.tool_erase_rb = QRadioButton()
        self.tool_erase_rb.setObjectName("tool_erase")
        self.tool_erase_rb.setToolTip(_("Erase (hotkey: d)"))
        self.tool_erase_rb.clicked.connect(self.tool_erase_clicked)
        self.hlayout3.addWidget(self.tool_erase_rb)

        self.tool_split_rb = QRadioButton()
        self.tool_split_rb.setObjectName("tool_split")
        self.tool_split_rb.setToolTip(_("Split (hotkey: f)"))
        self.tool_split_rb.clicked.connect(self.tool_split_clicked)
        self.hlayout3.addWidget(self.tool_split_rb)

        self.overdub_checkbox = QCheckBox(_("Overdub"))
        self.overdub_checkbox.clicked.connect(self.on_overdub_changed)
        #self.playback_vlayout.addWidget(self.overdub_checkbox)
        self.playback_vlayout.addWidget(QLabel(_("MIDI Input Devices")))

        self.playback_vlayout.addLayout(shared.MIDI_DEVICES_DIALOG.layout)
        self.active_devices = []

        self.audio_inputs = AudioInputWidget()
        self.playback_vlayout.addWidget(self.audio_inputs.widget)

        self.suppress_osc = False

    def tool_select_clicked(self, a_val=None):
        shared.EDITOR_MODE = shared.EDITOR_MODE_SELECT
        if not self.tool_select_rb.isChecked():
            self.tool_select_rb.setChecked(True)

    def tool_draw_clicked(self, a_val=None):
        shared.EDITOR_MODE = shared.EDITOR_MODE_DRAW
        if not self.tool_draw_rb.isChecked():
            self.tool_draw_rb.setChecked(True)

    def tool_erase_clicked(self, a_val=None):
        shared.EDITOR_MODE = shared.EDITOR_MODE_ERASE
        if not self.tool_erase_rb.isChecked():
            self.tool_erase_rb.setChecked(True)

    def tool_split_clicked(self, a_val=None):
        shared.EDITOR_MODE = shared.EDITOR_MODE_SPLIT
        if not self.tool_split_rb.isChecked():
            self.tool_split_rb.setChecked(True)

    def open_project(self):
        self.audio_inputs.open_project()

    def on_panic(self):
        shared.PROJECT.IPC.pydaw_panic()

    def set_time(self, a_beat):
        f_text = shared.CURRENT_REGION.get_time_at_beat(a_beat)
        libmk.TRANSPORT.set_time(f_text)

    def set_pos_from_cursor(self, a_beat):
        if libmk.IS_PLAYING or libmk.IS_RECORDING:
            f_beat = float(a_beat)
            self.set_time(f_beat)

    def set_controls_enabled(self, a_enabled):
        for f_widget in (
        shared.REGION_SETTINGS.snap_combobox, self.overdub_checkbox):
            f_widget.setEnabled(a_enabled)

    def on_play(self):
        if (
            shared.MAIN_WINDOW.main_tabwidget.currentIndex()
            ==
            shared.TAB_ITEM_EDITOR
        ):
            shared.SEQUENCER.open_region()
        shared.REGION_SETTINGS.on_play()
        shared.AUDIO_SEQ_WIDGET.on_play()
        shared.SEQUENCER.start_playback()
        shared.PROJECT.IPC.pydaw_en_playback(
            1,
            shared.SEQUENCER.get_beat_value(),
        )
        self.set_controls_enabled(False)
        return True

    def on_stop(self):
        shared.PROJECT.IPC.pydaw_en_playback(0)
        shared.REGION_SETTINGS.on_stop()
        shared.AUDIO_SEQ_WIDGET.on_stop()
        self.set_controls_enabled(True)
        self.loop_mode_combobox.setEnabled(True)
        self.playback_menu_button.setEnabled(True)

        if libmk.IS_RECORDING:
            f_restart_engine = False
            f_audio_count = len(self.audio_inputs.active())
            if f_audio_count:
                f_stop_time = datetime.datetime.now()
                f_delta = (f_stop_time -
                    self.recording_timestamp) * f_audio_count
                f_restart_engine = libmk.add_entropy(f_delta)
            if self.rec_end is None:
                self.rec_end = round(shared.SEQUENCER.get_beat_value() + 0.5)
            self.show_save_items_dialog(a_restart=f_restart_engine)

        shared.SEQUENCER.stop_playback()
        #shared.REGION_SETTINGS.open_region()
        self.set_time(shared.SEQUENCER.get_beat_value())

    def show_save_items_dialog(self, a_restart=False):
        f_inputs = self.audio_inputs.inputs
        def ok_handler():
            f_file_name = str(f_file.text())
            if f_file_name is None or f_file_name == "":
                QMessageBox.warning(
                    f_window, _("Error"),
                    _("You must select a name for the item"))
                return

            f_sample_count = shared.CURRENT_REGION.get_sample_count(
                self.rec_start, self.rec_end, pydaw_util.SAMPLE_RATE)

            shared.PROJECT.save_recorded_items(
                f_file_name, MREC_EVENTS, self.overdub_checkbox.isChecked(),
                pydaw_util.SAMPLE_RATE, self.rec_start, self.rec_end,
                f_inputs, f_sample_count, f_file_name)
            shared.REGION_SETTINGS.open_region()
            if pydaw_util.IS_ENGINE_LIB:
                libmk.clean_wav_pool()
            elif a_restart:
                libmk.restart_engine()
            f_window.close()

        def text_edit_handler(a_val=None):
            f_file.setText(pydaw_remove_bad_chars(f_file.text()))

        f_window = QDialog(shared.MAIN_WINDOW)
        f_window.setWindowTitle(_("Save Recorded Files"))
        f_window.setMinimumWidth(330)
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)
        f_layout.addWidget(QLabel(_("Save recorded items")), 0, 2)
        f_layout.addWidget(QLabel(_("Item Name:")), 3, 1)
        f_file = QLineEdit()
        f_file.setMaxLength(24)
        f_file.textEdited.connect(text_edit_handler)
        f_layout.addWidget(f_file, 3, 2)
        f_ok_button = QPushButton(_("Save"))
        f_ok_button.clicked.connect(ok_handler)
        f_cancel_button = QPushButton(_("Discard"))
        f_cancel_button.clicked.connect(f_window.close)
        f_ok_cancel_layout = QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_layout.addLayout(f_ok_cancel_layout, 8, 2)
        f_window.exec_()


    def on_rec(self):
        if self.loop_mode_combobox.currentIndex() == 1:
            QMessageBox.warning(
                self.group_box, _("Error"),
                _("Loop recording is not yet supported"))
            return False
        self.active_devices = [x for x in shared.MIDI_DEVICES_DIALOG.devices
            if x.record_checkbox.isChecked()]
        if not self.active_devices and not self.audio_inputs.active():
            QMessageBox.warning(
                self.group_box, _("Error"),
                _("No MIDI or audio inputs record-armed"))
            return False
#        if self.overdub_checkbox.isChecked() and \
#        self.loop_mode_combobox.currentIndex() > 0:
#            QMessageBox.warning(
#                self.group_box, _("Error"),
#                _("Cannot use overdub mode with loop mode to record"))
#            return False
        shared.REGION_SETTINGS.on_play()
        shared.AUDIO_SEQ_WIDGET.on_play()
        shared.SEQUENCER.start_playback()
        self.set_controls_enabled(False)
        self.loop_mode_combobox.setEnabled(False)
        self.playback_menu_button.setEnabled(False)
        global MREC_EVENTS
        MREC_EVENTS = []
        f_loop_pos = shared.SEQUENCER.get_loop_pos(a_warn=False)
        if self.loop_mode_combobox.currentIndex() == 0 or not f_loop_pos:
            self.rec_start = shared.SEQUENCER.get_beat_value()
            self.rec_end = None
        else:
            self.rec_start, self.rec_end = f_loop_pos
        self.recording_timestamp = datetime.datetime.now()
        shared.PROJECT.IPC.pydaw_en_playback(2, self.rec_start)
        return True

    def on_loop_mode_changed(self, a_loop_mode):
        if not self.suppress_osc:
            shared.PROJECT.IPC.pydaw_set_loop_mode(a_loop_mode)

    def toggle_loop_mode(self):
        f_index = self.loop_mode_combobox.currentIndex() + 1
        if f_index >= self.loop_mode_combobox.count():
            f_index = 0
        self.loop_mode_combobox.setCurrentIndex(f_index)

    def on_overdub_changed(self, a_val=None):
        shared.PROJECT.IPC.pydaw_set_overdub_mode(
            self.overdub_checkbox.isChecked())

    def reset(self):
        self.loop_mode_combobox.setCurrentIndex(0)
        self.overdub_checkbox.setChecked(False)

    def set_tooltips(self, a_enabled):
        if a_enabled:
            self.overdub_checkbox.setToolTip(
                _("Checking this box causes recording to "
                "unlink existing items and append new events to the "
                "existing events"))
            self.loop_mode_combobox.setToolTip(
                _("Use this to toggle between normal playback "
                "and looping a region.\nYou can toggle between "
                "settings with CTRL+L"))
            self.group_box.setToolTip(dn_strings.transport)
        else:
            self.overdub_checkbox.setToolTip("")
            self.loop_mode_combobox.setToolTip("")
            self.group_box.setToolTip("")

class TrackPanel:
    """ The widget that sits next to the sequencer QGraphicsView and
        contains the individual tracks
    """
    def __init__(self):
        self.tracks = {}
        self.plugin_uid_map = {}
        self.tracks_widget = QWidget()
        self.tracks_widget.setObjectName("plugin_ui")
        self.tracks_widget.setContentsMargins(0, 0, 0, 0)
        self.tracks_layout = QVBoxLayout(self.tracks_widget)
        self.tracks_layout.addItem(
            QSpacerItem(0, REGION_EDITOR_HEADER_HEIGHT + 2.0,
            vPolicy=QSizePolicy.MinimumExpanding))
        self.tracks_layout.setContentsMargins(0, 0, 0, 0)
        for i in range(REGION_EDITOR_TRACK_COUNT):
            f_track = SeqTrack(i, shared.TRACK_NAMES[i])
            self.tracks[i] = f_track
            self.tracks_layout.addWidget(f_track.group_box)
        self.automation_dict = {
            x:(None, None) for x in range(REGION_EDITOR_TRACK_COUNT)}
        self.set_track_height()

    def set_tooltips(self, a_on):
        if a_on:
            self.tracks_widget.setToolTip(mk_strings.track_panel)
        else:
            self.tracks_widget.setToolTip("")

    def set_track_height(self):
        self.tracks_widget.setUpdatesEnabled(False)
        self.tracks_widget.setFixedSize(
            QtCore.QSize(REGION_TRACK_WIDTH,
            (shared.REGION_EDITOR_TRACK_HEIGHT * REGION_EDITOR_TRACK_COUNT) +
            REGION_EDITOR_HEADER_HEIGHT))
        for f_track in self.tracks.values():
            f_track.group_box.setFixedHeight(shared.REGION_EDITOR_TRACK_HEIGHT)
        self.tracks_widget.setUpdatesEnabled(True)

    def get_track_names(self):
        return [
            self.tracks[k].track_name_lineedit.text()
            for k in sorted(self.tracks)]

    def get_atm_params(self, a_track_num):
        f_track = self.tracks[int(a_track_num)]
        return (
            f_track.automation_uid, f_track.automation_plugin)

    def update_automation(self):
        self.automation_dict = {
            x:(self.tracks[x].port_num, self.tracks[x].automation_uid)
            for x in self.tracks}

    def update_plugin_track_map(self):
        self.plugin_uid_map = {}
        for x in self.tracks:
            plugins = shared.PROJECT.get_track_plugins(x)
            if plugins:
                for y in plugins.plugins:
                    self.plugin_uid_map[int(y.plugin_uid)] = int(x)

    def has_automation(self, a_track_num):
        return self.automation_dict[int(a_track_num)]

    def update_ccs_in_use(self):
        for v in self.tracks.values():
            v.update_in_use_combobox()

    def open_tracks(self):
        f_tracks = shared.PROJECT.get_tracks()
        shared.TRACK_NAMES = f_tracks.get_names()
        global_update_track_comboboxes()
        for key, f_track in f_tracks.tracks.items():
            self.tracks[key].open_track(f_track)
            self.tracks[key].refresh()
        self.update_plugin_track_map()

    def get_tracks(self):
        f_result = pydaw_tracks()
        for k, v in self.tracks.items():
            f_result.add_track(k, v.get_track())
        return f_result

def global_update_track_comboboxes(a_index=None, a_value=None):
    if not a_index is None and not a_value is None:
        shared.TRACK_NAMES[int(a_index)] = str(a_value)
    global SUPPRESS_TRACK_COMBOBOX_CHANGES
    SUPPRESS_TRACK_COMBOBOX_CHANGES = True
    for f_cbox in shared.TRACK_NAME_COMBOBOXES:
        f_current_index = f_cbox.currentIndex()
        f_cbox.clear()
        f_cbox.clearEditText()
        f_cbox.addItems(shared.TRACK_NAMES)
        f_cbox.setCurrentIndex(f_current_index)

    shared.PLUGIN_RACK.set_track_names(shared.TRACK_NAMES)

    SUPPRESS_TRACK_COMBOBOX_CHANGES = False
    shared.ROUTING_GRAPH_WIDGET.draw_graph(
        shared.PROJECT.get_routing_graph(), shared.TRACK_PANEL.get_track_names())
    global_open_mixer()

class RegionSettings:
    """ The widget that holds the sequencer """
    def __init__(self):
        self.enabled = False
        self.widget = QWidget()
        self.widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.hlayout0 = QHBoxLayout(self.widget)
        self.hlayout0.setContentsMargins(1, 1, 1, 1)
        self.edit_mode_combobox = QComboBox()
        self.edit_mode_combobox.setMinimumWidth(132)
        self.edit_mode_combobox.addItems([_("Items"), _("Automation")])
        self.edit_mode_combobox.currentIndexChanged.connect(
            self.edit_mode_changed)

        self.menu_button = QPushButton(_("Menu"))
        self.hlayout0.addWidget(self.menu_button)
        self.menu = QMenu(self.menu_button)
        self.menu_button.setMenu(self.menu)

        self.menu_widget = QWidget()
        self.menu_layout = QGridLayout(self.menu_widget)
        self.action_widget = QWidgetAction(self.menu)
        self.action_widget.setDefaultWidget(self.menu_widget)
        self.menu.addAction(self.action_widget)

        self.toggle_edit_mode_action = QAction(
            _("Toggle Edit Mode"), self.menu_button)
        self.menu_button.addAction(self.toggle_edit_mode_action)
        self.toggle_edit_mode_action.setShortcut(
            QKeySequence.fromString("CTRL+E"))
        self.menu.addAction(self.toggle_edit_mode_action)
        self.toggle_edit_mode_action.triggered.connect(self.toggle_edit_mode)

        self.menu.addSeparator()

        self.menu_layout.addWidget(QLabel(_("Edit Mode:")), 0, 0)
        self.menu_layout.addWidget(self.edit_mode_combobox, 0, 1)

        self.reorder_tracks_action = self.menu.addAction(
            _("Reorder Tracks..."))
        self.reorder_tracks_action.triggered.connect(self.set_track_order)
        self.menu.addSeparator()
        self.hide_inactive = False
#        self.toggle_hide_action = self.menu.addAction(
#            _("Hide Inactive Instruments"))
#        self.toggle_hide_action.setCheckable(True)
#        self.toggle_hide_action.triggered.connect(self.toggle_hide_inactive)
#        self.toggle_hide_action.setShortcut(
#            QKeySequence.fromString("CTRL+H"))
        self.menu.addSeparator()
        self.unsolo_action = self.menu.addAction(_("Un-Solo All"))
        self.unsolo_action.triggered.connect(self.unsolo_all)
        self.unsolo_action.setShortcut(QKeySequence.fromString("CTRL+J"))
        self.unmute_action = self.menu.addAction(_("Un-Mute All"))
        self.unmute_action.triggered.connect(self.unmute_all)
        self.unmute_action.setShortcut(QKeySequence.fromString("CTRL+M"))

        self.snap_combobox = QComboBox()
        self.snap_combobox.addItems(
            [_("None"), _("Beat"), "1/8", "1/12", "1/16"])
        self.snap_combobox.currentIndexChanged.connect(self.set_snap)

        self.menu_layout.addWidget(QLabel(_("Snap:")), 5, 0)
        self.menu_layout.addWidget(self.snap_combobox, 5, 1)

        self.follow_checkbox = QCheckBox(_("Follow"))
        self.hlayout0.addWidget(self.follow_checkbox)

        self.hlayout0.addWidget(QLabel("H"))
        self.hzoom_slider = QSlider(QtCore.Qt.Horizontal)
        self.hlayout0.addWidget(self.hzoom_slider)
        self.hzoom_slider.setObjectName("zoom_slider")
        self.hzoom_slider.setRange(0, 30)
        self.last_hzoom = 3
        self.hzoom_slider.setValue(self.last_hzoom)
        self.hzoom_slider.setFixedWidth(90)
        self.hzoom_slider.sliderPressed.connect(self.hzoom_pressed)
        self.hzoom_slider.sliderReleased.connect(self.hzoom_released)
        self.hzoom_slider.valueChanged.connect(self.set_hzoom)
        self.is_hzooming = False

        self.hlayout0.addWidget(QLabel("V"))
        self.vzoom_slider = QSlider(QtCore.Qt.Horizontal)
        self.hlayout0.addWidget(self.vzoom_slider)
        self.vzoom_slider.setObjectName("zoom_slider")
        self.vzoom_slider.setRange(0, 60)
        self.last_vzoom = 0
        self.vzoom_slider.setValue(self.last_vzoom)
        self.vzoom_slider.setFixedWidth(60)
        self.vzoom_slider.sliderPressed.connect(self.vzoom_pressed)
        self.vzoom_slider.sliderReleased.connect(self.vzoom_released)
        self.vzoom_slider.valueChanged.connect(self.set_vzoom)
        self.is_vzooming = False

        # Ignore key and mouse wheel events, they do not work well with
        # how the zoom sliders visualize their changes
        self.hzoom_slider.wheelEvent = \
            self.hzoom_slider.keyPressEvent = \
            self.vzoom_slider.wheelEvent = \
            self.vzoom_slider.keyPressEvent = lambda x: None

        self.size_label = QLabel()
        self.size_label.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.scrollbar = shared.SEQUENCER.horizontalScrollBar()
        self.scrollbar.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.scrollbar.sliderPressed.connect(self.scrollbar_pressed)
        self.scrollbar.sliderReleased.connect(self.scrollbar_released)
        self.hlayout0.addWidget(self.scrollbar)
        self.scrollbar.setSingleStep(SEQUENCER_PX_PER_BEAT)

        self.widgets_to_disable = (
            self.hzoom_slider, self.vzoom_slider, self.menu_button)

    def toggle_edit_mode(self):
        if not libmk.IS_PLAYING:
            # This relies on the assumption that only 2 modes exist
            current_mode = self.edit_mode_combobox.currentIndex()
            self.edit_mode_combobox.setCurrentIndex(int(not current_mode))

    def scrollbar_pressed(self, a_val=None):
        if libmk.IS_PLAYING and self.follow_checkbox.isChecked():
            self.follow_checkbox.setChecked(False)

    def scrollbar_released(self, a_val=None):
        f_val = round(self.scrollbar.value() /
            SEQUENCER_PX_PER_BEAT) * SEQUENCER_PX_PER_BEAT
        self.scrollbar.setValue(int(f_val))

    def vzoom_pressed(self, a_val=None):
        self.is_vzooming = True
        self.old_px_per_beat = SEQUENCER_PX_PER_BEAT
        #self.size_label.move(QCursor.pos())
        self.size_label.setText("Track Height")
        self.set_vzoom_size()
        f_widget = shared.MAIN_WINDOW.midi_scroll_area
        f_point = QtCore.QPoint(0, REGION_EDITOR_HEADER_HEIGHT + 2)
        self.size_label.setParent(f_widget)
        self.size_label.setStyleSheet(
            "QLabel { background-color: black; color: white }")
        self.size_label.move(f_point)
        self.size_label.show()
        self.old_height_px = shared.REGION_EDITOR_TRACK_HEIGHT

    def vzoom_released(self, a_val=None):
        self.is_vzooming = False
        shared.TRACK_PANEL.set_track_height()
        self.open_region()

        f_scrollbar = shared.MAIN_WINDOW.midi_scroll_area.verticalScrollBar()
        f_scrollbar.setValue(
            (shared.REGION_EDITOR_TRACK_HEIGHT / self.old_height_px) *
            f_scrollbar.value())
        shared.MAIN_WINDOW.vscrollbar_released()  # Quantizes the vertical pos
        f_scrollbar.setSingleStep(shared.REGION_EDITOR_TRACK_HEIGHT)
        self.size_label.hide()

    def set_vzoom_size(self):
        self.size_label.setFixedSize(
            REGION_TRACK_WIDTH, shared.REGION_EDITOR_TRACK_HEIGHT + 2)

    def set_vzoom(self, a_val=None):
        if not self.is_vzooming:
            self.vzoom_slider.setValue(self.last_vzoom)
            return
        global REGION_EDITOR_TOTAL_HEIGHT
        self.last_vzoom = self.vzoom_slider.value()
        shared.REGION_EDITOR_TRACK_HEIGHT = (self.last_vzoom * 8) + 64
        REGION_EDITOR_TOTAL_HEIGHT = (REGION_EDITOR_TRACK_COUNT *
            shared.REGION_EDITOR_TRACK_HEIGHT)
        self.set_vzoom_size()

    def hzoom_pressed(self, a_val=None):
        self.is_hzooming = True
        self.old_px_per_beat = SEQUENCER_PX_PER_BEAT
        #self.size_label.move(QCursor.pos())
        self.size_label.setText("Beat")
        self.set_hzoom_size()
        f_point = QtCore.QPoint(REGION_TRACK_WIDTH + 10, 2)
        f_widget = shared.MAIN_WINDOW.midi_scroll_area
        self.size_label.setParent(f_widget)
        self.size_label.setStyleSheet(
            "QLabel { background-color: black; color: white }")
        self.size_label.move(f_point)
        self.size_label.show()

    def hzoom_released(self, a_val=None):
        self.is_hzooming = False
        pydaw_set_seq_snap()
        self.open_region()
        self.scrollbar.setValue(
            (SEQUENCER_PX_PER_BEAT / self.old_px_per_beat) *
            self.scrollbar.value())
        self.scrollbar.setSingleStep(SEQUENCER_PX_PER_BEAT)
        self.size_label.hide()

    def set_hzoom_size(self):
        self.size_label.setFixedSize(
            SEQUENCER_PX_PER_BEAT, REGION_EDITOR_HEADER_HEIGHT)

    def set_hzoom(self, a_val=None):
        if not self.is_hzooming:
            self.hzoom_slider.setValue(self.last_hzoom)
            return
        global SEQUENCER_PX_PER_BEAT, DRAW_SEQUENCER_GRAPHS
        self.last_hzoom = self.hzoom_slider.value()
        if self.last_hzoom < 3:
            DRAW_SEQUENCER_GRAPHS = False
            f_length = pydaw_get_current_region_length()
            f_width = shared.SEQUENCER.width()
            f_factor = {0:1, 1:2, 2:4}[self.last_hzoom]
            SEQUENCER_PX_PER_BEAT = (f_width / f_length) * f_factor
            self.size_label.setText("Project * {}".format(f_factor))
            self.size_label.setFixedSize(
                150, REGION_EDITOR_HEADER_HEIGHT)
        else:
            if self.last_hzoom < 6:
                self.last_hzoom = 6
            DRAW_SEQUENCER_GRAPHS = True
            SEQUENCER_PX_PER_BEAT = ((self.last_hzoom - 6) * 4) + 24
            self.size_label.setText("Beat")
            self.set_hzoom_size()

    def set_snap(self, a_val=None):
        pydaw_set_seq_snap(a_val)
        shared.MAIN_WINDOW.tab_changed()

    def edit_mode_changed(self, a_value=None):
        global REGION_EDITOR_MODE
        REGION_EDITOR_MODE = a_value
        shared.SEQUENCER.open_region()

    def toggle_hide_inactive(self):
        self.hide_inactive = self.toggle_hide_action.isChecked()
        global_update_hidden_rows()

    def unsolo_all(self):
        for f_track in shared.TRACK_PANEL.tracks.values():
            f_track.solo_checkbox.setChecked(False)

    def unmute_all(self):
        for f_track in shared.TRACK_PANEL.tracks.values():
            f_track.mute_checkbox.setChecked(False)

    def open_region(self):
        self.enabled = False
        if shared.CURRENT_REGION:
            self.clear_items()
        shared.CURRENT_REGION = shared.PROJECT.get_region()
        self.enabled = True
        shared.SEQUENCER.open_region()
        global_update_hidden_rows()
        #shared.TRANSPORT.set_time(shared.TRANSPORT.get_bar_value(), 0.0)

    def clear_items(self):
        shared.SEQUENCER.clear_drawn_items()
        shared.CURRENT_REGION = None

    def clear_new(self):
        shared.CURRENT_REGION = None
        shared.SEQUENCER.clear_new()

    def on_play(self):
        for f_widget in self.widgets_to_disable:
            f_widget.setEnabled(False)

    def on_stop(self):
        for f_widget in self.widgets_to_disable:
            f_widget.setEnabled(True)

    def set_track_order(self):
        f_result = pydaw_widgets.ordered_table_dialog(
            shared.TRACK_NAMES[1:],
            [x + 1 for x in range(len(shared.TRACK_NAMES[1:]))],
            30, 200, shared.MAIN_WINDOW,
        )
        if f_result:
            f_result = {f_result[x]:x + 1 for x in range(len(f_result))}
            f_result[0] = 0 # master track
            shared.PROJECT.reorder_tracks(f_result)
            shared.TRACK_PANEL.open_tracks()
            self.open_region()
            shared.MIDI_DEVICES_DIALOG.set_routings()
            shared.TRANSPORT.open_project()


def region_editor_set_delete_mode(a_enabled):
    global REGION_EDITOR_DELETE_MODE
    if a_enabled:
        shared.SEQUENCER.setDragMode(QGraphicsView.NoDrag)
        REGION_EDITOR_DELETE_MODE = True
        QApplication.setOverrideCursor(
            QCursor(QtCore.Qt.ForbiddenCursor))
    else:
        shared.SEQUENCER.setDragMode(QGraphicsView.RubberBandDrag)
        REGION_EDITOR_DELETE_MODE = False
        shared.SEQUENCER.selected_item_strings = set()
        QApplication.restoreOverrideCursor()



