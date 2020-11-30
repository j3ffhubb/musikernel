from . import _shared
from sgui.mkqt import *

ROUTING_GRAPH_NODE_BRUSH = None
ROUTING_GRAPH_TO_BRUSH = None
ROUTING_GRAPH_FROM_BRUSH = None

class RoutingGraphNode(QGraphicsRectItem):
    def __init__(self, a_text, a_width, a_height):
        QGraphicsRectItem.__init__(self, 0, 0, a_width, a_height)
        self.text = QGraphicsSimpleTextItem(a_text, self)
        self.text.setPos(3.0, 3.0)
        self.setPen(QtCore.Qt.black)
        self.set_brush()

    def set_brush(self, a_to=False, a_from=False):
        if a_to:
            brush = ROUTING_GRAPH_TO_BRUSH
        elif a_from:
            brush = ROUTING_GRAPH_FROM_BRUSH
        else:
            brush = ROUTING_GRAPH_NODE_BRUSH
        self.setBrush(brush)


class RoutingGraphWidget(QGraphicsView):
    def __init__(self, a_toggle_callback=None):
        QGraphicsView.__init__(self)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setBackgroundBrush(_shared.SCENE_BACKGROUND_BRUSH)
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.node_dict = {}
        self.setMouseTracking(True)
        self.toggle_callback = a_toggle_callback

    def prepare_to_quit(self):
        self.scene.clearSelection()
        self.scene.clear()

    def get_coords(self, a_pos):
        f_x = int(a_pos.x() // self.node_width)
        f_y = int(a_pos.y() // self.node_height)
        return (f_x, f_y)

    def backgroundMousePressEvent(self, a_event):
        #QGraphicsRectItem.mousePressEvent(self.background_item, a_event)
        if self.toggle_callback:
            f_x, f_y = self.get_coords(a_event.scenePos())
            if f_x == f_y or f_y == 0:
                return
            if a_event.modifiers() == QtCore.Qt.ControlModifier:
                route_type = 1
            elif a_event.modifiers() == QtCore.Qt.ShiftModifier:
                route_type = 2
            else:
                route_type = 0
            self.toggle_callback(f_y, f_x, route_type)

    def backgroundHoverEvent(self, a_event):
        QGraphicsRectItem.hoverMoveEvent(self.background_item, a_event)
        f_x, f_y = self.get_coords(a_event.scenePos())
        if f_x == f_y or f_y == 0:
            self.clear_selection()
            return
        for k, v in self.node_dict.items():
            v.set_brush(k == f_x, k == f_y)

    def backgroundHoverLeaveEvent(self, a_event):
        self.clear_selection()

    def clear_selection(self):
        for v in self.node_dict.values():
            v.set_brush()

    def draw_graph(self, a_graph, a_track_names):
        self.graph_height = self.height() - 36.0
        self.graph_width = self.width() - 36.0
        self.node_width = self.graph_width / 32.0
        self.node_height = self.graph_height / 32.0
        self.wire_width = self.node_height / 4.0  #max conns
        self.wire_width_div2 = self.wire_width * 0.5
        ROUTING_GRAPH_WIRE_INPUT = ((self.node_width * 0.5) -
            (self.wire_width * 0.5))

        f_line_pen = QPen(QColor(105, 105, 105))

        global ROUTING_GRAPH_NODE_BRUSH, ROUTING_GRAPH_TO_BRUSH, \
            ROUTING_GRAPH_FROM_BRUSH
        ROUTING_GRAPH_NODE_BRUSH = QBrush(QColor(231, 231, 0))
        ROUTING_GRAPH_TO_BRUSH = QBrush(QColor(231, 160, 160))
        ROUTING_GRAPH_FROM_BRUSH = QBrush(QColor(160, 160, 231))

        self.node_dict = {}
        f_wire_gradient = QLinearGradient(
            0.0, 0.0, self.width(), self.height())
        f_wire_gradient.setColorAt(0.0, QColor(250, 250, 255))
        f_wire_gradient.setColorAt(1.0, QColor(210, 210, 222))
        f_wire_pen = QPen(f_wire_gradient, self.wire_width_div2)
        f_sc_wire_pen = QPen(QtCore.Qt.red, self.wire_width_div2)
        f_midi_wire_pen = QPen(QtCore.Qt.blue, self.wire_width_div2)
        pen_dict = {0: f_wire_pen, 1: f_sc_wire_pen, 2: f_midi_wire_pen}
        self.setUpdatesEnabled(False)
        self.scene.clear()
        self.background_item = QGraphicsRectItem(
            0.0, 0.0, self.graph_width, self.graph_height)
        self.background_item.setBrush(QtCore.Qt.transparent)
        self.background_item.setPen(QPen(QtCore.Qt.black))
        self.scene.addItem(self.background_item)
        self.background_item.hoverMoveEvent = self.backgroundHoverEvent
        self.background_item.hoverLeaveEvent = self.backgroundHoverLeaveEvent
        self.background_item.setAcceptHoverEvents(True)
        self.background_item.mousePressEvent = self.backgroundMousePressEvent
        for k, f_i in zip(
            a_track_names,
            range(len(a_track_names)),
        ):
            f_node_item = RoutingGraphNode(
                k, self.node_width,
                self.node_height)
            self.node_dict[f_i] = f_node_item
            self.scene.addItem(f_node_item)
            f_x = self.node_width * f_i
            f_y = self.node_height * f_i
            if f_i != 0:
                self.scene.addLine(
                    0.0, f_y, self.graph_width, f_y, f_line_pen)
                self.scene.addLine(
                    f_x, 0.0, f_x, self.graph_height, f_line_pen)
            f_node_item.setPos(f_x, f_y)
            if f_i == 0 or f_i not in a_graph.graph:
                continue
            f_connections = [
                (x.output, x.index, x.sidechain)
                for x in a_graph.graph[f_i].values()
            ]
            for f_dest_pos, f_wire_index, f_sidechain in f_connections:
                if f_dest_pos < 0:
                    continue
                f_pen = pen_dict[f_sidechain]
                if f_dest_pos > f_i:
                    f_src_x = f_x + self.node_width
                    f_y_wire_offset = (f_wire_index *
                        self.wire_width) + self.wire_width_div2
                    f_src_y = f_y + f_y_wire_offset
                    f_wire_width = ((f_dest_pos - f_i - 1) *
                        self.node_width) + ROUTING_GRAPH_WIRE_INPUT
                    f_v_wire_x = f_src_x + f_wire_width
                    if f_sidechain:
                        f_v_wire_x += self.wire_width_div2 * 2
                    else:
                        f_v_wire_x -= self.wire_width_div2 * 2
                    f_wire_height = ((f_dest_pos - f_i) *
                        self.node_height) - f_y_wire_offset
                    f_dest_y = f_src_y + f_wire_height
                    line = self.scene.addLine( # horizontal wire
                        f_src_x, f_src_y, f_v_wire_x, f_src_y, f_pen)
                    line.setZValue(2000)
                    line = self.scene.addLine( # vertical wire
                        f_v_wire_x, f_src_y, f_v_wire_x, f_dest_y, f_pen)
                    line.setZValue(2000)
                else:
                    f_src_x = f_x
                    f_y_wire_offset = (f_wire_index *
                        self.wire_width) + self.wire_width_div2
                    f_src_y = f_y + f_y_wire_offset
                    f_wire_width = ((f_i - f_dest_pos - 1) *
                        self.node_width) + ROUTING_GRAPH_WIRE_INPUT
                    f_v_wire_x = f_src_x - f_wire_width
                    if f_sidechain:
                        f_v_wire_x += self.wire_width_div2 * 2
                    else:
                        f_v_wire_x -= self.wire_width_div2 * 2
                    f_wire_height = ((f_i - f_dest_pos - 1) *
                        self.node_height) + f_y_wire_offset
                    f_dest_y = f_src_y - f_wire_height
                    line = self.scene.addLine( # horizontal wire
                        f_v_wire_x, f_src_y, f_src_x, f_src_y, f_pen)
                    line.setZValue(2000)
                    line = self.scene.addLine( # vertical wire
                        f_v_wire_x, f_dest_y, f_v_wire_x, f_src_y, f_pen)
                    line.setZValue(2000)

        self.setUpdatesEnabled(True)
        self.update()


