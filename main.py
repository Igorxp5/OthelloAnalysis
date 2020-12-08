import sys

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt

from Widgets import BoardWidget, PlayerCardWidget

from listener import OthelloListener, ListenerCallback


class Application(QApplication):
    def __init__(self, window_title, window_size=(800, 440)):
        super().__init__(sys.argv)

        # Listeners
        self._listener = OthelloListener()

        self._listener.register_callback(ListenerCallback.BOARD, self._board_callback)
        self._listener.register_callback(ListenerCallback.PLAYERS, self._players_callback)
        self._listener.register_callback(ListenerCallback.PLAYERS_TIME, self._players_time_callback)
        self._listener.register_callback(ListenerCallback.PLAYERS_POINTS, self._players_points_callback)
        

        self._player_name = None
        self._opponent_name = None


        self._window = QWidget()
        self._window.setWindowTitle(window_title)
        self._window.setFixedWidth(window_size[0])
        self._window.setFixedHeight(window_size[1])

        self._board_widget = BoardWidget(8)

        self._main_layout = QGridLayout(self._window)
        self._main_layout.addWidget(self._board_widget, 0, 0, alignment=Qt.AlignTop)

        self._parameters_layout = QVBoxLayout()
        self._main_layout.addLayout(self._parameters_layout, 0, 1)

        # Player
        self._player_card_widget = PlayerCardWidget()
        self._parameters_layout.addWidget(self._player_card_widget)

        # Opponent
        self._opponent_card_widget = PlayerCardWidget()
        self._parameters_layout.addWidget(self._opponent_card_widget)

        # Parameter Title
        parameters_label = QLabel('Parameters')
        parameters_font = QFont()
        parameters_font.setBold(True)
        parameters_label.setFont(parameters_font)
        self._parameters_layout.addWidget(parameters_label)

        # Depth Level
        depth_level_title = QLabel('Depth level')
        depth_level_slider_label = QLabel('0')
        self._depth_level_slider = QSlider(Qt.Horizontal)
        self._depth_level_slider.setRange(0, 60)
        self._depth_level_slider.setTickInterval(1)
        self._depth_level_slider.valueChanged.connect(lambda v: depth_level_slider_label.setText(str(v)))
        self._parameters_layout.addWidget(depth_level_title)
        self._parameters_layout.addWidget(self._depth_level_slider)
        self._parameters_layout.addWidget(depth_level_slider_label, alignment=Qt.AlignCenter)

        # Value Function
        value_function_title = QLabel('Value Function')
        self._parameters_layout.addWidget(value_function_title)

        group_box = QGroupBox()
        self._parameters_layout.addWidget(group_box)

        self._parameters_layout.addStretch()
    
    def run(self):
        self._listener.start()
        self._window.show()
        sys.exit(self.exec_())

    def _board_callback(self, event, result):
        self._board_widget.set_board(result)
    
    def _players_callback(self, event, result):
        if result:
            self._player_name, self._opponent_name = result
            self._player_card_widget.set_player_name(self._player_name)
            self._opponent_card_widget.set_player_name(self._opponent_name)
    
    def _players_time_callback(self, event, result):
        if result:
            self._player_card_widget.set_time(result[self._player_name])
            self._opponent_card_widget.set_time(result[self._opponent_name])
    
    def _players_points_callback(self, event, result):
        if result:
            self._player_card_widget.set_points(result[self._player_name])
            self._opponent_card_widget.set_points(result[self._opponent_name])


if __name__ == '__main__':
    app = Application('Othello Analysis')
    app.run()
