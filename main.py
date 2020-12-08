import sys
import collections

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt

from Widgets import BoardWidget, PlayerCardWidget, \
    FloatingDialogWidget, FloatingDialogAlignment

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
        self._lotteries = {(3, 3): {-1: 0.5, 3: 0.3, 4: 0.2}}  # example

        self._window = QWidget()
        self._window.setWindowTitle(window_title)
        self._window.setFixedWidth(window_size[0])
        self._window.setFixedHeight(window_size[1])

        self._board_widget = BoardWidget(8)
        self._board_widget.register_square_hover_callback(self._square_hover_callback)
        self._floating_dialog_widget = FloatingDialogWidget(parent=self._board_widget)
        self._floating_dialog_widget.hide()

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
        # self._listener.start()
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
    
    def _square_hover_callback(self, square):
        if not (square and square in self._lotteries):
            return self._floating_dialog_widget.hide()
        
        board_size = self._board_widget.get_board_size()
        board_width, board_height = self._board_widget.get_size()
        square_size = board_width // board_size
        x = square[1] * square_size + square_size // 2
        y = square[0] * square_size + square_size // 2
        
        ordered_lottery = collections.OrderedDict(sorted(self._lotteries[square].items()))
        
        lines = []
        for pieces, probability in ordered_lottery.items():
            pieces = str(pieces).rjust(2).ljust(5)
            probability = (str(probability * 100) + '%').rjust(8)
            lines.append(f'{pieces}-{probability}')
        self._floating_dialog_widget.set_text('\n'.join(lines))
        
        if square[1] < board_size // 2 and square[0] < board_size // 2:
            alignment = FloatingDialogAlignment.TOP_LEFT
        elif square[1] > board_size // 2 and square[0] < board_size // 2:
            alignment = FloatingDialogAlignment.TOP_RIGHT
        elif square[1] > board_size // 2 and square[0] > board_size // 2:
            alignment = FloatingDialogAlignment.BOTTOM_RIGHT
        elif square[1] < board_size // 2 and square[0] > board_size // 2:
            alignment = FloatingDialogAlignment.BOTTOM_LEFT

        self._floating_dialog_widget.set_alignment(alignment)
        self._floating_dialog_widget.move(x, y)
        self._floating_dialog_widget.show()


if __name__ == '__main__':
    app = Application('Othello Analysis')
    app.run()
