from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from enum import Enum, auto
from threading import Thread, Event

from typing import Callable, Dict, List, Tuple


_listeners: Dict['OthelloListenerCallback', Callable] = {}
_listeners_cache: Dict['OthelloListenerCallback', Tuple] = {}


class ListenerCallback(Enum):
    USER_LOGGED = auto()


class ListenerCallbackRegister:
    def register_listener(type_: ListenerCallback):
        global _listeners
        def decorator(function):
            _listeners[type_] = function
            return function
        return decorator
    
    @register_listener(ListenerCallback.USER_LOGGED)
    def _user_logged_listener(driver):
        try:
            driver.find_element_by_xpath('//body[not(contains(@class, "not_logged_user"))]')
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
                    if not isinstance(result, tuple):
                        result = (result,)
                    if result is not None and _listeners_cache.get(type_) != result:
                        _listeners_cache[type_] = result
                        for callback in self._callbacks[type_]:
                            Thread(target=callback, args=result, daemon=True).start()


def callback(event):
    print(f'Event: {event}')


if __name__ == '__main__':
    listener = OthelloListener()
    listener.start()

    listener.register_callback(ListenerCallback.USER_LOGGED, callback)

    while True:
        pass
