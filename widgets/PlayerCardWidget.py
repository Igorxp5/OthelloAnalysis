import numpy as np

from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


class PlayerCardWidget(QtWidgets.QGroupBox):
    def __init__(self, player_name='', *args, **kwargs):
        super(PlayerCardWidget, self).__init__(*args, **kwargs)

        self.setFixedHeight(50)
        
        self._layout = QtWidgets.QGridLayout()
        self.setLayout(self._layout)

        self._time_label = QtWidgets.QLabel('00:00')
        self._layout.addWidget(self._time_label, 0, 0, alignment=Qt.AlignVCenter | Qt.AlignLeft)

        self._player_label = QtWidgets.QLabel(player_name)
        self._layout.addWidget(self._player_label, 0, 1, alignment=Qt.AlignCenter)

        self._points_label = QtWidgets.QLabel('0 points')
        self._layout.addWidget(self._points_label, 0, 2, alignment=Qt.AlignVCenter | Qt.AlignRight)

    def set_player_name(self, name):
        self._player_label.setText(str(name) or '')

    def set_time(self, time_):
        self._time_label.setText(str(time_) or '')
    
    def set_points(self, points):
        points = points or 0
        self._points_label.setText(f'{points} points')
