import os
import sys
import matplotlib
import numpy as np
import collections

matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt

from threading import Thread

from Widgets import BoardWidget, PlayerCardWidget, LegendWidget, \
    FloatingDialogWidget, FloatingDialogAlignment

from Othello import OthelloGame, OthelloPlayer

from listener import OthelloListener, ListenerCallback
from move_analysis import MoveAnalysis

class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)        
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class Application(QApplication):
    BEST_ACTION_COLOR = '#db5c5c'
    VALID_ACTIONS_COLOR = '#6edb5c'
    GREEDY_ACTION_COLOR = '#dbd35c'

    WINDOW_SIZE = 850, 600 #490

    def __init__(self, window_title):
        super().__init__(sys.argv)

        # Listeners
        self._listener = OthelloListener()

        self._listener.register_callback(ListenerCallback.BOARD, self._listener_callback)
        self._listener.register_callback(ListenerCallback.PLAYERS, self._listener_callback)
        self._listener.register_callback(ListenerCallback.PLAYERS_TIME, self._listener_callback)
        self._listener.register_callback(ListenerCallback.PLAYERS_POINTS, self._listener_callback)
        self._listener.register_callback(ListenerCallback.PLAYER_COLOR, self._listener_callback)
        self._listener.register_callback(ListenerCallback.CURRENT_PLAYER, self._listener_callback)
        self._listener.register_callback(ListenerCallback.GAME_PROGRESS, self._listener_callback)
        if os.name != 'nt':
            self._listener.register_callback(ListenerCallback.IN_GAME, self._listener_callback)

        self._listener.register_callback(ListenerCallback.CLOSE, self._listener_close_callback)

        self._move_analysis = None

        self._player_name = None
        self._opponent_name = None
        self._lotteries = {}

        self._current_player = None
        self._player_color = None
        self._players_time = dict()
        self._players_points = dict()
        self._rendered_rounds = set()
        self._board = None
        self._game_progress = None
        self._depth_level = 2
        self._exponential_utility_factor = 0

        self._waiting_window = QWidget()
        self._waiting_window.setWindowTitle(window_title)
        self._waiting_window.setFixedWidth(self.WINDOW_SIZE[0])
        self._waiting_window.setFixedHeight(self.WINDOW_SIZE[1])

        waiting_layout = QGridLayout(self._waiting_window)
        waiting_label = QLabel('Entre em sua conta do Board Game Arena\n'
                               'pelo navegador aberto por esse programa e \n'
                               'inicie uma partida.\n\nEsperando por uma partida...')
        waiting_label.setAlignment(Qt.AlignCenter)
        waiting_layout.addWidget(waiting_label, 0, 0, alignment=Qt.AlignCenter)


        self._main_window = QWidget()
        self._main_window.setWindowTitle(window_title)
        self._main_window.setFixedWidth(self.WINDOW_SIZE[0])
        self._main_window.setFixedHeight(self.WINDOW_SIZE[1])

        self._board_widget = BoardWidget(8)
        self._board_widget.register_square_hover_callback(self._square_hover)
        self._floating_dialog_widget = FloatingDialogWidget(parent=self._board_widget)
        self._floating_dialog_widget.hide()

        self._main_layout = QGridLayout(self._main_window)
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
        self._depth_level_slider_label = QLabel('0')
        self._depth_level_slider = QSlider(Qt.Horizontal)
        self._depth_level_slider.setRange(0, 10)
        self._depth_level_slider.setTickInterval(1)
        self._depth_level_slider.valueChanged.connect(self._depth_level_slider_changed)
        self._depth_level_slider.setValue(self._depth_level)
        self._parameters_layout.addWidget(depth_level_title)
        self._parameters_layout.addWidget(self._depth_level_slider)
        self._parameters_layout.addWidget(self._depth_level_slider_label, alignment=Qt.AlignCenter)

        # Value Function
        value_function_title = QLabel('Value Function')
        self._parameters_layout.addWidget(value_function_title)

        group_box = QGroupBox()
        group_box.setFixedHeight(300)
        self._parameters_layout.addWidget(group_box)

        vbox = QVBoxLayout()
        group_box.setLayout(vbox)
        self._canvas = MplCanvas(self, width=5, height=6, dpi=100)
        self._xdata = np.array(range(-63, 63, 1))
        self._ydata = self._get_utility_value(self._xdata)
        vbox.addWidget(self._canvas)
        self._update_plot()

        #slide exponential utility factor
        factor_level_title = QLabel('Risk Level: ')
        self._factor_level_slider_label = QLabel('0')
        self._factor_level_slider = QSlider(Qt.Horizontal)
        self._factor_level_slider.setRange(-50, 50)
        self._factor_level_slider.setTickInterval(1)
        self._factor_level_slider.valueChanged.connect(self._factor_changed)
        self._factor_level_slider.setValue(self._exponential_utility_factor)
        vbox.addWidget(factor_level_title)
        vbox.addWidget(self._factor_level_slider)
        vbox.addWidget(self._factor_level_slider_label, alignment=Qt.AlignCenter)

        # self._parameters_layout.addStretch()

        # Legend Footer
        self._footer_layout = QHBoxLayout()
        self._footer_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.addLayout(self._footer_layout, 1, 0)

        best_action_legend = LegendWidget(self.BEST_ACTION_COLOR, 'Best action')
        self._footer_layout.addWidget(best_action_legend)

        greddy_action_legend = LegendWidget(self.GREEDY_ACTION_COLOR, 'Greedy action')
        self._footer_layout.addWidget(greddy_action_legend)

        valid_actions_legend = LegendWidget(self.VALID_ACTIONS_COLOR, 'Valid action')
        self._footer_layout.addWidget(valid_actions_legend)

        self._statusbar = QStatusBar()
        self._main_layout.addWidget(self._statusbar, 2, 0, 1, 2)

    def run(self):
        self._listener.start()
        if os.name == 'nt':
            self._main_window.show()
        else:
            self._waiting_window.show()
        sys.exit(self.exec_())
    
    def _in_game_callback(self, event, result):
        if result:
            self._waiting_window.hide()
            self._main_window.show()
        else:
            self._player_name = None
            self._opponent_name = None
            self._lotteries = {}

            self._current_player = None
            self._player_color = None
            self._players_time = dict()
            self._players_points = dict()
            self._board = None
            self._depth_level = 2
            self._game_progress = None
            self._rendered_rounds = set()
            self._exponential_utility_factor = 0

            self._waiting_window.show()
            self._main_window.hide()
    
    def _listener_callback(self, event, result):
        if event is ListenerCallback.BOARD:
            self._board_callback(event, result)
        elif event is ListenerCallback.PLAYERS:
            self._players_callback(event, result)
        elif event is ListenerCallback.PLAYERS_TIME:
            self._players_time_callback(event, result)
        elif event is ListenerCallback.PLAYERS_POINTS:
            self._players_points_callback(event, result)
        elif event is ListenerCallback.CURRENT_PLAYER:
            self._current_player_callback(event, result)
        elif event is ListenerCallback.PLAYER_COLOR:
            self._player_color_callback(event, result)
        elif event is ListenerCallback.IN_GAME:
            self._in_game_callback(event, result)
        elif event is ListenerCallback.GAME_PROGRESS:
            self._game_progress_callback(event, result)

        
        if self._player_name:
            self._player_card_widget.set_player_name(self._player_name)
            self._opponent_card_widget.set_player_name(self._opponent_name)

            if self._players_time:
                self._player_card_widget.set_time(self._players_time[self._player_name])
                self._opponent_card_widget.set_time(self._players_time[self._opponent_name])
            
            if self._players_points:
                self._player_card_widget.set_points(self._players_points[self._player_name])
                self._opponent_card_widget.set_points(self._players_points[self._opponent_name])

            if self._game_progress and self._game_progress not in self._rendered_rounds:
                self._lotteries = {}  # Clear lotteries when the round changes
                if self._move_analysis and self._move_analysis.is_alive():
                    self._move_analysis.stop()
                self._render_board()

    def _board_callback(self, event, result):
        self._board = result
        self._board_widget.set_board(result)
    
    def _game_progress_callback(self, event, result):
        if result:
            self._game_progress = result
    
    def _players_callback(self, event, result):
        if result:
            self._player_name, self._opponent_name = result

    def _players_time_callback(self, event, result):
        if result:
            self._players_time = result
    
    def _players_points_callback(self, event, result):
        if result:
            self._players_points = result

    def _current_player_callback(self, event, result):
        if result:
            self._current_player = result

    def _player_color_callback(self, event, result):
        if result:
            self._player_color = OthelloPlayer.BLACK if result == 1 else OthelloPlayer.WHITE 
    
    def _listener_close_callback(self, event, result):
        self.quit()

    def _square_hover(self, square):
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
            probability = ('{:.2f}%'.format(probability * 100)).rjust(8)
            lines.append(f'{pieces}-{probability}')
        self._floating_dialog_widget.set_text('\n'.join(lines))
        
        if square[1] < board_size // 2 and square[0] < board_size // 2:
            alignment = FloatingDialogAlignment.TOP_LEFT
        elif square[1] >= board_size // 2 and square[0] < board_size // 2:
            alignment = FloatingDialogAlignment.TOP_RIGHT
        elif square[1] >= board_size // 2 and square[0] >= board_size // 2:
            alignment = FloatingDialogAlignment.BOTTOM_RIGHT
        elif square[1] < board_size // 2 and square[0] >= board_size // 2:
            alignment = FloatingDialogAlignment.BOTTOM_LEFT

        self._floating_dialog_widget.set_alignment(alignment)
        self._floating_dialog_widget.move(x, y)
        self._floating_dialog_widget.show()

    def _render_board(self, update_lotteries=True):
        highlight_squares = dict()
        if self._board is not None and self._current_player == self._player_name and self._player_color and self._game_progress:
            self._rendered_rounds.add(self._game_progress)
            state = OthelloGame.convert_to_two_channels_board(self._board)
            greedy_actions = tuple(OthelloGame.get_greedy_actions(state, self._player_color))
            valid_actions = OthelloGame.get_player_valid_actions(state, self._player_color)
            highlight_squares.update({tuple(a): self.VALID_ACTIONS_COLOR for a in valid_actions})
            highlight_squares.update({tuple(a): self.GREEDY_ACTION_COLOR for a in greedy_actions})
            self._board_widget.set_board(self._board, highlight_squares=highlight_squares)
            
            success = not update_lotteries or self._update_lotteries()
            if success:
                best_action = self._get_best_action()
                highlight_squares.update({best_action: self.BEST_ACTION_COLOR})
                self._board_widget.set_board(self._board, highlight_squares=highlight_squares)
        elif self._board is not None:
            self._board_widget.set_board(self._board, highlight_squares=highlight_squares)

    def _depth_level_slider_changed(self, value):
        self._depth_level_slider_label.setText(str(value))
        self._depth_level = value
        Thread(target=self._render_board).start()
    
    def _factor_changed(self, value):
        self._factor_level_slider_label.setText(str(value/10 if value != 0 else 0))
        self._exponential_utility_factor = value
        self._update_plot()
        self._render_board(False)
    
    def _update_plot(self):
        self._ydata = self._get_utility_value(self._xdata)
        self._canvas.axes.cla()
        self._canvas.axes.plot(self._xdata, self._ydata, 'r')
        self._canvas.draw()

    def _update_lotteries(self):
        if self._move_analysis and self._move_analysis.is_alive():
            self._move_analysis.stop()
        
        state = OthelloGame.convert_to_two_channels_board(self._board)
        possible_actions = list(OthelloGame.get_player_valid_actions(state, self._player_color))

        lotteries = {}
        success = False
        for action in possible_actions:
            self._statusbar.showMessage('Calculating best action...')
            action = tuple(action)
            self._move_analysis = MoveAnalysis(state, action, self._player_color, self._depth_level)
            self._move_analysis.start()
            lottery = self._move_analysis.get_result()
            if not lottery:
                break
            lotteries.update({action: lottery})
        else:
            sums = {a: sum(lotteries[a].values()) for a in lotteries}
            for a in lotteries:
                lotteries[a] = {p: lotteries[a][p] / sums[a] for p in lotteries[a]}
            self._lotteries = lotteries
            success = True
        
        self._statusbar.showMessage('')

        return success

    def _get_best_action(self):
        return max(self._lotteries, key=lambda a: self._get_lottery_utility(self._lotteries[a]))
    
    def _get_lottery_utility(self, lottery):
        return sum(self._get_utility_value(value) * probability for value, probability in lottery.items())
    
    def _get_utility_value(self, value):
        value = value/63
        if self._exponential_utility_factor == 0:
            return value
        else:
            return (1-np.exp(-(-self._exponential_utility_factor/10) * value))/ (-self._exponential_utility_factor/10)


if __name__ == '__main__':
    app = Application('Othello Analysis')
    app.run()
