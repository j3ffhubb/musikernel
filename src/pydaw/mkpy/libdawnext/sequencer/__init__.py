"""

"""
from . import (
    _shared,
    atm_context_menu,
    context_menu,
    header_context_menu,
)
from .audio_input import AudioInput, AudioInputWidget
from .track import SeqTrack, TrackPanel
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

        if _shared.REGION_EDITOR_MODE == 0:
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
            (
                f_pixmaps,
                f_transform,
                self.x_scale,
                self.y_scale,
            ) = shared.PROJECT.get_item_path(
                a_audio_item.item_uid,
                SEQUENCER_PX_PER_BEAT,
                shared.REGION_EDITOR_TRACK_HEIGHT - 20,
                shared.CURRENT_REGION.get_tempo_at_pos(
                    a_audio_item.start_beat,
                ),
            )
            for f_pixmap in f_pixmaps:
                f_pixmap_item = QGraphicsPixmapItem(self)
                f_pixmap_item.setCacheMode(
                    QGraphicsItem.DeviceCoordinateCache,
                )
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
            shared.AUDIO_ITEM_HANDLE_SIZE,
            shared.AUDIO_ITEM_HANDLE_HEIGHT,
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (
                shared.REGION_EDITOR_TRACK_HEIGHT * -1.0
            ) + shared.AUDIO_ITEM_HANDLE_HEIGHT,
            self.length_handle,
        )

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
            (
                shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5
            ) - (shared.REGION_EDITOR_TRACK_HEIGHT * 0.5),
            shared.AUDIO_ITEM_HANDLE_SIZE,
            (
                shared.REGION_EDITOR_TRACK_HEIGHT * 0.5
            ) + (shared.AUDIO_ITEM_HANDLE_HEIGHT * 0.5),
            self.stretch_handle,
        )
        self.stretch_handle.hide()

        self.split_line = QGraphicsLineItem(
            0.0,
            0.0,
            0.0,
            shared.REGION_EDITOR_TRACK_HEIGHT,
            self,
        )
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
        self.length_px_start = (
            self.audio_item.start_offset * SEQUENCER_PX_PER_BEAT
        )
        self.length_px_minus_start = f_length - self.length_px_start

        self.rect_orig = QtCore.QRectF(
            0.0,
            0.0,
            f_length,
            shared.REGION_EDITOR_TRACK_HEIGHT,
        )
        self.setRect(self.rect_orig)

        label_rect = QtCore.QRectF(0.0, 0.0, f_length, 20)
        self.label_bg.setRect(label_rect)

        f_track_num = REGION_EDITOR_HEADER_HEIGHT + (
            shared.REGION_EDITOR_TRACK_HEIGHT * self.audio_item.track_num
        )

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
            (
                shared.REGION_EDITOR_TRACK_HEIGHT
                -
                shared.AUDIO_ITEM_HANDLE_HEIGHT
            ),
        )
        self.start_handle.setPos(
            0.0,
            (
                shared.REGION_EDITOR_TRACK_HEIGHT
                -
                shared.AUDIO_ITEM_HANDLE_HEIGHT
            )
        )
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
            if _shared.REGION_EDITOR_MODE == 0:
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
            if _shared.REGION_EDITOR_MODE == 0:
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

        self.addAction(_shared.copy_action)
        self.addAction(context_menu.cut_action)
        self.addAction(atm_context_menu.break_atm_action)
        self.addAction(atm_context_menu.unbreak_atm_action)
        self.addAction(_shared.delete_action)
        self.addAction(context_menu.unlink_selected_action)
        self.addAction(context_menu.unlink_unique_action)
        self.addAction(context_menu.unlink_action)
        self.addAction(context_menu.rename_action)
        self.addAction(context_menu.transpose_action)
        self.addAction(context_menu.glue_action)

        self.context_menu_enabled = True

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
        if _shared.REGION_EDITOR_MODE == 0:
            self.populate_takes_menu()
            context_menu.exec_(QCursor.pos())
        elif _shared.REGION_EDITOR_MODE == 1:
            atm_context_menu.exec_(QCursor.pos())
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
                    f_point = pydaw_atm_point(
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
            if REGION_EDITOR_DELETE_MODE:
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
        global CACHED_SEQ_LEN
        shared.ATM_REGION = shared.PROJECT.get_atm_region()
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
            not libmk.IS_PLAYING
            and
            a_event.button() != QtCore.Qt.RightButton
        ):
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
        self.header.contextMenuEvent = header_context_menu.show
        self.scene.addItem(self.header)

        for f_marker in shared.CURRENT_REGION.get_markers():
            if f_marker.type == 1:  # Loop
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
                    f_marker.beat * SEQUENCER_PX_PER_BEAT,
                    REGION_EDITOR_HEADER_ROW_HEIGHT,
                )
                item.setToolTip(f_text)
                item.mousePressEvent = TempoMarkerEvent(
                    f_marker.beat,
                ).mouse_press
                self.draw_region(f_marker)
            elif f_marker.type == 3:  # Text
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
        shared.PROJECT.save_atm_region(shared.ATM_REGION)
        if a_open:
            self.open_region()

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
        _shared.REGION_EDITOR_MODE = a_value
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

