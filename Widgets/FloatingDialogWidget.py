import math

from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


class FloatingDialog(QtWidgets.QWidget):
    CHAR_WIDTH = 7.2
    LINE_HEIGHT = 17
    TRIANGLE_WIDTH = 20

    def __init__(self, padding=10, line_margin=3, *args, **kwargs):
        super(FloatingDialog, self).__init__(*args, **kwargs)

        self._content = ''
        self._padding = padding
        self._line_margin = line_margin
        self._stroke_width = 1
        
        self._pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
        self._pen.setWidth(self._stroke_width)
        self._brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 255))
        
    def set_content(self, content):
        self._content = content
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        if self._stroke_width:
            painter.setPen(self._pen)
        painter.setBrush(self._brush)
        painter.drawPolygon(self._out_box_polygon())
        padding = self._padding + self._stroke_width
        lines = self._content.splitlines()
        for i, line in enumerate(lines):
            static_text = QtGui.QStaticText()
            static_text.setText(line)
            line_total_height = self.LINE_HEIGHT + self._line_margin
            painter.drawStaticText(QtCore.QPoint(padding, padding + i * line_total_height), static_text)
    
    def _out_box_polygon(self):
        width, height = self._get_size()
        polygon = QtGui.QPolygonF()
        polygon.append(QtCore.QPointF(0, 0))
        polygon.append(QtCore.QPointF(width, 0))
        polygon.append(QtCore.QPointF(width, height))
        polygon.append(QtCore.QPointF(self.TRIANGLE_WIDTH, height))
        x, y = self.TRIANGLE_WIDTH // 2, height + math.tan(math.radians(60)) * (self.TRIANGLE_WIDTH // 2)
        polygon.append(QtCore.QPointF(x, y))
        polygon.append(QtCore.QPointF(0, height))
        
        return polygon
    
    def _get_size(self):
        lines = self._content.splitlines()
        max_string = (lines or '') and max(lines, key=len)
        width = self._padding * 2 + len(max_string) * self.CHAR_WIDTH + self._stroke_width * 2
        height = self._padding * 2 + len(lines) * (self.LINE_HEIGHT + self._line_margin) + self._stroke_width * 2
        return width, height


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    floating_dialog = FloatingDialog()

    floating_dialog.show()
    sys.exit(app.exec_())