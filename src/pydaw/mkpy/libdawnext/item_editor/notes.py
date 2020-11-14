"""

"""

from .abstract import AbstractItemEditor, ItemEditorHeader
from mkpy import libmk
from mkpy.libdawnext import shared
from mkpy.libdawnext.project import *
from mkpy.libdawnext.shared import *
from mkpy.libmk import mk_project
from mkpy.libpydaw import (
    pydaw_util,
    pydaw_widgets,
)
from mkpy.libpydaw import scales
from mkpy.libpydaw.pydaw_util import *
from mkpy.libpydaw.translate import _
from mkpy.mkqt import *

PIANO_ROLL_HEADER_HEIGHT = 45
SELECTED_NOTE_GRADIENT = QLinearGradient(
    QtCore.QPointF(0, 0),
    QtCore.QPointF(0, 12),
)
SELECTED_NOTE_GRADIENT.setColorAt(0, QColor(180, 172, 100))
SELECTED_NOTE_GRADIENT.setColorAt(1, QColor(240, 240, 240))

SELECTED_PIANO_NOTE = None   #Used for mouse click hackery

PIANO_ROLL_NOTE_LABELS = [
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

PIANO_NOTE_GRADIENT_TUPLE = \
    ((255, 0, 0), (255, 123, 0), (255, 255, 0), (123, 255, 0), (0, 255, 0),
     (0, 255, 123), (0, 255, 255), (0, 123, 255), (0, 0, 255), (0, 0, 255))

PIANO_ROLL_DELETE_MODE = False
PIANO_ROLL_DELETED_NOTES = []


def piano_roll_set_delete_mode(a_enabled):
    global PIANO_ROLL_DELETE_MODE, PIANO_ROLL_DELETED_NOTES
    if a_enabled:
        shared.PIANO_ROLL_EDITOR.setDragMode(QGraphicsView.NoDrag)
        PIANO_ROLL_DELETED_NOTES = []
        PIANO_ROLL_DELETE_MODE = True
        QApplication.setOverrideCursor(
            QCursor(QtCore.Qt.ForbiddenCursor))
    else:
        shared.PIANO_ROLL_EDITOR.setDragMode(QGraphicsView.RubberBandDrag)
        PIANO_ROLL_DELETE_MODE = False
        for f_item in PIANO_ROLL_DELETED_NOTES:
            f_item.delete()
        shared.PIANO_ROLL_EDITOR.selected_note_strings = []
        global_save_and_reload_items()
        QApplication.restoreOverrideCursor()


class PianoRollNoteItem(pydaw_widgets.QGraphicsRectItemNDL):
    """ An individual note in the PianoRollEditor """
    def __init__(
            self, a_length, a_note_height, a_note,
            a_note_item, a_enabled=True):
        QGraphicsRectItem.__init__(self, 0, 0, a_length, a_note_height)
        if a_enabled:
            self.setFlag(QGraphicsItem.ItemIsMovable)
            self.setFlag(QGraphicsItem.ItemIsSelectable)
            self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
            self.setZValue(1002.0)
        else:
            self.setZValue(1001.0)
            self.setEnabled(False)
            self.setOpacity(0.3)
        self.note_height = a_note_height
        self.current_note_text = None
        self.note_item = a_note_item
        self.setAcceptHoverEvents(True)
        self.resize_start_pos = self.note_item.start
        self.is_copying = False
        self.is_velocity_dragging = False
        self.is_velocity_curving = False
        if SELECTED_PIANO_NOTE is not None and \
        a_note_item == SELECTED_PIANO_NOTE:
            self.is_resizing = True
            shared.PIANO_ROLL_EDITOR.click_enabled = True
        else:
            self.is_resizing = False
        self.showing_resize_cursor = False
        self.resize_rect = self.rect()
        self.mouse_y_pos = QCursor.pos().y()
        self.note_text = QGraphicsSimpleTextItem(self)
        self.note_text.setPen(QPen(QtCore.Qt.black))
        self.update_note_text()
        self.vel_line = QGraphicsLineItem(self)
        self.set_vel_line()
        self.set_brush()

    def set_vel_line(self):
        f_vel = self.note_item.velocity
        f_rect = self.rect()
        f_y = (1.0 - (f_vel * 0.007874016)) * f_rect.height()
        f_width = f_rect.width()
        self.vel_line.setLine(0.0, f_y, f_width, f_y)

    def set_brush(self):
        f_val = (1.0 - (self.note_item.velocity / 127.0)) * 9.0
        f_val = pydaw_util.pydaw_clip_value(f_val, 0.0, 9.0)
        f_int = int(f_val)
        f_frac = f_val - f_int
        f_vals = []
        for f_i in range(3):
            f_val = (((PIANO_NOTE_GRADIENT_TUPLE[f_int + 1][f_i] -
                PIANO_NOTE_GRADIENT_TUPLE[f_int][f_i]) * f_frac) +
                PIANO_NOTE_GRADIENT_TUPLE[f_int][f_i])
            f_vals.append(int(f_val))
        f_vals_m1 = pydaw_rgb_minus(f_vals, 90)
        f_vals_m2 = pydaw_rgb_minus(f_vals, 120)
        f_gradient = QLinearGradient(0.0, 0.0, 0.0, self.note_height)
        f_gradient.setColorAt(0.0, QColor(*f_vals_m1))
        f_gradient.setColorAt(0.4, QColor(*f_vals))
        f_gradient.setColorAt(0.6, QColor(*f_vals))
        f_gradient.setColorAt(1.0, QColor(*f_vals_m2))
        self.setBrush(f_gradient)

    def update_note_text(self, a_note_num=None):
        f_note_num = a_note_num if a_note_num is not None \
            else self.note_item.note_num
        f_octave = (f_note_num // 12) - 2
        f_note = PIANO_ROLL_NOTE_LABELS[f_note_num % 12]
        f_text = "{}{}".format(f_note, f_octave)
        if f_text != self.current_note_text:
            self.current_note_text = f_text
            self.note_text.setText(f_text)

    def mouse_is_at_end(self, a_pos):
        f_width = self.rect().width()
        if f_width >= 30.0:
            return a_pos.x() > (f_width - 15.0)
        else:
            return a_pos.x() > (f_width * 0.72)

    def hoverMoveEvent(self, a_event):
        #QGraphicsRectItem.hoverMoveEvent(self, a_event)
        if not self.is_resizing:
            shared.PIANO_ROLL_EDITOR.click_enabled = False
            self.show_resize_cursor(a_event)

    def delete_later(self):
        global PIANO_ROLL_DELETED_NOTES
        if self.isEnabled() and self not in PIANO_ROLL_DELETED_NOTES:
            PIANO_ROLL_DELETED_NOTES.append(self)
            self.hide()

    def delete(self):
        shared.CURRENT_ITEM.remove_note(self.note_item)

    def show_resize_cursor(self, a_event):
        f_is_at_end = self.mouse_is_at_end(a_event.pos())
        if f_is_at_end and not self.showing_resize_cursor:
            QApplication.setOverrideCursor(
                QCursor(QtCore.Qt.SizeHorCursor))
            self.showing_resize_cursor = True
        elif not f_is_at_end and self.showing_resize_cursor:
            QApplication.restoreOverrideCursor()
            self.showing_resize_cursor = False

    def get_selected_string(self):
        return str(self.note_item)

    def hoverEnterEvent(self, a_event):
        QGraphicsRectItem.hoverEnterEvent(self, a_event)
        shared.PIANO_ROLL_EDITOR.click_enabled = False

    def hoverLeaveEvent(self, a_event):
        QGraphicsRectItem.hoverLeaveEvent(self, a_event)
        shared.PIANO_ROLL_EDITOR.click_enabled = True
        QApplication.restoreOverrideCursor()
        self.showing_resize_cursor = False

    def mouseDoubleClickEvent(self, a_event):
        QGraphicsRectItem.mouseDoubleClickEvent(self, a_event)
        QApplication.restoreOverrideCursor()

    def mousePressEvent(self, a_event):
        if not self.isSelected():
            shared.PIANO_ROLL_EDITOR.scene.clearSelection()
            self.setSelected(True)
        if shared.EDITOR_MODE == shared.EDITOR_MODE_ERASE:
            piano_roll_set_delete_mode(True)
            self.delete_later()
        elif a_event.modifiers() == \
        QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier:
            self.is_velocity_dragging = True
        elif a_event.modifiers() == \
        QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier:
            f_list = [x.note_item.start
                for x in shared.PIANO_ROLL_EDITOR.get_selected_items()]
            if len(f_list) > 1:
                f_list.sort()
                self.is_velocity_curving = True
                self.vc_start = f_list[0]
                self.vc_mid = self.note_item.start
                self.vc_end = f_list[-1]
            elif len(f_list) <= 1:
                self.is_velocity_dragging = True
        else:
            a_event.setAccepted(True)
            QGraphicsRectItem.mousePressEvent(self, a_event)
            self.setBrush(SELECTED_NOTE_GRADIENT)
            self.o_pos = self.pos()
            if self.mouse_is_at_end(a_event.pos()):
                self.is_resizing = True
                self.mouse_y_pos = QCursor.pos().y()
                self.resize_last_mouse_pos = a_event.pos().x()
                for f_item in shared.PIANO_ROLL_EDITOR.get_selected_items():
                    f_item.resize_start_pos = f_item.note_item.start
                    f_item.resize_pos = f_item.pos()
                    f_item.resize_rect = f_item.rect()
            elif a_event.modifiers() == QtCore.Qt.ControlModifier:
                self.is_copying = True
                for f_item in shared.PIANO_ROLL_EDITOR.get_selected_items():
                    shared.PIANO_ROLL_EDITOR.draw_note(f_item.note_item)
        if self.is_velocity_curving or self.is_velocity_dragging:
            a_event.setAccepted(True)
            QGraphicsRectItem.mousePressEvent(self, a_event)
            self.orig_y = a_event.pos().y()
            QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)
            for f_item in shared.PIANO_ROLL_EDITOR.get_selected_items():
                f_item.orig_value = f_item.note_item.velocity
                f_item.set_brush()
            for f_item in shared.PIANO_ROLL_EDITOR.note_items:
                f_item.note_text.setText(str(f_item.note_item.velocity))
        shared.PIANO_ROLL_EDITOR.click_enabled = True

    def mouseMoveEvent(self, a_event):
        if self.is_velocity_dragging or self.is_velocity_curving:
            f_pos = a_event.pos()
            f_y = f_pos.y()
            f_diff_y = self.orig_y - f_y
            f_val = (f_diff_y * 0.5)
        else:
            QGraphicsRectItem.mouseMoveEvent(self, a_event)

        if self.is_resizing:
            f_pos_x = a_event.pos().x()
            self.resize_last_mouse_pos = a_event.pos().x()
        for f_item in shared.PIANO_ROLL_EDITOR.get_selected_items():
            if self.is_resizing:
                if shared.PIANO_ROLL_SNAP:
                    f_adjusted_width = round(
                        f_pos_x / shared.PIANO_ROLL_SNAP_VALUE) * \
                        shared.PIANO_ROLL_SNAP_VALUE
                    if f_adjusted_width == 0.0:
                        f_adjusted_width = shared.PIANO_ROLL_SNAP_VALUE
                else:
                    f_adjusted_width = pydaw_clip_min(
                        f_pos_x,
                        shared.PIANO_ROLL_MIN_NOTE_LENGTH,
                    )
                f_item.resize_rect.setWidth(f_adjusted_width)
                f_item.setRect(f_item.resize_rect)
                f_item.setPos(f_item.resize_pos.x(), f_item.resize_pos.y())
                QCursor.setPos(QCursor.pos().x(), self.mouse_y_pos)
            elif self.is_velocity_dragging:
                f_new_vel = pydaw_util.pydaw_clip_value(
                    f_val + f_item.orig_value, 1, 127)
                f_new_vel = int(f_new_vel)
                f_item.note_item.velocity = f_new_vel
                f_item.note_text.setText(str(f_new_vel))
                f_item.set_brush()
                f_item.set_vel_line()
            elif self.is_velocity_curving:
                f_start = f_item.note_item.start
                if f_start == self.vc_mid:
                    f_new_vel = f_val + f_item.orig_value
                else:
                    if f_start > self.vc_mid:
                        f_frac = (f_start -
                            self.vc_mid) / (self.vc_end - self.vc_mid)
                        f_new_vel = pydaw_util.linear_interpolate(
                            f_val, 0.3 * f_val, f_frac)
                    else:
                        f_frac = (f_start -
                            self.vc_start) / (self.vc_mid - self.vc_start)
                        f_new_vel = pydaw_util.linear_interpolate(
                            0.3 * f_val, f_val, f_frac)
                    f_new_vel += f_item.orig_value
                f_new_vel = pydaw_util.pydaw_clip_value(f_new_vel, 1, 127)
                f_new_vel = int(f_new_vel)
                f_item.note_item.velocity = f_new_vel
                f_item.note_text.setText(str(f_new_vel))
                f_item.set_brush()
                f_item.set_vel_line()
            else:
                f_pos_x = f_item.pos().x()
                f_pos_y = f_item.pos().y()
                if f_pos_x < shared.PIANO_KEYS_WIDTH:
                    f_pos_x = shared.PIANO_KEYS_WIDTH
                elif f_pos_x > shared.PIANO_ROLL_GRID_MAX_START_TIME:
                    f_pos_x = shared.PIANO_ROLL_GRID_MAX_START_TIME
                if f_pos_y < PIANO_ROLL_HEADER_HEIGHT:
                    f_pos_y = PIANO_ROLL_HEADER_HEIGHT
                elif f_pos_y > shared.PIANO_ROLL_TOTAL_HEIGHT:
                    f_pos_y = shared.PIANO_ROLL_TOTAL_HEIGHT
                f_pos_y = \
                    (int((f_pos_y - PIANO_ROLL_HEADER_HEIGHT) /
                    self.note_height) * self.note_height) + \
                    PIANO_ROLL_HEADER_HEIGHT
                if shared.PIANO_ROLL_SNAP:
                    f_pos_x = (int((f_pos_x - shared.PIANO_KEYS_WIDTH) /
                    shared.PIANO_ROLL_SNAP_VALUE) *
                    shared.PIANO_ROLL_SNAP_VALUE) + shared.PIANO_KEYS_WIDTH
                f_item.setPos(f_pos_x, f_pos_y)
                f_new_note = self.y_pos_to_note(f_pos_y)
                f_item.update_note_text(f_new_note)

    def y_pos_to_note(self, a_y):
        return int(shared.PIANO_ROLL_NOTE_COUNT -
            ((a_y - PIANO_ROLL_HEADER_HEIGHT) /
            shared.PIANO_ROLL_NOTE_HEIGHT))

    def mouseReleaseEvent(self, a_event):
        if PIANO_ROLL_DELETE_MODE:
            piano_roll_set_delete_mode(False)
            return
        a_event.setAccepted(True)
        f_recip = 1.0 / shared.PIANO_ROLL_GRID_WIDTH
        QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        global SELECTED_PIANO_NOTE
        if self.is_copying:
            f_new_selection = []
        for f_item in shared.PIANO_ROLL_EDITOR.get_selected_items():
            f_pos_x = f_item.pos().x()
            f_pos_y = f_item.pos().y()
            if self.is_resizing:
                f_new_note_length = ((f_pos_x + f_item.rect().width() -
                    shared.PIANO_KEYS_WIDTH) * f_recip *
                    shared.CURRENT_ITEM_LEN) - f_item.resize_start_pos
                if shared.PIANO_ROLL_SNAP and \
                f_new_note_length < shared.PIANO_ROLL_SNAP_BEATS:
                    f_new_note_length = shared.PIANO_ROLL_SNAP_BEATS
                elif f_new_note_length < pydaw_min_note_length:
                    f_new_note_length = pydaw_min_note_length
                f_item.note_item.set_length(f_new_note_length)
            elif self.is_velocity_dragging or self.is_velocity_curving:
                pass
            else:
                f_new_note_start = (f_pos_x -
                    shared.PIANO_KEYS_WIDTH) * shared.CURRENT_ITEM_LEN * f_recip
                f_new_note_num = self.y_pos_to_note(f_pos_y)
                if self.is_copying:
                    f_new_note = mk_project.pydaw_note(
                        f_new_note_start, f_item.note_item.length,
                        f_new_note_num, f_item.note_item.velocity)
                    shared.CURRENT_ITEM.add_note(f_new_note, False)
                    # pass a ref instead of a str in case
                    # fix_overlaps() modifies it.
                    f_item.note_item = f_new_note
                    f_new_selection.append(f_item)
                else:
                    shared.CURRENT_ITEM.notes.remove(f_item.note_item)
                    f_item.note_item.set_start(f_new_note_start)
                    f_item.note_item.note_num = f_new_note_num
                    shared.CURRENT_ITEM.notes.append(f_item.note_item)
                    shared.CURRENT_ITEM.notes.sort()
        if self.is_resizing:
            shared.LAST_NOTE_RESIZE = self.note_item.length
        shared.CURRENT_ITEM.fix_overlaps()
        SELECTED_PIANO_NOTE = None
        shared.PIANO_ROLL_EDITOR.selected_note_strings = []
        if self.is_copying:
            for f_new_item in f_new_selection:
                shared.PIANO_ROLL_EDITOR.selected_note_strings.append(
                    f_new_item.get_selected_string())
        else:
            for f_item in shared.PIANO_ROLL_EDITOR.get_selected_items():
                shared.PIANO_ROLL_EDITOR.selected_note_strings.append(
                    f_item.get_selected_string())
        for f_item in shared.PIANO_ROLL_EDITOR.note_items:
            f_item.is_resizing = False
            f_item.is_copying = False
            f_item.is_velocity_dragging = False
            f_item.is_velocity_curving = False
        global_save_and_reload_items()
        self.showing_resize_cursor = False
        QApplication.restoreOverrideCursor()
        shared.PIANO_ROLL_EDITOR.click_enabled = True

class PianoKeyItem(QGraphicsRectItem):
    """ This is a piano key on the PianoRollEditor
    """
    def __init__(self, a_piano_width, a_note_height, a_parent):
        QGraphicsRectItem.__init__(
            self, 0, 0, a_piano_width, a_note_height, a_parent)
        self.setAcceptHoverEvents(True)
        self.hover_brush = QColor(200, 200, 200)

    def hoverEnterEvent(self, a_event):
        QGraphicsRectItem.hoverEnterEvent(self, a_event)
        self.o_brush = self.brush()
        self.setBrush(self.hover_brush)
        QApplication.restoreOverrideCursor()

    def hoverLeaveEvent(self, a_event):
        QGraphicsRectItem.hoverLeaveEvent(self, a_event)
        self.setBrush(self.o_brush)

class PianoRollEditor(AbstractItemEditor):
    """ This is the QGraphicsView and QGraphicsScene where notes are drawn
    """
    def __init__(self):
        self.viewer_width = 1000
        self.grid_div = 16

        self.end_octave = 8
        self.start_octave = -2
        self.notes_in_octave = 12
        self.piano_width = 32
        self.padding = 2

        self.update_note_height()

        AbstractItemEditor.__init__(self, shared.PIANO_KEYS_WIDTH)
        self.scene = QGraphicsScene(self)
        self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.scene.setBackgroundBrush(pydaw_widgets.SCENE_BACKGROUND_BRUSH)
        self.scene.mousePressEvent = self.sceneMousePressEvent
        self.scene.mouseReleaseEvent = self.sceneMouseReleaseEvent
        self.setAlignment(QtCore.Qt.AlignLeft)
        self.setScene(self.scene)
        self.first_open = True

        self.has_selected = False

        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.note_items = []

        self.right_click = False
        self.left_click = False
        self.click_enabled = True
        self.last_scale = 1.0
        self.last_x_scale = 1.0
        self.scene.selectionChanged.connect(self.highlight_selected)
        self.selected_note_strings = []
        self.piano_keys = None
        self.vel_rand = 0
        self.vel_emphasis = 0
        self.clipboard = []

    def update_note_height(self):
        self.note_height = shared.PIANO_ROLL_NOTE_HEIGHT
        self.octave_height = self.notes_in_octave * self.note_height

        self.piano_height = self.note_height * shared.PIANO_ROLL_NOTE_COUNT

        self.piano_height = self.note_height * shared.PIANO_ROLL_NOTE_COUNT
        shared.PIANO_ROLL_TOTAL_HEIGHT = self.piano_height + PIANO_ROLL_HEADER_HEIGHT

    def get_selected_items(self):
        return (x for x in self.note_items if x.isSelected())

    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip(mk_strings.PianoRollEditor)
        else:
            self.setToolTip("")

    def prepare_to_quit(self):
        self.scene.clearSelection()
        self.scene.clear()

    def highlight_keys(self, a_state, a_note):
        f_note = int(a_note)
        f_state = int(a_state)
        if self.piano_keys is not None and f_note in self.piano_keys:
            if f_state == 0:
                if self.piano_keys[f_note].is_black:
                    self.piano_keys[f_note].setBrush(QColor(0, 0, 0))
                else:
                    self.piano_keys[f_note].setBrush(
                        QColor(255, 255, 255))
            elif f_state == 1:
                self.piano_keys[f_note].setBrush(QColor(237, 150, 150))
            else:
                assert False, "Invalid state"

    def set_grid_div(self, a_div):
        self.grid_div = int(a_div)

    def scrollContentsBy(self, x, y):
        QGraphicsView.scrollContentsBy(self, x, y)
        self.set_header_and_keys()

    def set_header_and_keys(self):
        f_point = self.get_scene_pos()
        self.piano.setPos(f_point.x(), PIANO_ROLL_HEADER_HEIGHT)
        self.header.setPos(self.piano_width + self.padding, f_point.y())

    def get_scene_pos(self):
        return QtCore.QPointF(
            self.horizontalScrollBar().value(),
            self.verticalScrollBar().value())

    def highlight_selected(self):
        self.has_selected = False
        for f_item in self.note_items:
            if f_item.isSelected():
                f_item.setBrush(SELECTED_NOTE_GRADIENT)
                f_item.note_item.is_selected = True
                self.has_selected = True
            else:
                f_item.note_item.is_selected = False
                f_item.set_brush()

    def set_selected_strings(self):
        self.selected_note_strings = [x.get_selected_string()
            for x in self.note_items if x.isSelected()]

    def keyPressEvent(self, a_event):
        QGraphicsView.keyPressEvent(self, a_event)
        QApplication.restoreOverrideCursor()

    def half_selected(self):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return

        self.selected_note_strings = []

        min_split_size = 4.0 / 64.0

        f_selected = [x for x in self.note_items if x.isSelected()]
        if not f_selected:
            QMessageBox.warning(self, _("Error"), _("Nothing selected"))
            return

        for f_note in f_selected:
            if f_note.note_item.length < min_split_size:
                continue
            f_half = f_note.note_item.length * 0.5
            f_note.note_item.set_length(f_half)
            f_new_start = f_note.note_item.start + f_half
            f_note_num = f_note.note_item.note_num
            f_velocity = f_note.note_item.velocity
            self.selected_note_strings.append(str(f_note.note_item))
            f_new_note_item = mk_project.pydaw_note(
                f_new_start, f_half, f_note_num, f_velocity)
            shared.CURRENT_ITEM.add_note(f_new_note_item, False)
            self.selected_note_strings.append(str(f_new_note_item))

        global_save_and_reload_items()

    def glue_selected(self):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return

        f_selected = [x for x in self.note_items if x.isSelected()]
        if not f_selected:
            QMessageBox.warning(self, _("Error"), _("Nothing selected"))
            return

        f_dict = {}
        for f_note in f_selected:
            f_note_num = f_note.note_item.note_num
            if not f_note_num in f_dict:
                f_dict[f_note_num] = []
            f_dict[f_note_num].append(f_note)

        f_result = []

        for k in sorted(f_dict.keys()):
            v = f_dict[k]
            if len(v) == 1:
                v[0].setSelected(False)
                f_dict.pop(k)
            else:
                f_max = -1.0
                f_min = 99999999.9
                for f_note in f_dict[k]:
                    f_start = f_note.note_item.start
                    if f_start < f_min:
                        f_min = f_start
                    f_end = f_note.note_item.length + f_start
                    if f_end > f_max:
                        f_max = f_end
                f_vels = [x.note_item.velocity for x in f_dict[k]]
                f_vel = int(sum(f_vels) // len(f_vels))

                print(str(f_max))
                print(str(f_min))
                f_length = f_max - f_min
                print(str(f_length))
                f_start = f_min
                print(str(f_start))
                f_new_note = mk_project.pydaw_note(f_start, f_length, k, f_vel)
                print(str(f_new_note))
                f_result.append(f_new_note)

        self.delete_selected(False)
        for f_new_note in f_result:
            shared.CURRENT_ITEM.add_note(f_new_note, False)
        global_save_and_reload_items()


    def copy_selected(self):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return 0
        self.clipboard = [
            str(x.note_item) for x in self.note_items if x.isSelected()]
        return len(self.clipboard)

    def paste(self):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return
        if not self.clipboard:
            QMessageBox.warning(
                self, _("Error"), _("Nothing copied to the clipboard"))
            return
        for f_item in self.clipboard:
            shared.CURRENT_ITEM.add_note(mk_project.pydaw_note.from_str(f_item))
        global_save_and_reload_items()
        self.scene.clearSelection()
        for f_item in self.note_items:
            f_tuple = str(f_item.note_item)
            if f_tuple in self.clipboard:
                f_item.setSelected(True)

    def delete_selected(self, a_save_and_reload=True):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return
        self.selected_note_strings = []
        for f_item in self.get_selected_items():
            shared.CURRENT_ITEM.remove_note(f_item.note_item)
        if a_save_and_reload:
            global_save_and_reload_items()

    def transpose_selected(self, a_amt):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return

        f_list = [x for x in self.note_items if x.isSelected()]
        if not f_list:
            QMessageBox.warning(self, _("Error"), _("No notes selected"))
            return
        self.selected_note_strings = []
        for f_item in f_list:
            f_item.note_item.note_num = pydaw_clip_value(
                f_item.note_item.note_num + a_amt, 0, 120)
            self.selected_note_strings.append(f_item.get_selected_string())
        global_save_and_reload_items()

    def focusOutEvent(self, a_event):
        QGraphicsView.focusOutEvent(self, a_event)
        QApplication.restoreOverrideCursor()

    def sceneMouseReleaseEvent(self, a_event):
        if PIANO_ROLL_DELETE_MODE:
            piano_roll_set_delete_mode(False)
        else:
            QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        self.click_enabled = True

    def sceneMousePressEvent(self, a_event):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
        elif a_event.button() == QtCore.Qt.RightButton:
            return
        elif shared.EDITOR_MODE == shared.EDITOR_MODE_SELECT:
            if self.click_enabled:
                self.scene.clearSelection()
            self.hover_restore_cursor_event()
        elif shared.EDITOR_MODE == shared.EDITOR_MODE_ERASE:
            piano_roll_set_delete_mode(True)
            return
        elif (
            a_event.modifiers() == (
                QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier
            )
            or
            a_event.modifiers() == (
                QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier
            )
        ):
            pass
        elif (
            self.click_enabled
            and
            shared.ITEM_EDITOR.enabled
            and
            shared.EDITOR_MODE == shared.EDITOR_MODE_DRAW
        ):
            self.scene.clearSelection()
            f_pos = a_event.scenePos()
            if self.get_item_at_pos(f_pos, ItemEditorHeader):
                a_event.setAccepted(True)
                QGraphicsScene.mousePressEvent(self.scene, a_event)
                return
            f_pos_x = a_event.scenePos().x()
            f_pos_y = a_event.scenePos().y()
            if (
                f_pos_x > shared.PIANO_KEYS_WIDTH
                and
                f_pos_x < shared.PIANO_ROLL_GRID_MAX_START_TIME
                and
                f_pos_y > PIANO_ROLL_HEADER_HEIGHT
                and
                f_pos_y < shared.PIANO_ROLL_TOTAL_HEIGHT
            ):
                f_recip = 1.0 / shared.PIANO_ROLL_GRID_WIDTH
                if self.vel_rand == 1:
                    pass
                elif self.vel_rand == 2:
                    pass
                f_note = int(
                    shared.PIANO_ROLL_NOTE_COUNT - ((f_pos_y -
                    PIANO_ROLL_HEADER_HEIGHT) / self.note_height)) + 1
                if shared.PIANO_ROLL_SNAP:
                    f_beat = (
                        int(
                            (f_pos_x - shared.PIANO_KEYS_WIDTH) /
                            shared.PIANO_ROLL_SNAP_VALUE
                        ) * shared.PIANO_ROLL_SNAP_VALUE
                    ) * f_recip * shared.CURRENT_ITEM_LEN
                    f_note_item = mk_project.pydaw_note(
                        f_beat,
                        shared.LAST_NOTE_RESIZE,
                        f_note,
                        self.get_vel(f_beat),
                    )
                else:
                    f_beat = (
                        f_pos_x - shared.PIANO_KEYS_WIDTH
                    ) * f_recip * shared.CURRENT_ITEM_LEN
                    f_note_item = mk_project.pydaw_note(
                        f_beat, 0.25, f_note, self.get_vel(f_beat))
                shared.ITEM_EDITOR.add_note(f_note_item)
                global SELECTED_PIANO_NOTE
                SELECTED_PIANO_NOTE = f_note_item
                f_drawn_note = self.draw_note(f_note_item)
                f_drawn_note.setSelected(True)
                f_drawn_note.resize_start_pos = f_drawn_note.note_item.start
                f_drawn_note.resize_pos = f_drawn_note.pos()
                f_drawn_note.resize_rect = f_drawn_note.rect()
                f_drawn_note.is_resizing = True
                f_cursor_pos = QCursor.pos()
                f_drawn_note.mouse_y_pos = f_cursor_pos.y()
                f_drawn_note.resize_last_mouse_pos = \
                    f_pos_x - f_drawn_note.pos().x()

        a_event.setAccepted(True)
        QGraphicsScene.mousePressEvent(self.scene, a_event)
        QApplication.restoreOverrideCursor()

    def mouseMoveEvent(self, a_event):
        QGraphicsView.mouseMoveEvent(self, a_event)
        if PIANO_ROLL_DELETE_MODE:
            for f_item in self.items(a_event.pos()):
                if isinstance(f_item, PianoRollNoteItem):
                    f_item.delete_later()

    def hover_restore_cursor_event(self, a_event=None):
        QApplication.restoreOverrideCursor()

    def draw_header(self):
        AbstractItemEditor.draw_header(
            self, self.viewer_width, PIANO_ROLL_HEADER_HEIGHT)
        self.header.hoverEnterEvent = self.hover_restore_cursor_event
        self.scene.addItem(self.header)
        #self.header.mapToScene(self.piano_width + self.padding, 0.0)
        self.px_per_beat = self.viewer_width / shared.CURRENT_ITEM_LEN
        self.value_width = self.px_per_beat / self.grid_div
        self.header.setZValue(1003.0)
        if shared.ITEM_REF_POS:
            f_start, f_end = shared.ITEM_REF_POS
            f_start_x = f_start * self.px_per_beat
            f_end_x = f_end * self.px_per_beat
            f_start_line = QGraphicsLineItem(
                f_start_x, 0.0, f_start_x,
                PIANO_ROLL_HEADER_HEIGHT, self.header)
            f_start_line.setPen(shared.START_PEN)
            f_end_line = QGraphicsLineItem(
                f_end_x, 0.0, f_end_x, PIANO_ROLL_HEADER_HEIGHT, self.header)
            f_end_line.setPen(shared.END_PEN)

    def draw_piano(self):
        self.piano_keys = {}
        f_black_notes = [2, 4, 6, 9, 11]
        f_piano_label = QFont()
        f_piano_label.setPointSize(8)
        self.piano = QGraphicsRectItem(
            0, 0, self.piano_width, self.piano_height)
        self.scene.addItem(self.piano)
        self.piano.mapToScene(0.0, PIANO_ROLL_HEADER_HEIGHT)
        f_key = PianoKeyItem(self.piano_width, self.note_height, self.piano)
        f_label = QGraphicsSimpleTextItem("C8", f_key)
        f_label.setPen(QtCore.Qt.black)
        f_label.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        f_label.setPos(4, 0)
        f_label.setFont(f_piano_label)
        f_key.setBrush(QColor(255, 255, 255))
        f_note_index = 0
        f_note_num = 0

        for i in range(self.end_octave - self.start_octave,
                       self.start_octave - self.start_octave, -1):
            for j in range(self.notes_in_octave, 0, -1):
                f_key = PianoKeyItem(
                    self.piano_width, self.note_height, self.piano)
                self.piano_keys[f_note_index] = f_key
                f_note_index += 1
                f_key.setPos(
                    0, (self.note_height * j) + (self.octave_height * (i - 1)))

                f_key.setToolTip("{} - {}hz - MIDI note #{}".format(
                    pydaw_util.note_num_to_string(f_note_num),
                    round(pydaw_pitch_to_hz(f_note_num)), f_note_num))
                f_note_num += 1
                if j == 12:
                    f_label = QGraphicsSimpleTextItem("C{}".format(
                        self.end_octave - i), f_key)
                    f_label.setFlag(
                        QGraphicsItem.ItemIgnoresTransformations)
                    f_label.setPos(4, 0)
                    f_label.setFont(f_piano_label)
                    f_label.setPen(QtCore.Qt.black)
                if j in f_black_notes:
                    f_key.setBrush(QColor(0, 0, 0))
                    f_key.is_black = True
                else:
                    f_key.setBrush(QColor(255, 255, 255))
                    f_key.is_black = False
        self.piano.setZValue(1000.0)

    def draw_grid(self):
        f_black_key_brush = QBrush(QColor(30, 30, 30, 90))
        f_white_key_brush = QBrush(QColor(210, 210, 210, 90))
        f_base_brush = QBrush(QColor(255, 255, 255, 120))
        try:
            f_index = shared.PIANO_ROLL_EDITOR_WIDGET.scale_combobox.currentIndex()
        except NameError:
            f_index = 0
        if self.first_open:
            f_index = 0

        f_octave_brushes = scales.scale_to_value_list(
            f_index, [f_base_brush, f_white_key_brush, f_black_key_brush])

        f_current_key = 0
        if not self.first_open:
            f_index = \
                12 - shared.PIANO_ROLL_EDITOR_WIDGET.scale_key_combobox.currentIndex()
            f_octave_brushes = \
                f_octave_brushes[f_index:] + f_octave_brushes[:f_index]
        self.first_open = False
        f_note_bar = QGraphicsRectItem(
            0, 0, self.viewer_width, self.note_height)
        f_note_bar.hoverMoveEvent = self.hover_restore_cursor_event
        f_note_bar.setBrush(f_base_brush)
        self.scene.addItem(f_note_bar)
        f_note_bar.setPos(
            self.piano_width + self.padding, PIANO_ROLL_HEADER_HEIGHT)
        for i in range(self.end_octave - self.start_octave,
                       self.start_octave - self.start_octave, -1):
            for j in range(self.notes_in_octave, 0, -1):
                f_note_bar = QGraphicsRectItem(
                    0, 0, self.viewer_width, self.note_height)
                f_note_bar.setZValue(60.0)
                self.scene.addItem(f_note_bar)
                f_note_bar.setBrush(f_octave_brushes[f_current_key])
                f_current_key += 1
                if f_current_key >= len(f_octave_brushes):
                    f_current_key = 0
                f_note_bar_y = (self.note_height * j) + (self.octave_height *
                    (i - 1)) + PIANO_ROLL_HEADER_HEIGHT
                f_note_bar.setPos(
                    self.piano_width + self.padding, f_note_bar_y)
        f_beat_pen = QPen()
        f_beat_pen.setWidth(2)
        f_line_pen = QPen(QColor(0, 0, 0))
        self.total_height = \
            self.piano_height + PIANO_ROLL_HEADER_HEIGHT + self.note_height
        for i in range(0, int(shared.CURRENT_ITEM_LEN) + 1):
            f_beat_x = (self.px_per_beat * i) + self.piano_width
            f_beat = self.scene.addLine(
                f_beat_x, 0, f_beat_x, self.total_height)
            f_beat_number = i
            f_beat.setPen(f_beat_pen)
            if i < shared.CURRENT_ITEM_LEN:
                f_number = QGraphicsSimpleTextItem(
                    str(f_beat_number + 1), self.header)
                f_number.setFlag(
                    QGraphicsItem.ItemIgnoresTransformations)
                f_number.setPos((self.px_per_beat * i), 24)
                f_number.setBrush(QtCore.Qt.white)
                for j in range(0, self.grid_div):
                    f_x = (self.px_per_beat * i) + (self.value_width *
                        j) + self.piano_width
                    f_line = self.scene.addLine(
                        f_x, PIANO_ROLL_HEADER_HEIGHT, f_x, self.total_height)
                    if float(j) != self.grid_div * 0.5:
                        f_line.setPen(f_line_pen)

    def default_vposition(self):
        scrollbar = self.verticalScrollBar()
        new_val = int(self.piano_height * 0.5)
        scrollbar.setSliderPosition(new_val)

    def resizeEvent(self, a_event):
        QGraphicsView.resizeEvent(self, a_event)
        shared.ITEM_EDITOR.tab_changed()

    def clear_drawn_items(self):
        self.note_items = []
        self.scene.clear()
        self.update_note_height()
        self.draw_header()
        self.draw_piano()
        self.draw_grid()
        self.set_header_and_keys()

    def draw_item(self):
        self.has_selected = False #Reset the selected-ness state...
        self.viewer_width = shared.PIANO_ROLL_GRID_WIDTH
        self.setSceneRect(
            0.0, 0.0, self.viewer_width + 200.0,
            self.piano_height + PIANO_ROLL_HEADER_HEIGHT + 24.0)
        shared.PIANO_ROLL_GRID_MAX_START_TIME = (shared.PIANO_ROLL_GRID_WIDTH -
            1.0) + shared.PIANO_KEYS_WIDTH
        self.setUpdatesEnabled(False)
        self.clear_drawn_items()
        if shared.CURRENT_ITEM:
            for f_note in shared.CURRENT_ITEM.notes:
                f_note_item = self.draw_note(f_note)
                f_note_item.resize_last_mouse_pos = \
                    f_note_item.scenePos().x()
                f_note_item.resize_pos = f_note_item.scenePos()
                if f_note_item.get_selected_string() in \
                self.selected_note_strings:
                    f_note_item.setSelected(True)
            if shared.DRAW_LAST_ITEMS and shared.LAST_ITEM:
                f_offset = (
                    shared.LAST_ITEM_REF.start_offset
                    -
                    shared.ITEM_REF_POS[0]
                )
                for f_note in shared.LAST_ITEM.notes:
                    f_note_item = self.draw_note(
                        f_note, False, a_offset=f_offset)
            self.scrollContentsBy(0, 0)
#            f_text = QGraphicsSimpleTextItem(f_name, self.header)
#            f_text.setFlag(QGraphicsItem.ItemIgnoresTransformations)
#            f_text.setBrush(QtCore.Qt.yellow)
#            f_text.setPos((f_i * shared.PIANO_ROLL_GRID_WIDTH), 2.0)
        self.setUpdatesEnabled(True)
        self.update()

    def draw_note(self, a_note, a_enabled=True, a_offset=0.0):
        """ a_note is an instance of the mk_project.pydaw_note class"""
        f_start = (self.piano_width + self.padding +
            self.px_per_beat * (a_note.start - a_offset))
        f_length = self.px_per_beat * a_note.length
        f_note = PIANO_ROLL_HEADER_HEIGHT + self.note_height * \
            (shared.PIANO_ROLL_NOTE_COUNT - a_note.note_num)
        f_note_item = PianoRollNoteItem(
            f_length, self.note_height, a_note.note_num,
            a_note, a_enabled)
        f_note_item.setPos(f_start, f_note)
        self.scene.addItem(f_note_item)
        if a_enabled:
            self.note_items.append(f_note_item)
            return f_note_item

    def set_vel_rand(self, a_rand, a_emphasis):
        self.vel_rand = int(a_rand)
        self.vel_emphasis = int(a_emphasis)

    def get_vel(self, a_beat):
        if self.vel_rand == 0:
            return 100
        f_emph = self.get_beat_emphasis(a_beat)
        if self.vel_rand == 1:
            return random.randint(75 - f_emph, 100 - f_emph)
        elif self.vel_rand == 2:
            return random.randint(75 - f_emph, 100 - f_emph)
        else:
            assert False, "Invalid velocity randomization value"

    def get_beat_emphasis(self, a_beat, a_amt=25.0):
        if self.vel_emphasis == 0:
            return 0
        f_beat = a_beat
        if self.vel_emphasis == 2:
            f_beat += 0.5
        f_beat = f_beat % 1.0
        if f_beat > 0.5:
            f_beat = 0.5 - (f_beat - 0.5)
            f_beat = 0.5 - f_beat
        return int(f_beat * 2.0 * a_amt)


class PianoRollEditorWidget:
    """ This is the parent widget that contains the PianoRollEditor """
    def __init__(self):
        self.widget = QWidget()
        self.vlayout = QVBoxLayout()
        self.widget.setLayout(self.vlayout)

        self.controls_grid_layout = QGridLayout()
        self.scale_key_combobox = QComboBox()
        self.scale_key_combobox.setMinimumWidth(60)
        self.scale_key_combobox.addItems(PIANO_ROLL_NOTE_LABELS)
        self.scale_key_combobox.currentIndexChanged.connect(
            self.reload_handler)
        self.controls_grid_layout.addWidget(QLabel("Key:"), 0, 3)
        self.controls_grid_layout.addWidget(self.scale_key_combobox, 0, 4)
        self.scale_combobox = QComboBox()
        self.scale_combobox.setMinimumWidth(172)
        self.scale_combobox.addItems(scales.SCALE_NAMES)
        self.scale_combobox.currentIndexChanged.connect(self.reload_handler)
        self.controls_grid_layout.addWidget(QLabel(_("Scale:")), 0, 5)
        self.controls_grid_layout.addWidget(self.scale_combobox, 0, 6)

        self.controls_grid_layout.addWidget(QLabel("V"), 0, 45)
        self.vzoom_slider = QSlider(QtCore.Qt.Horizontal)
        self.controls_grid_layout.addWidget(self.vzoom_slider, 0, 46)
        self.vzoom_slider.setObjectName("zoom_slider")
        self.vzoom_slider.setMaximumWidth(72)
        self.vzoom_slider.setRange(9, 24)
        self.vzoom_slider.setValue(shared.PIANO_ROLL_NOTE_HEIGHT)
        self.vzoom_slider.valueChanged.connect(self.set_midi_vzoom)
        self.vzoom_slider.sliderReleased.connect(self.save_vzoom)

        self.controls_grid_layout.addItem(
            QSpacerItem(10, 10, QSizePolicy.Expanding), 0, 30)

        self.edit_menu_button = QPushButton(_("Menu"))
        self.edit_menu_button.setFixedWidth(60)
        self.edit_menu = QMenu(self.widget)
        self.edit_menu_button.setMenu(self.edit_menu)
        self.controls_grid_layout.addWidget(self.edit_menu_button, 0, 30)

        self.edit_actions_menu = self.edit_menu.addMenu(_("Edit"))

        self.copy_action = self.edit_actions_menu.addAction(_("Copy"))
        self.copy_action.triggered.connect(
            shared.PIANO_ROLL_EDITOR.copy_selected,
        )
        self.copy_action.setShortcut(QKeySequence.Copy)

        self.cut_action = self.edit_actions_menu.addAction(_("Cut"))
        self.cut_action.triggered.connect(self.on_cut)
        self.cut_action.setShortcut(QKeySequence.Cut)

        self.paste_action = self.edit_actions_menu.addAction(_("Paste"))
        self.paste_action.triggered.connect(shared.PIANO_ROLL_EDITOR.paste)
        self.paste_action.setShortcut(QKeySequence.Paste)

        self.select_all_action = self.edit_actions_menu.addAction(
            _("Select All"))
        self.select_all_action.triggered.connect(self.select_all)
        self.select_all_action.setShortcut(QKeySequence.SelectAll)

        self.clear_selection_action = self.edit_actions_menu.addAction(
            _("Clear Selection")
        )
        self.clear_selection_action.triggered.connect(
            shared.PIANO_ROLL_EDITOR.scene.clearSelection,
        )
        self.clear_selection_action.setShortcut(
            QKeySequence.fromString("Esc")
        )

        self.edit_actions_menu.addSeparator()

        self.delete_selected_action = self.edit_actions_menu.addAction(
            _("Delete"),
        )
        self.delete_selected_action.triggered.connect(self.on_delete_selected)
        self.delete_selected_action.setShortcut(QKeySequence.Delete)

        self.quantize_action = self.edit_menu.addAction(_("Quantize..."))
        self.quantize_action.triggered.connect(self.quantize_dialog)

        self.transpose_menu = self.edit_menu.addMenu(_("Transpose"))

        self.transpose_action = self.transpose_menu.addAction(_("Dialog..."))
        self.transpose_action.triggered.connect(self.transpose_dialog)

        self.transpose_menu.addSeparator()

        self.up_semitone_action = self.transpose_menu.addAction(
            _("Up Semitone"))
        self.up_semitone_action.triggered.connect(self.transpose_up_semitone)
        self.up_semitone_action.setShortcut(
            QKeySequence.fromString("SHIFT+UP"))

        self.down_semitone_action = self.transpose_menu.addAction(
            _("Down Semitone"),
        )
        self.down_semitone_action.triggered.connect(
            self.transpose_down_semitone,
        )
        self.down_semitone_action.setShortcut(
            QKeySequence.fromString("SHIFT+DOWN"),
        )

        self.up_octave_action = self.transpose_menu.addAction(_("Up Octave"))
        self.up_octave_action.triggered.connect(self.transpose_up_octave)
        self.up_octave_action.setShortcut(
            QKeySequence.fromString("ALT+UP"),
        )

        self.down_octave_action = self.transpose_menu.addAction(
            _("Down Octave"),
        )
        self.down_octave_action.triggered.connect(self.transpose_down_octave)
        self.down_octave_action.setShortcut(
            QKeySequence.fromString("ALT+DOWN"))

        self.velocity_menu = self.edit_menu.addMenu(_("Velocity"))

        self.velocity_menu.addSeparator()

        self.vel_random_index = 0
        self.velocity_random_menu = self.velocity_menu.addMenu(_("Randomness"))
        self.random_types = [_("None"), _("Tight"), _("Loose")]
        self.vel_rand_action_group = QActionGroup(
            self.velocity_random_menu)
        self.velocity_random_menu.triggered.connect(self.vel_rand_triggered)

        for f_i, f_type in zip(
        range(len(self.random_types)), self.random_types):
            f_action = self.velocity_random_menu.addAction(f_type)
            f_action.setActionGroup(self.vel_rand_action_group)
            f_action.setCheckable(True)
            f_action.my_index = f_i
            if f_i == 0:
                f_action.setChecked(True)

        self.vel_emphasis_index = 0
        self.velocity_emphasis_menu = self.velocity_menu.addMenu(_("Emphasis"))
        self.emphasis_types = [_("None"), _("On-beat"), _("Off-beat")]
        self.vel_emphasis_action_group = QActionGroup(
            self.velocity_random_menu)
        self.velocity_emphasis_menu.triggered.connect(
            self.vel_emphasis_triggered)

        for f_i, f_type in zip(
        range(len(self.emphasis_types)), self.emphasis_types):
            f_action = self.velocity_emphasis_menu.addAction(f_type)
            f_action.setActionGroup(self.vel_emphasis_action_group)
            f_action.setCheckable(True)
            f_action.my_index = f_i
            if f_i == 0:
                f_action.setChecked(True)

        self.edit_menu.addSeparator()

        self.glue_selected_action = self.edit_menu.addAction(
            _("Glue Selected"))
        self.glue_selected_action.triggered.connect(
            shared.PIANO_ROLL_EDITOR.glue_selected)
        self.glue_selected_action.setShortcut(
            QKeySequence.fromString("CTRL+G"))

        self.half_selected_action = self.edit_menu.addAction(
            _("Split Selected in Half"))
        self.half_selected_action.triggered.connect(
            shared.PIANO_ROLL_EDITOR.half_selected)
        self.half_selected_action.setShortcut(
            QKeySequence.fromString("CTRL+H"))


        self.edit_menu.addSeparator()

        self.draw_last_action = self.edit_menu.addAction(
            _("Draw Last Item(s)"))
        self.draw_last_action.triggered.connect(self.draw_last)
        self.draw_last_action.setCheckable(True)
        self.draw_last_action.setShortcut(
            QKeySequence.fromString("CTRL+F"))

        self.open_last_action = self.edit_menu.addAction(
            _("Open Last Item(s)"))
        self.open_last_action.triggered.connect(self.open_last)
        self.open_last_action.setShortcut(
            QKeySequence.fromString("ALT+F"))

        self.controls_grid_layout.addItem(
            QSpacerItem(10, 10, QSizePolicy.Expanding), 0, 31)

        self.vlayout.addLayout(self.controls_grid_layout)
        self.vlayout.addWidget(shared.PIANO_ROLL_EDITOR)

    def set_midi_vzoom(self, a_val):
        shared.PIANO_ROLL_NOTE_HEIGHT = a_val
        shared.PIANO_ROLL_EDITOR.draw_item()

    def save_vzoom(self):
        pydaw_util.set_file_setting("PIANO_VZOOM", self.vzoom_slider.value())

    def quantize_dialog(self):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return
        shared.ITEM_EDITOR.quantize_dialog(shared.PIANO_ROLL_EDITOR.has_selected)

    def transpose_dialog(self):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return
        shared.ITEM_EDITOR.transpose_dialog(shared.PIANO_ROLL_EDITOR.has_selected)

    def select_all(self):
        if not shared.ITEM_EDITOR.enabled:
            shared.ITEM_EDITOR.show_not_enabled_warning()
            return
        for f_note in shared.PIANO_ROLL_EDITOR.note_items:
            f_note.setSelected(True)

    def open_last(self):
        if shared.LAST_ITEM_NAME:
            global_open_items(shared.LAST_ITEM_NAME, a_new_ref=shared.LAST_ITEM_REF)
            shared.PIANO_ROLL_EDITOR.draw_item()

    def draw_last(self):
        shared.DRAW_LAST_ITEMS = not shared.DRAW_LAST_ITEMS
        self.draw_last_action.setChecked(shared.DRAW_LAST_ITEMS)
        shared.PIANO_ROLL_EDITOR.draw_item()
        #global_open_items()

    def vel_rand_triggered(self, a_action):
        self.vel_random_index = a_action.my_index
        self.set_vel_rand()

    def vel_emphasis_triggered(self, a_action):
        self.vel_emphasis_index = a_action.my_index
        self.set_vel_rand()

    def transpose_up_semitone(self):
        shared.PIANO_ROLL_EDITOR.transpose_selected(1)

    def transpose_down_semitone(self):
        shared.PIANO_ROLL_EDITOR.transpose_selected(-1)

    def transpose_up_octave(self):
        shared.PIANO_ROLL_EDITOR.transpose_selected(12)

    def transpose_down_octave(self):
        shared.PIANO_ROLL_EDITOR.transpose_selected(-12)

    def set_vel_rand(self, a_val=None):
        shared.PIANO_ROLL_EDITOR.set_vel_rand(
            self.vel_random_index, self.vel_emphasis_index)

    def on_delete_selected(self):
        shared.PIANO_ROLL_EDITOR.delete_selected()

    def on_cut(self):
        if shared.PIANO_ROLL_EDITOR.copy_selected():
            self.on_delete_selected()

    def reload_handler(self, a_val=None):
        shared.PROJECT.set_midi_scale(
            self.scale_key_combobox.currentIndex(),
            self.scale_combobox.currentIndex())
        if shared.CURRENT_ITEM:
            shared.PIANO_ROLL_EDITOR.set_selected_strings()
            global_open_items()
            shared.PIANO_ROLL_EDITOR.draw_item()
        else:
            shared.PIANO_ROLL_EDITOR.clear_drawn_items()

