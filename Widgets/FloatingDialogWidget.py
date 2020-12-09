import math

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from enum import Enum, auto


class FloatingDialogAlignment(Enum):
    TOP_RIGHT = auto()
    TOP_LEFT = auto()
    BOTTOM_RIGHT = auto()
    BOTTOM_LEFT = auto()


class FloatingDialogWidget(QtWidgets.QWidget):
    CHAR_WIDTH = 6
    LINE_HEIGHT = 17
    TRIANGLE_WIDTH = 15

    def __init__(self, padding=15, line_margin=3, *args, **kwargs):
        super(FloatingDialogWidget, self).__init__(*args, **kwargs)

        self._text = ''
        self._alignment = FloatingDialogAlignment.BOTTOM_LEFT
        self._padding = padding
        self._line_margin = line_margin
        self._stroke_width = 1
        
        self._pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
        self._pen.setWidth(self._stroke_width)
        self._brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 255))
        
    def set_text(self, text):
        self._text = text
        self.update()
    
    def set_alignment(self, alignment):
        if not isinstance(alignment, FloatingDialogAlignment):
            raise TypeError('expecting FloatingDialogAlignment')
        self._alignment = alignment
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        if self._stroke_width:
            painter.setPen(self._pen)
        painter.setBrush(self._brush)
        painter.drawPolygon(self._out_box_polygon())
        padding = self._padding + self._stroke_width
        lines = self._text.splitlines()
        text_y = 0
        if self._alignment in (FloatingDialogAlignment.TOP_LEFT, FloatingDialogAlignment.TOP_RIGHT):
            text_y = self.TRIANGLE_WIDTH
        for i, line in enumerate(lines):
            static_text = QtGui.QStaticText()
            static_text.setText(line)
            line_total_height = self.LINE_HEIGHT + self._line_margin
            painter.drawStaticText(QtCore.QPoint(padding, text_y + padding + i * line_total_height), static_text)
        self._update_fixed_size()
    
    def move(self, x, y):
        if self._alignment is FloatingDialogAlignment.TOP_RIGHT:
            x -= self.get_size()[0]
        elif self._alignment is FloatingDialogAlignment.BOTTOM_RIGHT:
            x -= self.get_size()[0]
            y -= self.get_size()[1]
        elif self._alignment is FloatingDialogAlignment.BOTTOM_LEFT:
            y -= self.get_size()[1]
        super().move(x, y)

    def _out_box_polygon(self):
        width, height = self.get_size()
        height -= self.TRIANGLE_WIDTH
        
        polygon = QtGui.QPolygonF()

        # Bottom-Left
        if self._alignment is FloatingDialogAlignment.BOTTOM_LEFT:
            polygon.append(QtCore.QPointF(0, 0))
            polygon.append(QtCore.QPointF(width, 0))
            polygon.append(QtCore.QPointF(width, height))
            polygon.append(QtCore.QPointF(self.TRIANGLE_WIDTH, height))
            polygon.append(QtCore.QPointF(0, height + self.TRIANGLE_WIDTH))
            polygon.append(QtCore.QPointF(0, height))
        elif self._alignment is FloatingDialogAlignment.BOTTOM_RIGHT:
            polygon.append(QtCore.QPointF(0, 0))
            polygon.append(QtCore.QPointF(width, 0))
            polygon.append(QtCore.QPointF(width, height + self.TRIANGLE_WIDTH))
            polygon.append(QtCore.QPointF(width - self.TRIANGLE_WIDTH, height))
            polygon.append(QtCore.QPointF(0, height))
        elif self._alignment is FloatingDialogAlignment.TOP_LEFT:
            polygon.append(QtCore.QPointF(0, 0))
            polygon.append(QtCore.QPointF(self.TRIANGLE_WIDTH, self.TRIANGLE_WIDTH))
            polygon.append(QtCore.QPointF(width, self.TRIANGLE_WIDTH))
            polygon.append(QtCore.QPointF(width, self.TRIANGLE_WIDTH + height))
            polygon.append(QtCore.QPointF(0, self.TRIANGLE_WIDTH + height))
        elif self._alignment is FloatingDialogAlignment.TOP_RIGHT:
            polygon.append(QtCore.QPointF(0, self.TRIANGLE_WIDTH))
            polygon.append(QtCore.QPointF(width - self.TRIANGLE_WIDTH, self.TRIANGLE_WIDTH))
            polygon.append(QtCore.QPointF(width, 0))
            polygon.append(QtCore.QPointF(width, height + self.TRIANGLE_WIDTH))
            polygon.append(QtCore.QPointF(0, height + self.TRIANGLE_WIDTH))

        return polygon

    def get_size(self):
        lines = self._text.splitlines()
        max_string = (lines or '') and max(lines, key=len)
        width = self._padding * 2 + len(max_string) * self.CHAR_WIDTH + self._stroke_width * 2
        height = self._padding * 2 + len(lines) * (self.LINE_HEIGHT + self._line_margin) + self._stroke_width * 2
        return width, height + self.TRIANGLE_WIDTH
    
    def _update_fixed_size(self):
        width, height = self.get_size()
        self.setFixedWidth(width + 1)
        self.setFixedHeight(height + 1)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    floating_dialog = FloatingDialogWidget()

    floating_dialog.show()
    sys.exit(app.exec_())