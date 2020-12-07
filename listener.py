import re
import numpy as np

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, \
    UnexpectedAlertPresentException, StaleElementReferenceException

from enum import Enum, auto
from threading import Thread, Event

from typing import Callable, Dict, List, Tuple


_listeners: Dict['OthelloListenerCallback', Callable] = {}
_listeners_cache: Dict['OthelloListenerCallback', Tuple] = {}


class ListenerCallback(Enum):
    USER_LOGGED = auto()
    IN_ROOM = auto()
    IN_GAME = auto()
    CURRENT_PLAYER = auto()
    PLAYERS = auto()
    PLAYER_COLOR = auto()
    BOARD = auto()
    POINTS = auto()
    PLAYERS_TIME = auto()
    IS_FINISHED = auto()


class ListenerCallbackRegister:
    def register_listener(type_: ListenerCallback):
        global _listeners
        def decorator(function):
            _listeners[type_] = function
            def wrapper(*args, **kwargs):
                try:
                    return function(*args, **kwargs)
                except UnexpectedAlertPresentException:
                    return None
                except StaleElementReferenceException:
                    return None
            return wrapper
        return decorator
    
    @register_listener(ListenerCallback.USER_LOGGED)
    def _user_logged_listener(driver):
        try:
            driver.find_element_by_xpath('//body[not(contains(@class, "not_logged_user"))]')
            return driver.execute_script('return document.getElementById("connected_username").innerText')
        except NoSuchElementException:
            return None

    @register_listener(ListenerCallback.IN_ROOM)
    def _in_room_logged_listener(driver):
        return bool(re.match(r'.+/table\?table=\d+', driver.current_url))
    
    @register_listener(ListenerCallback.IN_GAME)
    def _in_game_logged_listener(driver):
        return bool(re.match(r'.+/reversi\?table=\d+', driver.current_url))
    
    @register_listener(ListenerCallback.CURRENT_PLAYER)
    def _current_player_logged_listener(driver):
        xpath = '//*[contains(@class, "current-player-board")]//*[contains(@class, "player-name")]//a'
        try:
            element = driver.find_element_by_xpath(xpath)
            return element and element.text
        except NoSuchElementException:
            return None
    
    @register_listener(ListenerCallback.PLAYERS)
    def _players_logged_listener(driver):
        xpath = '//*[contains(@class, "player-name")]//a'
        try:
            elements = driver.find_elements_by_xpath(xpath)
            return tuple([element.text for element in elements])
        except NoSuchElementException:
            return None
    
    @register_listener(ListenerCallback.BOARD)
    def _board_listener(driver):
        try:
            xpath = '//*[contains(@class, "player-name")]//a'
            logged_player_style = driver.find_element_by_xpath(xpath).get_attribute('style')
            if logged_player_style == 'color: rgb(0, 0, 0);':
                logged_player_color = '#000000'
            else:
                logged_player_color = '#ffffff'
            board = np.zeros((8, 8), dtype=int).tolist()
            discs_root = driver.find_element_by_id('discs')
            discs = {}
            for disc_el in discs_root.find_elements_by_class_name('disc'):
                player = '#ffffff' if 'disccolor_ffffff' in disc_el.get_attribute('class') else '#000000'
                position = disc_el.get_attribute('id').split('_')[1]
                position = int(position[1]) - 1, int(position[0]) - 1
                board[position[0]][position[1]] = 1 if player == logged_player_color else -1
            return board
        except NoSuchElementException:
            return None
    
    @register_listener(ListenerCallback.POINTS)
    def _points_listener(driver):
        try:
            players = driver.find_elements_by_xpath('//*[contains(@class, "player-name")]//a')
            players = [p.text for p in players]
            points = driver.execute_script('return Array.prototype.map.call(document.querySelectorAll(".player_score_value"),(item) => item.innerText)')
            points = map(int, points)
            return dict(zip(players, points))
        except NoSuchElementException:
            return None

    @register_listener(ListenerCallback.PLAYERS_TIME)
    def _players_time_listener(driver):
        try:
            players = driver.find_elements_by_xpath('//*[contains(@class, "player-name")]//a')
            players = [p.text for p in players]
            times = driver.execute_script('return Array.prototype.map.call(document.querySelectorAll(".timeToThink"),(item) => item.innerText)')
            return dict(zip(players, times))
        except NoSuchElementException:
            return None
    
    @register_listener(ListenerCallback.PLAYER_COLOR)
    def _player_color_listener(driver):
        try:
            xpath = '//*[contains(@class, "player-name")]//a'
            logged_player_style = driver.find_element_by_xpath(xpath).get_attribute('style')
            return '#000000' if logged_player_style == 'color: rgb(0, 0, 0);' else '#ffffff'
        except NoSuchElementException:
            return None

    @register_listener(ListenerCallback.IS_FINISHED)
    def _is_finished_listener(driver):
        try:
            driver.find_element_by_id('createNew_btn')
            return True
        except NoSuchElementException:
            return None


class OthelloListener(Thread):
    HOME_PAGE = 'https://en.boardgamearena.com/account'
    
    def __init__(self):
        self._driver = None
        self._stop_event = Event()
        self._callbacks: Dict[OthelloListenerCallback, List[Callable]] = {}
        super().__init__(daemon=True)

    def run(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--lang=en')
        self._driver = webdriver.Chrome(executable_path='./chromedriver', options=options)
        self._driver.get(OthelloListener.HOME_PAGE)

        self._listener()

        self._driver.quit()

    def register_callback(self, type_: 'OthelloListenerCallback', callback: Callable):
        if type_ not in self._callbacks:
            self._callbacks[type_] = []
        self._callbacks[type_].append(callback)
    
    def unregister_callback(self, callback: Callable):
        self._callbacks[type_].remove(callback)

    def _listener(self):
        global _listeners_cache

        while not self._stop_event.is_set():
            for type_, listener in _listeners.items():
                if type_ in self._callbacks:
                    result = listener(self._driver)
                    callback_params = tuple([type_] + [result])
                    if result is not None and _listeners_cache.get(type_) != callback_params:
                        for callback in self._callbacks[type_]:
                            Thread(target=callback, args=callback_params, daemon=True).start()
                    _listeners_cache[type_] = callback_params


def callback(event, result):
    print(f'Event: {event}. Result: {repr(result)}')


if __name__ == '__main__':
    listener = OthelloListener()
    listener.start()

    listener.register_callback(ListenerCallback.USER_LOGGED, callback)
    listener.register_callback(ListenerCallback.IN_ROOM, callback)
    listener.register_callback(ListenerCallback.CURRENT_PLAYER, callback)
    listener.register_callback(ListenerCallback.BOARD, callback)
    listener.register_callback(ListenerCallback.POINTS, callback)
    listener.register_callback(ListenerCallback.PLAYERS, callback)
    listener.register_callback(ListenerCallback.PLAYER_COLOR, callback)
    listener.register_callback(ListenerCallback.PLAYERS_TIME, callback)
    listener.register_callback(ListenerCallback.IS_FINISHED, callback)

    while True:
        pass
