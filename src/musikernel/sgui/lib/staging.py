# -*- coding: utf-8 -*-
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


from sgui.sgqt import *

class wire_input_port(QGraphicsRectItem):
    def __init__(self):
        pass

class wire_output_port(QGraphicsRectItem):
    def __init__(self):
        pass

class wire_block(QGraphicsRectItem):
    """ Over-ride to add extra controls to the middle-area """
    def __init__(self, a_in_count, a_out_count, a_brush, a_drag=False):
        QGraphicsRectItem.__init__(self)

class wire_canvas:
    def __init__(self):
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QtCore.Qt.darkGray)
        self.view.setScene(self.scene)

    def draw_item(self, a_item):
        """ Over-ride this and use it to draw the various
            blocks and wires
        """
        raise NotImplementedError()

class mk_track_route:
    def __init__(self, a_in_count, a_out_count, a_out_connections=None):
        """ a_out_connections =
            {
                out_port_num:[(track_num, channel_num), ...],
                out_port_num:[(track_num, channel_num), ...]
            }
        """
        self.out_count = a_out_count
        self.in_count = a_in_count
        self.out_connections = a_out_connections

ROUTING_STRUCT_PROTOTYPE = {
    0:{ # level
        2: mk_track_route(0, 4),  # master in, not connected
        2: mk_track_route(0, 2, {0:[(0, 0)], 1:[(0, 1)]})
    },
    1:{ # level
       0: mk_track_route(2, 0)  # master out
    }
}

if __name__ == "__main__":

    import sys
    app = QApplication(sys.argv)
    f_widget = wire_canvas()
    f_widget.view.show()

    sys.exit(app.exec_())

