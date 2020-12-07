import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer

from widgets import BoardWidget
from listener import OthelloListener, ListenerCallback

app = QApplication(sys.argv)
window = QWidget()

window.setWindowTitle('Othello Analysis')
window.show()

board_widget = BoardWidget(8)

layout = QGridLayout(window)
layout.addWidget(board_widget, 0, 0)

def callback(event, result):
    board_widget.set_board(result)

listener = OthelloListener()
listener.start()

listener.register_callback(ListenerCallback.BOARD, callback)

sys.exit(app.exec_())
