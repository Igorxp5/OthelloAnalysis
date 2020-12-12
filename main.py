import sys
import queue
import collections
import multiprocessing

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt

from Widgets import BoardWidget, PlayerCardWidget, LegendWidget, \
    FloatingDialogWidget, FloatingDialogAlignment

from Othello import OthelloGame, OthelloPlayer

from listener import OthelloListener, ListenerCallback
from move_analysis import MoveAnalysis


class Application(QApplication):
    BEST_ACTION_COLOR = '#db5c5c'
    VALID_ACTIONS_COLOR = '#6edb5c'
    GREEDY_ACTION_COLOR = '#dbd35c'

    WINDOW_SIZE = 800, 490

    def __init__(self, window_title):
        super().__init__(sys.argv)

        # Listeners
        self._listener = OthelloListener()

        self._listener.register_callback(ListenerCallback.BOARD, self._listener_callback)
        self._listener.register_callback(ListenerCallback.IN_GAME, self._listener_callback)
        self._listener.register_callback(ListenerCallback.PLAYERS, self._listener_callback)
        self._listener.register_callback(ListenerCallback.PLAYERS_TIME, self._listener_callback)
        self._listener.register_callback(ListenerCallback.PLAYERS_POINTS, self._listener_callback)
        self._listener.register_callback(ListenerCallback.PLAYER_COLOR, self._listener_callback)
        self._listener.register_callback(ListenerCallback.CURRENT_PLAYER, self._listener_callback)

        self._listener.register_callback(ListenerCallback.CLOSE, self._listener_close_callback)

        self._player_name = None
        self._opponent_name = None
        self._lotteries = {}

        self._current_player = None
        self._player_color = None
        self._players_time = dict()
        self._players_points = dict()
        self._board = None
        self._depth_level = 2

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
        self._depth_level_slider.setRange(0, 60)
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
        group_box.setFixedHeight(190)
        self._parameters_layout.addWidget(group_box)

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

        self._move_analysis_process = None

    def run(self):
        self._listener.start()
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
        
        if self._player_name:
            self._player_card_widget.set_player_name(self._player_name)
            self._opponent_card_widget.set_player_name(self._opponent_name)

            if self._players_time:
                self._player_card_widget.set_time(self._players_time[self._player_name])
                self._opponent_card_widget.set_time(self._players_time[self._opponent_name])
            
            if self._players_points:
                self._player_card_widget.set_points(self._players_points[self._player_name])
                self._opponent_card_widget.set_points(self._players_points[self._opponent_name])
            
            if event is ListenerCallback.CURRENT_PLAYER:
                self._render_board()

    def _board_callback(self, event, result):
        self._board = result
        self._board_widget.set_board(result)
    
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
            probability = (str(probability * 100) + '%').rjust(8)
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

    def _render_board(self):
        highlight_squares = dict()
        if self._board is not None and self._current_player == self._player_name and self._player_color:
            state = OthelloGame.convert_to_two_channels_board(self._board)
            greedy_action = tuple(OthelloGame.get_greedy_action(state, self._player_color))
            valid_actions = OthelloGame.get_player_valid_actions(state, self._player_color)
            highlight_squares = {tuple(a): self.VALID_ACTIONS_COLOR for a in valid_actions}
            highlight_squares.update({greedy_action: self.GREEDY_ACTION_COLOR})
            self._board_widget.set_board(self._board, highlight_squares=highlight_squares)
            
            success = self._update_lotteries()
            if success:
                best_action = self._get_best_action()
                highlight_squares.update({best_action: self.BEST_ACTION_COLOR})
                self._board_widget.set_board(self._board, highlight_squares=highlight_squares)
        elif self._board is not None:
            self._board_widget.set_board(self._board, highlight_squares=highlight_squares)

    def _depth_level_slider_changed(self, value):
        self._depth_level_slider_label.setText(str(value))
        self._depth_level = value
        self._render_board()

    def _update_lotteries(self):
        state = OthelloGame.convert_to_two_channels_board(self._board)
        possible_actions = list(OthelloGame.get_player_valid_actions(state, self._player_color))
        result_queue = multiprocessing.Queue()
        if self._move_analysis_process and self._move_analysis_process.is_alive():
            self._move_analysis_process.kill()
            self._move_analysis_process.join()
        process = multiprocessing.Process(target=self.analyse_action, 
            args=(state, self._player_color, possible_actions, self._depth_level, result_queue))
        self._move_analysis_process = process

        lotteries = {}
        progress_fraction = 100 / len(possible_actions)
        
        process.start()
        self._statusbar.showMessage('Calculating possible scenarios...')
        while process.is_alive():
            try:
                result = result_queue.get(timeout=3)
            except queue.Empty:
                continue
            lotteries.update(result)

        if process.exitcode == 0:
            sums = {a: sum(lotteries[a].values()) for a in lotteries}
            for a in lotteries:
                lotteries[a] = {p: lotteries[a][p] / sums[a] for p in lotteries[a]}
            self._lotteries = lotteries
            self._statusbar.showMessage('')
        
        return process.exitcode == 0

    def _get_best_action(self):
        return max(self._lotteries, key=lambda a: self._get_lottery_utility(self._lotteries[a]))
    
    def _get_lottery_utility(self, lottery):
        return sum(self._get_utility_value(value) * probability for value, probability in lottery.items())
    
    def _get_utility_value(self, value):
        # TODO
        return value

    @staticmethod
    def analyse_action(state, player_color, actions, depth_level, result_queue):
        for action in actions:
            action = tuple(action)
            future_moves = MoveAnalysis(state, action, player_color, depth_level)
            future_moves.start_analysis()
            lottery = future_moves.get_points()
            result_queue.put({action: lottery})


if __name__ == '__main__':
    app = Application('Othello Analysis')
    app.run()
