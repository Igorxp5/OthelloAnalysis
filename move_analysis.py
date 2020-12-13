import numpy as np

from Othello import OthelloGame, OthelloPlayer, BoardView

from threading import Thread, Event


class MoveAnalysis(Thread):
    def __init__(self, state, move, current_player, count_future_moves):
        self.state = np.copy(state)
        self.move = move

        self.player = current_player
        self.count_future_moves = count_future_moves
        self.points_before = OthelloGame.get_board_players_points(self.state)[self.player]

        self._has_finished = False
        self._points = {}
        self._stop_event = Event()
        self._result = None

        super().__init__(daemon=True)
    
    def run(self):
        if self.start_analysis():
            self._result = self._points
            self._stop_event.set()

    def stop(self):
        self._stop_event.set()

    def has_finished(self):
        return self._has_finished

    def get_result(self):
        self._stop_event.wait()
        return self._result

    def start_analysis(self):
        OthelloGame.flip_board_squares(self.state, self.player, *self.move)

        # Checar se o adversário tem jogada ou se acabou o jogo
        current_player = self.player.opponent
        can_new_player_play = OthelloGame.has_player_actions_on_board(self.state, current_player)

        if not can_new_player_play:
            can_previous_player_play = OthelloGame.has_player_actions_on_board(self.state, current_player.opponent)

            if not can_previous_player_play:
                points_now =  OthelloGame.get_board_players_points(self.state)[self.player]
                # adicionando no dicionario
                self._points[points_now - self.points_before] = self._points.get(points_now - self.points_before, 0) + 1
                return self._points
            else:
                current_player = current_player.opponent

        return self.future_moves(self.state, current_player, count=0)


    def future_moves(self, state, current_player, count):
        if count == self.count_future_moves or self.has_finished():
            return True
        else:
            count += 1
            possible_moves = OthelloGame.get_player_valid_actions(state, current_player)
            for move in possible_moves:
                if self._stop_event.is_set():
                    return False

                board = np.copy(state)
                OthelloGame.flip_board_squares(board, current_player, *move)
                # Checar se o adversário tem jogada ou se acabou o jogo
                new_player = current_player.opponent
                can_new_player_play = OthelloGame.has_player_actions_on_board(board, new_player)

                if not can_new_player_play:
                    can_previous_player_play = OthelloGame.has_player_actions_on_board(board, new_player.opponent)

                    if not can_previous_player_play:
                        self._has_finished = True
                    else:
                        new_player = new_player.opponent 

                if count == self.count_future_moves or self.has_finished():
                    points_now =  OthelloGame.get_board_players_points(board)[self.player]
                    self._points[points_now - self.points_before] = self._points.get(points_now - self.points_before, 0) + 1
                    
                self.future_moves(board, new_player, count)
            return True


if __name__ == "__main__":
    state = np.array([[[False,  False],
        [False, False],
        [False,  False],
        [False,  False],
        [False,  False],
        [False,  False]],

       [[False,  False],
        [False,  False],
        [ False, False],
        [ False, False],
        [ False, False],
        [False,  False]],

       [[False,  False],
        [False,  False],
        [ True, False],
        [ False, True],
        [ False, False],
        [False,  False]],

       [[False,  False],
        [False, False],
        [False,  True],
        [True,  False],
        [False,  False],
        [False,  False]],

       [[False, False],
        [ False, False],
        [ False, False],
        [ False, False],
        [ False, False],
        [False,  False]],

       [[False, False],
        [ False, False],
        [False, False],
        [False, False],
        [False, False],
        [False, False]]])

    #game = OthelloGame(8)
    #state = game.board(BoardView.TWO_CHANNELS)
    
    current_player = OthelloPlayer.BLACK
    move = (3,2)
    count = 3

    future_moves = MoveAnalysis(state, move, current_player, count)
    future_moves.start()
    dicio = future_moves.get_result()
    print(f"O dicionário final {dicio}")