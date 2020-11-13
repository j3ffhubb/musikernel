#!/usr/bin/env python3

"""
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

import mkpy.libpydaw.pydaw_util as pydaw_util
from mkpy.libpydaw.translate import _

from mkpy.mkqt import *

import json
import os
import shutil
import tarfile
import datetime

class project_history_widget(QTreeWidget):
    def __init__(self, a_backup_dir, a_backup_file, a_project_dir):
        QTreeWidget.__init__(self)
        self.header().close()
        self.backup_file = a_backup_file
        self.backup_dir = a_backup_dir
        self.project_dir = a_project_dir
        with open(a_backup_file) as f_handle:
            self.project_data = json.load(f_handle)
        self.nodes = []
        self.draw_tree()

    def draw_tree(self):
        self.clear()
        for f_name, f_data in self.project_data["NODES"].items():
            pass
        # ^^^ should be exactly one root
        self.nodes = []
        f_root_node = self.get_node(f_name, f_name)
        self.nodes.append(f_root_node)
        self.addTopLevelItem(f_root_node)
        self.recursive_node_add(f_name, f_data, f_root_node)
        self.expandAll()
        for f_node in self.nodes:
            if f_node.node_path == self.project_data["CURRENT"]:
                f_node.setSelected(True)

    def get_node(self, a_text, a_path):
        f_node = QTreeWidgetItem()
        f_node.setText(0, a_text)
        f_node.node_path = a_path
        self.nodes.append(f_node)
        return f_node

    def recursive_node_add(self, a_path, a_node, a_parent_node):
        for k in sorted(a_node):
            v = a_node[k]
            f_path = "/".join((a_path, k))
            f_node = self.get_node(k, f_path)
            a_parent_node.addChild(f_node)
            self.recursive_node_add(f_path, v, f_node)

    def node_context_menu_event(self, a_event):
        f_menu = QMenu()
        f_menu.exec_(QCursor.pos())

    def set_selected_as_project(self):
        f_items = self.selectedItems()
        if f_items and len(f_items) == 1:
            f_project_dir = os.path.join(self.project_dir, "projects")
            f_tmp_dir = "{}-tmp-{}".format(
                f_project_dir,
                datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            f_item = f_items[0]
            f_tar_path = os.path.join(
                self.backup_dir, f_item.text(0))
            shutil.move(f_project_dir, f_tmp_dir)
            with tarfile.open(f_tar_path, "r:bz2") as f_tar:
                f_tar.extractall(self.project_dir)
            self.project_data["CURRENT"] = f_item.node_path
            with open(self.backup_file, "w", newline="\n") as f_handle:
                json.dump(
                    self.project_data, f_handle, sort_keys=True,
                    indent=4, separators=(',', ': '))
            shutil.rmtree(f_tmp_dir)
            QMessageBox.warning(
                self, _("Complete"),
                _("Reverted project to {}".format(f_item.node_path)))
            self.draw_tree()



def project_recover_dialog(a_file):
    f_window = QMainWindow()
    f_window.setStyleSheet(pydaw_util.STYLESHEET)
    f_window.setWindowState(QtCore.Qt.WindowMaximized)
    f_window.setWindowTitle("Project History")
    if a_file is None:
        f_file, f_filter = QFileDialog.getOpenFileName(
            caption='Open Project',
            filter=pydaw_util.global_pydaw_file_type_string,
            directory=pydaw_util.global_default_project_folder,
            options=QFileDialog.DontUseNativeDialog,
        )
        if f_file is None or not str(f_file):
            return None
    else:
        f_file = a_file
    f_project_dir = os.path.dirname(str(f_file))
    f_backup_file = os.path.join(f_project_dir, "backups.json")
    if not os.path.isfile(f_backup_file):
        f_answer = QMessageBox.question(
            f_window, _("Error"), _("No backups exist for this "
            "project, recovery is not possible.\nPress 'Yes' to "
            "open another project,\n'No' to create a new project,\n"
            "or 'Cancel' to close MusiKernel"),
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Cancel)
        if (f_answer == QMessageBox.Yes and pydaw_util.open_project()) or \
        (f_answer == QMessageBox.No and pydaw_util.new_project()):
            pydaw_util.run_musikernel()
            exit(0)
        exit(1)
    f_backup_dir = os.path.join(f_project_dir, "backups")
    f_central_widget = QWidget()
    f_layout = QVBoxLayout(f_central_widget)
    f_window.setCentralWidget(f_central_widget)
    f_widget = project_history_widget(
        f_backup_dir, f_backup_file, f_project_dir)
    f_layout.addWidget(f_widget)
    f_hlayout = QHBoxLayout()
    f_layout.addLayout(f_hlayout)
    f_set_project_button = QPushButton(
        _("Revert Project to Selected"))
    f_set_project_button.pressed.connect(
        f_widget.set_selected_as_project)
    f_hlayout.addWidget(f_set_project_button)
    f_hlayout.addItem(
        QSpacerItem(1, 1, QSizePolicy.Expanding))
    print("showing")
    f_window.show()
    return f_window


if __name__ == "__main__":
    def _main():
        import sys
        app = QApplication(sys.argv)
        f_window = project_recover_dialog(
            sys.argv[1] if len(sys.argv) == 2 else None)
        exit(app.exec_())

    _main()
