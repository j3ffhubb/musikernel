from sgui.lib.translate import _
from sgui.sgqt import *

NOTE_SELECTOR_CLIPBOARD = None

class note_selector_widget:
    def __init__(
        self,
        a_port_num,
        a_rel_callback,
        a_val_callback,
        a_port_dict=None,
        a_default_value=None,
        a_preset_mgr=None,
    ):
        self.control = self
        self.port_num = a_port_num
        self.rel_callback = a_rel_callback
        self.val_callback = a_val_callback
        self.note_combobox = QComboBox()
        self.note_combobox.wheelEvent = self.wheel_event
        self.note_combobox.setMinimumWidth(60)
        self.note_combobox.addItems(
            ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        )
        self.note_combobox.contextMenuEvent = self.context_menu_event
        self.octave_spinbox = QSpinBox()
        self.octave_spinbox.setRange(-2, 8)
        self.octave_spinbox.setValue(3)
        self.octave_spinbox.contextMenuEvent = self.context_menu_event
        self.widget = QWidget()
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.widget.setLayout(self.layout)
        self.layout.addWidget(self.note_combobox)
        self.layout.addWidget(self.octave_spinbox)
        self.note_combobox.currentIndexChanged.connect(
            self.control_value_changed)
        self.octave_spinbox.valueChanged.connect(self.control_value_changed)
        self.suppress_changes = False
        if a_port_dict is not None:
            a_port_dict[self.port_num] = self
        self.name_label = None
        self.value_label = None
        self.default_value = a_default_value
        if a_default_value is not None:
            self.selected_note = a_default_value
            self.set_value(a_default_value)
        else:
            self.selected_note = 60
        if a_preset_mgr is not None:
            a_preset_mgr.add_control(self)

    def context_menu_event(self, a_event=None):
        f_menu = QMenu(self.widget)
        f_copy_action = f_menu.addAction(_("Copy"))
        f_copy_action.triggered.connect(self.copy_to_clipboard)
        f_paste_action = f_menu.addAction(_("Paste"))
        f_paste_action.triggered.connect(self.paste_from_clipboard)
        f_menu.exec_(QCursor.pos())

    def copy_to_clipboard(self):
        global NOTE_SELECTOR_CLIPBOARD
        NOTE_SELECTOR_CLIPBOARD = self.get_value()

    def paste_from_clipboard(self):
        if NOTE_SELECTOR_CLIPBOARD is not None:
            self.set_value(NOTE_SELECTOR_CLIPBOARD, True)

    def wheel_event(self, a_event=None):
        pass

    def control_value_changed(self, a_val=None):
        self.selected_note = (
            self.note_combobox.currentIndex()
        ) + ((self.octave_spinbox.value() + 2) * 12)
        if not self.suppress_changes:
            if self.val_callback is not None:
                self.val_callback(self.port_num, self.selected_note)
            if self.rel_callback is not None:
                self.rel_callback(self.port_num, self.selected_note)

    def set_value(self, a_val, a_changed=False):
        self.suppress_changes = True
        self.note_combobox.setCurrentIndex(a_val % 12)
        self.octave_spinbox.setValue((int(float(a_val) / 12.0)) - 2)
        self.suppress_changes = False
        if a_changed:
            self.control_value_changed(a_val)

    def get_value(self):
        return self.selected_note

    def reset_default_value(self):
        if self.default_value is not None:
            self.set_value(self.default_value, True)

    def add_to_grid_layout(self, a_layout, a_x):
        if self.name_label is not None:
            a_layout.addWidget(
                self.name_label,
                0,
                a_x,
                alignment=QtCore.Qt.AlignHCenter,
            )
        a_layout.addWidget(
            self.widget,
            1,
            a_x,
            alignment=QtCore.Qt.AlignHCenter,
        )
        if self.value_label is not None:
            a_layout.addWidget(
                self.value_label,
                2,
                a_x,
                alignment=QtCore.Qt.AlignHCenter,
            )

