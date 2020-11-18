from mkpy import glbl
from mkpy.libpydaw import pydaw_util
from mkpy.libpydaw.translate import _
from mkpy.mkqt import *
import os


# This is for plugins to consume, it's not a default value anywhere
DEFAULT_KNOB_SIZE = 48
KNOB_ARC_PEN = QPen(QtCore.Qt.white, 5.0)
KNOB_BACKGROUND_PEN = QPen(QColor.fromRgb(90, 90, 90, 255), 5.0)

CC_CLIPBOARD = None

class PixmapKnobCache:
    def __init__(self, a_path):
        self.cache = {}
        self.path = a_path
        self.knob_pixmap = None
        self.first_load = True

    def get_scaled_pixmap_knob(self, a_size):
        # hack to get around creating a QApplication first
        if self.first_load:
            self.first_load = False
            if os.path.exists(self.path):
                self.knob_pixmap = QPixmap(self.path)
            else:
                print("ERROR:  '{}' does not exist, you may be using "
                    "an old-style theme, try loading the default "
                    "theme".format(self.path))
        if not self.knob_pixmap:
            return None
        if a_size not in self.cache:
            self.cache[a_size] = self.knob_pixmap.scaled(
                a_size, a_size,
                QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        return self.cache[a_size]

DEFAULT_KNOB_FG_PIXMAP_CACHE = PixmapKnobCache(
    os.path.join(pydaw_util.STYLESHEET_DIR, "knob-fg.png"))
DEFAULT_KNOB_BG_PIXMAP_CACHE = PixmapKnobCache(
    os.path.join(pydaw_util.STYLESHEET_DIR, "knob-bg.png"))

class pydaw_pixmap_knob(QDial):
    def __init__(
        self,
        a_size,
        a_min_val,
        a_max_val,
        a_pixmap_fg_cache=DEFAULT_KNOB_FG_PIXMAP_CACHE,
        a_pixmap_bg_cache=DEFAULT_KNOB_BG_PIXMAP_CACHE,
    ):
        QDial.__init__(self)
        self.pixmap_fg_cache = a_pixmap_fg_cache
        self.pixmap_bg_cache = a_pixmap_bg_cache
        self.setRange(a_min_val, a_max_val)
        self.val_step = float(a_max_val - a_min_val) * 0.005  # / 200.0
        self.val_step_small = self.val_step * 0.1
        self.setGeometry(0, 0, a_size, a_size)
        self.pixmap_size = a_size - 12
        self.pixmap_fg = self.pixmap_fg_cache.get_scaled_pixmap_knob(
            self.pixmap_size)
        self.pixmap_bg = self.pixmap_bg_cache.get_scaled_pixmap_knob(
            self.pixmap_size)
        self.setFixedSize(a_size, a_size)

    def keyPressEvent(self, a_event):
        QDial.keyPressEvent(self, a_event)
        if a_event.key() == QtCore.Qt.Key_Space:
            glbl.TRANSPORT.on_spacebar()

    def paintEvent(self, a_event):
        p = QPainter(self)
        p.setRenderHints(
            QPainter.HighQualityAntialiasing |
            QPainter.SmoothPixmapTransform)
        f_frac_val = ((float(self.value() - self.minimum())) /
            (float(self.maximum() - self.minimum())))
        f_rotate_value = f_frac_val * 270.0
        f_rect = self.rect()
        f_rect.setWidth(f_rect.width() - 5)
        f_rect.setHeight(f_rect.height() - 5)
        f_rect.setX(f_rect.x() + 5)
        f_rect.setY(f_rect.y() + 5)
        p.setPen(KNOB_BACKGROUND_PEN)
        p.drawArc(f_rect, -136 * 16, 136 * 2 * -16)
        p.setPen(KNOB_ARC_PEN)
        p.drawArc(f_rect, -136 * 16, (f_rotate_value + 1.0) * -16)

        if self.pixmap_bg:
            p.drawPixmap(6, 6, self.pixmap_bg)

        if self.pixmap_fg:
            # xc and yc are the center of the widget's rect.
            xc = self.width() * 0.5
            yc = self.height() * 0.5
            # translates the coordinate system by xc and yc
            p.translate(xc, yc)
            p.rotate(f_rotate_value)
            # we need to move the rectangle that we draw by
            # rx and ry so it's in the center.
            rx = -(self.pixmap_size * 0.5)
            ry = -(self.pixmap_size * 0.5)
            p.drawPixmap(rx, ry, self.pixmap_fg)


    def mousePressEvent(self, a_event):
        self.mouse_pos = QCursor.pos()
        if a_event.button() == QtCore.Qt.RightButton:
            QDial.mousePressEvent(self, a_event)
            return
        f_pos = a_event.pos()
        self.orig_x = f_pos.x()
        self.orig_y = f_pos.y()
        self.orig_value = self.value()
        self.fine_only = (a_event.modifiers() == QtCore.Qt.ControlModifier)
        QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)

    def mouseMoveEvent(self, a_event):
        f_pos = a_event.pos()
        f_x = f_pos.x()
        f_diff_x = f_x - self.orig_x
        if self.fine_only:
            f_val = (f_diff_x * self.val_step_small) + self.orig_value
        else:
            f_y = f_pos.y()
            f_diff_y = self.orig_y - f_y
            f_val = ((f_diff_y * self.val_step) +
                (f_diff_x * self.val_step_small)) + self.orig_value
        f_val = pydaw_util.pydaw_clip_value(
            f_val, self.minimum(), self.maximum())
        f_val = int(f_val)
        if f_val != self.value():
            self.setValue(f_val)
            self.valueChanged.emit(f_val)

    def mouseReleaseEvent(self, a_event):
        QCursor.setPos(self.mouse_pos)
        QApplication.restoreOverrideCursor()
        self.sliderReleased.emit()

