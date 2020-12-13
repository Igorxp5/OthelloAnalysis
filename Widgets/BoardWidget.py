import numpy as np

from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


class BoardWidget(QtWidgets.QWidget):
    def __init__(self, board_size=8, size=500, *args, **kwargs):
        super(BoardWidget, self).__init__(*args, **kwargs)
        self.setContentsMargins(0, 0, 0, 0)
        
        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        
        self._board = np.zeros((board_size, board_size), dtype=int)
        self._size = size
        self._board_size = board_size
        board_image = self.get_board_image(self._board, self._size)
        
        self._image_label = QtWidgets.QLabel(self)
        self._layout.addWidget(self._image_label)
        self.setLayout(self._layout)
        self.set_board(self._board)
    
        self._image_label.setMouseTracking(True)
        self._image_label.mouseMoveEvent = self._mouseMoveEvent
        self._image_label.mouseReleaseEvent = self.leaveEvent

        self._hover_square = None
        self._hover_callback = None
    
    def get_size(self):
        return self._size, self._size
    
    def get_board_size(self):
        return self._board_size
    
    def set_board(self, board, highlight_squares=None):
        self._board = board
        board_image = self.get_board_image(self._board, self._size, 
                                           highlight_squares=highlight_squares)
        self._pix_widget = QtGui.QPixmap.fromImage(ImageQt(board_image))
        self._image_label.setPixmap(self._pix_widget)
    
    def register_square_hover_callback(self, callback):
        self._hover_callback = callback

    def _mouseMoveEvent(self, event):
        col =  event.x() // (self._size // self._board_size)
        row = event.y() // (self._size // self._board_size)
        hover_square = row, col
        if hover_square != self._hover_square:
            self._hover_square = hover_square
            self._hover_callback(self._hover_square)
    
    def leaveEvent(self, event):
        self._hover_square = None
        self._hover_callback(self._hover_square)

    @staticmethod
    def get_board_image(board, size, background_color='#4ac236', square_stroke=2, 
                        piece_stroke=2, stroke_color='#000000', piece_white_color='#ffffff', 
                        piece_black_color='#000000', highlight_squares=None):
        rows, cols = board.shape
        image = Image.new(mode='RGBA', size=(size, size))
        draw = ImageDraw.Draw(image)

        square_size = (size / rows)
        piece_padding = 5
        piece_size = square_size - (2 * piece_padding)  
        for row in range(rows):
            for col in range(cols):
                # Draw square
                x1 = row * square_size
                y1 = col * square_size
                x2 = x1 + square_size
                y2 = y1 + square_size
                
                square_color = background_color
                if highlight_squares and (col, row) in highlight_squares:
                    square_color = highlight_squares[(col, row)]

                draw.rectangle((x1, y1, x2, y2), fill=square_color, 
                               width=square_stroke, outline=stroke_color)
                
                # Draw piece
                if board[col, row] != 0:
                    x1 = x1 + piece_padding
                    y1 = y1 + piece_padding
                    x2 = x2 - piece_padding
                    y2 = y2 - piece_padding
                    color = piece_black_color if board[col, row] == 1 else piece_white_color
                    draw.ellipse((x1, y1, x2, y2), fill=color, 
                                width=piece_stroke, outline=stroke_color)
        
        # Board border
        draw.line((0, square_stroke - 1, size, square_stroke - 1), fill=stroke_color, width=square_stroke)
        draw.line((square_stroke - 1, 0, square_stroke - 1, size), fill=stroke_color, width=square_stroke)
        draw.line((0, size - square_stroke - 1, size, size - square_stroke - 1), fill=stroke_color, width=square_stroke)
        draw.line((size - square_stroke - 1, 0, size - square_stroke - 1, size), fill=stroke_color, width=square_stroke)

        return image

if __name__ == '__main__':
    board = np.zeros((8, 8), dtype=int)
    board[3][3] = -1
    board[3][4] = 1
    board[4][3] = 1
    board[4][4] = -1
    image = BoardWidget.get_board_image(board, 400, highlight_squares={(0, 1): '#6edb5c'})
    image.show()
