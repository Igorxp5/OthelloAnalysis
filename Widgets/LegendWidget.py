from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


class LegendWidget(QtWidgets.QWidget):
    CHAR_WIDTH = 8
    TEXT_HEIGHT = 17
    MARGIN_LEFT = 10
    SQUARE_SIZE = 25
    STROKE_WIDTH = 2

    def __init__(self, color, text, *args, **kwargs):
        super(LegendWidget, self).__init__(*args, **kwargs)

        self._text = text
        self._color = color
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(Qt.black, self.STROKE_WIDTH, Qt.SolidLine))
        painter.setBrush(QtGui.QBrush(QtGui.QColor(self._color), Qt.SolidPattern))
        painter.drawRect(1, 1, self.SQUARE_SIZE, self.SQUARE_SIZE)
        y = (self.SQUARE_SIZE - self.TEXT_HEIGHT) // 2
        static_text = QtGui.QStaticText()
        static_text.setText(self._text)
        painter.drawStaticText(self.SQUARE_SIZE + self.MARGIN_LEFT, y, static_text)
        width = self.SQUARE_SIZE + self.MARGIN_LEFT + self.CHAR_WIDTH * len(self._text)
        self.setFixedWidth(width + 2)
        self.setFixedHeight(self.SQUARE_SIZE + 2)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    legend_widget = LegendWidget('#db5c5c', 'Best action')

    legend_widget.show()
    sys.exit(app.exec_())