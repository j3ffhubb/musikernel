from .abstract import AbstractItemEditor
from .automation import AutomationEditorWidget
from sgui import glbl
from sgui.daw import shared
from sgui.daw.shared import *
from sgui.lib import util
from sgui.lib.util import *
from sgui.lib.translate import _
from sgui.sgqt import *


class ItemListViewer:
    """ This is the "Items" tab in MainWindow
    """
    def __init__(self):
        self.enabled = False
        self.events_follow_default = True

        self.widget = QWidget()
        self.master_vlayout = QVBoxLayout()
        self.widget.setLayout(self.master_vlayout)

        self.tab_widget = QTabWidget()

        shared.AUDIO_SEQ_WIDGET.hsplitter.insertWidget(0, shared.AUDIO_SEQ_WIDGET.widget)
        self.tab_widget.addTab(shared.AUDIO_SEQ_WIDGET.hsplitter, _("Audio"))

        self.piano_roll_tab = QWidget()
        self.tab_widget.addTab(self.piano_roll_tab, _("Piano Roll"))
        self.notes_tab = QWidget()
        self.cc_tab = QWidget()
        self.tab_widget.addTab(self.cc_tab, _("CC"))

        self.pitchbend_tab = QWidget()
        self.tab_widget.addTab(self.pitchbend_tab, _("Pitchbend"))

        self.editing_hboxlayout = QHBoxLayout()
        self.master_vlayout.addWidget(self.tab_widget)

        self.notes_groupbox = QGroupBox(_("Notes"))
        self.notes_vlayout = QVBoxLayout(self.notes_groupbox)

        self.cc_vlayout = QVBoxLayout()
        self.cc_tab.setLayout(self.cc_vlayout)

        self.notes_table_widget = QTableWidget()
        self.notes_table_widget.setVerticalScrollMode(
            QAbstractItemView.ScrollPerPixel)
        self.notes_table_widget.setColumnCount(5)
        self.notes_table_widget.setSortingEnabled(True)
        self.notes_table_widget.sortItems(0)
        self.notes_table_widget.setEditTriggers(
            QAbstractItemView.NoEditTriggers)
        self.notes_table_widget.setSelectionBehavior(
            QAbstractItemView.SelectRows)
        self.notes_vlayout.addWidget(self.notes_table_widget)
        self.notes_table_widget.resizeColumnsToContents()

        self.notes_hlayout = QHBoxLayout()
        self.list_tab_vlayout = QVBoxLayout()
        self.notes_tab.setLayout(self.list_tab_vlayout)
        self.list_tab_vlayout.addLayout(self.editing_hboxlayout)
        self.list_tab_vlayout.addLayout(self.notes_hlayout)
        self.notes_hlayout.addWidget(self.notes_groupbox)

        self.piano_roll_hlayout = QHBoxLayout(self.piano_roll_tab)
        self.piano_roll_hlayout.setContentsMargins(2, 2, 2, 2)
        self.piano_roll_hlayout.addWidget(
            shared.PIANO_ROLL_EDITOR_WIDGET.widget,
        )

        self.ccs_groupbox = QGroupBox(_("CCs"))
        self.ccs_vlayout = QVBoxLayout(self.ccs_groupbox)

        self.ccs_table_widget = QTableWidget()
        self.ccs_table_widget.setVerticalScrollMode(
            QAbstractItemView.ScrollPerPixel)
        self.ccs_table_widget.setColumnCount(3)
        self.ccs_table_widget.setSortingEnabled(True)
        self.ccs_table_widget.sortItems(0)
        self.ccs_table_widget.setEditTriggers(
            QAbstractItemView.NoEditTriggers)
        self.ccs_table_widget.setSelectionBehavior(
            QAbstractItemView.SelectRows)
        self.ccs_table_widget.resizeColumnsToContents()
        self.ccs_vlayout.addWidget(self.ccs_table_widget)
        self.notes_hlayout.addWidget(self.ccs_groupbox)

        self.cc_vlayout.addWidget(shared.CC_EDITOR_WIDGET.widget)

        self.pb_hlayout = QHBoxLayout()
        self.pitchbend_tab.setLayout(self.pb_hlayout)
        self.pb_groupbox = QGroupBox(_("Pitchbend"))
        self.pb_groupbox.setFixedWidth(240)
        self.pb_vlayout = QVBoxLayout(self.pb_groupbox)

        self.pitchbend_table_widget = QTableWidget()
        self.pitchbend_table_widget.setVerticalScrollMode(
            QAbstractItemView.ScrollPerPixel)
        self.pitchbend_table_widget.setColumnCount(2)
        self.pitchbend_table_widget.setSortingEnabled(True)
        self.pitchbend_table_widget.sortItems(0)
        self.pitchbend_table_widget.setEditTriggers(
            QAbstractItemView.NoEditTriggers)
        self.pitchbend_table_widget.setSelectionBehavior(
            QAbstractItemView.SelectRows)
        self.pitchbend_table_widget.resizeColumnsToContents()
        self.pb_vlayout.addWidget(self.pitchbend_table_widget)
        self.notes_hlayout.addWidget(self.pb_groupbox)
        self.pb_auto_vlayout = QVBoxLayout()
        self.pb_hlayout.addLayout(self.pb_auto_vlayout)
        self.pb_viewer_widget = AutomationEditorWidget(shared.PB_EDITOR, False)
        self.pb_auto_vlayout.addWidget(self.pb_viewer_widget.widget)

        self.tab_widget.addTab(self.notes_tab, _("List Viewers"))

        self.zoom_widget = QWidget()
        #self.zoom_widget.setContentsMargins(0, 0, 2, 0)
        self.zoom_hlayout = QHBoxLayout(self.zoom_widget)
        self.zoom_hlayout.setContentsMargins(2, 0, 2, 0)
        #self.zoom_hlayout.setSpacing(0)

        self.snap_combobox = QComboBox()
        self.snap_combobox.setMinimumWidth(90)
        self.snap_combobox.addItems(
            [_("None"), "1/4", "1/8", "1/12", "1/16",
            "1/32", "1/64", "1/128"])
        self.zoom_hlayout.addWidget(QLabel(_("Snap:")))
        self.zoom_hlayout.addWidget(self.snap_combobox)
        self.snap_combobox.currentIndexChanged.connect(self.set_snap)

        self.item_name_lineedit = QLineEdit()
        self.item_name_lineedit.setReadOnly(True)
        self.item_name_lineedit.editingFinished.connect(self.on_item_rename)
        self.item_name_lineedit.setMinimumWidth(150)
        self.zoom_hlayout.addWidget(self.item_name_lineedit)

        self.zoom_hlayout.addWidget(QLabel("H"))
        self.zoom_slider = QSlider(QtCore.Qt.Horizontal)
        self.zoom_hlayout.addWidget(self.zoom_slider)
        self.zoom_slider.setObjectName("zoom_slider")
        self.zoom_slider.setRange(10, 100)
        self.zoom_slider.valueChanged.connect(self.set_midi_zoom)
        self.tab_widget.setCornerWidget(self.zoom_widget)
        self.tab_widget.currentChanged.connect(self.tab_changed)

        self.set_headers()
        self.default_note_start = 0.0
        self.default_note_length = 1.0
        self.default_note_note = 0
        self.default_note_octave = 3
        self.default_note_velocity = 100
        self.default_cc_num = 0
        self.default_cc_start = 0.0
        self.default_cc_val = 0
        self.default_quantize = 5
        self.default_pb_start = 0
        self.default_pb_val = 0
        self.default_pb_quantize = 0

    def on_item_rename(self, a_val=None):
        name = str(self.item_name_lineedit.text()).strip()
        shared.PROJECT.rename_items([shared.CURRENT_ITEM_NAME], name)
        shared.PROJECT.commit(_("Rename items"))
        items_dict = shared.PROJECT.get_items_dict()
        name = items_dict.get_name_by_uid(shared.CURRENT_ITEM.uid)
        self.item_name_lineedit.setText(name)

    def set_snap(self, a_val=None):
        f_index = self.snap_combobox.currentIndex()
        set_piano_roll_quantize(f_index)
        set_audio_snap(f_index)
        if shared.CURRENT_ITEM:
            shared.PIANO_ROLL_EDITOR.set_selected_strings()
            global_open_items()
            self.tab_changed()
        else:
            shared.PIANO_ROLL_EDITOR.clear_drawn_items()

    def clear_new(self):
        self.enabled = False
        self.ccs_table_widget.clearContents()
        self.notes_table_widget.clearContents()
        self.pitchbend_table_widget.clearContents()
        shared.PIANO_ROLL_EDITOR.clear_drawn_items()
        self.item = None

    def quantize_dialog(self, a_selected_only=False):
        if not self.enabled:
            self.show_not_enabled_warning()
            return

        def quantize_ok_handler():
            f_quantize_text = f_quantize_combobox.currentText()
            self.events_follow_default = f_events_follow_notes.isChecked()
            f_clip = shared.CURRENT_ITEM.quantize(f_quantize_text,
                f_events_follow_notes.isChecked(),
                a_selected_only=f_selected_only.isChecked())
            shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)

            if f_selected_only.isChecked():
                shared.PIANO_ROLL_EDITOR.selected_note_strings = f_clip
            else:
                shared.PIANO_ROLL_EDITOR.selected_note_strings = []

            global_open_items()
            shared.PIANO_ROLL_EDITOR.draw_item()
            shared.PROJECT.commit(_("Quantize item(s)"))
            f_window.close()

        def quantize_cancel_handler():
            f_window.close()

        f_window = QDialog(shared.MAIN_WINDOW)
        f_window.setWindowTitle(_("Quantize"))
        f_layout = QGridLayout()
        f_window.setLayout(f_layout)

        f_layout.addWidget(QLabel(_("Quantize")), 0, 0)
        f_quantize_combobox = QComboBox()
        f_quantize_combobox.addItems(bar_fracs)
        f_layout.addWidget(f_quantize_combobox, 0, 1)
        f_events_follow_notes = QCheckBox(
            _("CCs and pitchbend follow notes?"))
        f_events_follow_notes.setChecked(self.events_follow_default)
        f_layout.addWidget(f_events_follow_notes, 1, 1)
        f_ok = QPushButton(_("OK"))
        f_ok.pressed.connect(quantize_ok_handler)
        f_ok_cancel_layout = QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok)

        f_selected_only = QCheckBox(_("Selected Notes Only?"))
        f_selected_only.setChecked(a_selected_only)
        f_layout.addWidget(f_selected_only, 2, 1)

        f_layout.addLayout(f_ok_cancel_layout, 3, 1)
        f_cancel = QPushButton(_("Cancel"))
        f_cancel.pressed.connect(quantize_cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec_()

    def transpose_dialog(self, a_selected_only=False):
        if not self.enabled:
            self.show_not_enabled_warning()
            return

        def transpose_ok_handler():
            f_clip = shared.CURRENT_ITEM.transpose(
                f_semitone.value(), f_octave.value(),
                a_selected_only=f_selected_only.isChecked(),
                a_duplicate=f_duplicate_notes.isChecked())
            shared.PROJECT.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)

            if f_selected_only.isChecked():
                shared.PIANO_ROLL_EDITOR.selected_note_strings = f_clip
            else:
                shared.PIANO_ROLL_EDITOR.selected_note_strings = []

            global_open_items()
            shared.PIANO_ROLL_EDITOR.draw_item()
            shared.PROJECT.commit(_("Transpose item(s)"))
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
            _("Checking this box causes the transposed notes "
            "to be added rather than moving the existing notes."))
        f_layout.addWidget(f_duplicate_notes, 2, 1)
        f_selected_only = QCheckBox(_("Selected Notes Only?"))
        f_selected_only.setChecked(a_selected_only)
        f_layout.addWidget(f_selected_only, 4, 1)
        f_ok_cancel_layout = QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout, 6, 1)
        f_ok = QPushButton(_("OK"))
        f_ok.pressed.connect(transpose_ok_handler)
        f_ok_cancel_layout.addWidget(f_ok)
        f_cancel = QPushButton(_("Cancel"))
        f_cancel.pressed.connect(transpose_cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec_()

    def tab_changed(self, a_val=None):
        f_list = [
            shared.AUDIO_SEQ,
            shared.PIANO_ROLL_EDITOR,
            shared.CC_EDITOR,
            shared.PB_EDITOR,
        ]
        f_index = self.tab_widget.currentIndex()
        if f_index == 0:
            global_open_audio_items()
        else:
            if f_index == 1:
                set_piano_roll_quantize()
            elif f_index == 4:
                shared.ITEM_EDITOR.open_item_list()
            if f_index < len(f_list):
                f_list[f_index].draw_item()
            shared.PIANO_ROLL_EDITOR.click_enabled = True
            #^^^^huh?

    def show_not_enabled_warning(self):
        QMessageBox.warning(
            shared.MAIN_WINDOW, _("Error"),
           _("You must open an item first by double-clicking on one in "
           "the region editor on the 'Song/Region' tab."))

    def set_midi_zoom(self, a_val):
        global_set_midi_zoom(a_val * 0.1)
        #global_open_items()
        shared.AUDIO_SEQ.set_zoom(float(a_val) * 0.1)
        self.tab_changed()

    def set_headers(self): #Because clearing the table clears the headers
        self.notes_table_widget.setHorizontalHeaderLabels(
            [_('Start'), _('Length'), _('Note'), _('Note#'), _('Velocity')])
        self.ccs_table_widget.setHorizontalHeaderLabels(
            [_('Start'), _('Control'), _('Value')])
        self.pitchbend_table_widget.setHorizontalHeaderLabels(
            [_('Start'), _('Value')])

    def set_row_counts(self):
        if shared.CURRENT_ITEM:
            self.notes_table_widget.setRowCount(len(shared.CURRENT_ITEM.notes))
            self.ccs_table_widget.setRowCount(len(shared.CURRENT_ITEM.ccs))
            self.pitchbend_table_widget.setRowCount(
                len(shared.CURRENT_ITEM.pitchbends))
        else:
            self.notes_table_widget.setRowCount(0)
            self.ccs_table_widget.setRowCount(0)
            self.pitchbend_table_widget.setRowCount(0)

    def add_cc(self, a_cc):
        shared.CURRENT_ITEM.add_cc(a_cc)

    def add_note(self, a_note):
        shared.CURRENT_ITEM.add_note(a_note, False)

    def add_pb(self, a_pb):
        shared.CURRENT_ITEM.add_pb(a_pb)

    def open_item_list(self):
        self.notes_table_widget.clear()
        self.ccs_table_widget.clear()
        self.pitchbend_table_widget.clear()
        self.set_headers()
        self.notes_table_widget.setSortingEnabled(False)
        self.set_row_counts()

        if not shared.CURRENT_ITEM:
            return

        for note, f_i in zip(
        shared.CURRENT_ITEM.notes, range(len(shared.CURRENT_ITEM.notes))):
            f_note_str = note_num_to_string(note.note_num)
            self.notes_table_widget.setItem(
                f_i, 0, QTableWidgetItem(str(note.start)))
            self.notes_table_widget.setItem(
                f_i, 1, QTableWidgetItem(str(note.length)))
            self.notes_table_widget.setItem(
                f_i, 2, QTableWidgetItem(f_note_str))
            self.notes_table_widget.setItem(
                f_i, 3, QTableWidgetItem(str(note.note_num)))
            self.notes_table_widget.setItem(
                f_i, 4, QTableWidgetItem(str(note.velocity)))
        self.notes_table_widget.setSortingEnabled(True)
        self.ccs_table_widget.setSortingEnabled(False)

        for cc, f_i in zip(
        shared.CURRENT_ITEM.ccs, range(len(shared.CURRENT_ITEM.ccs))):
            self.ccs_table_widget.setItem(
                f_i, 0, QTableWidgetItem(str(cc.start)))
            self.ccs_table_widget.setItem(
                f_i, 1, QTableWidgetItem(str(cc.cc_num)))
            self.ccs_table_widget.setItem(
                f_i, 2, QTableWidgetItem(str(cc.cc_val)))
        self.ccs_table_widget.setSortingEnabled(True)
        self.pitchbend_table_widget.setSortingEnabled(False)

        for pb, f_i in zip(
            shared.CURRENT_ITEM.pitchbends,
            range(len(shared.CURRENT_ITEM.pitchbends)),
        ):
            self.pitchbend_table_widget.setItem(
                f_i, 0, QTableWidgetItem(str(pb.start)))
            self.pitchbend_table_widget.setItem(
                f_i, 1, QTableWidgetItem(str(pb.pb_val)))
        self.pitchbend_table_widget.setSortingEnabled(True)
        self.notes_table_widget.resizeColumnsToContents()
        self.ccs_table_widget.resizeColumnsToContents()
        self.pitchbend_table_widget.resizeColumnsToContents()

