from selenium.webdriver.chrome.webdriver import WebDriver
import json
import time


class ScraperException(Exception):
    pass


class ElementNotFound(ScraperException):
    pass


class SeleniumNetworkScraper:
    def __init__(self, driver: WebDriver):
        self._driver = driver

    def get_events(self) -> list:
        """
        :return: Get webdriver logs
        """

        logs = self._driver.get_log('performance')

        return list(map(lambda log: json.loads(log['message']), logs))

    def listen_for_event(self, params: dict, timeout: int) -> any:
        """
        :param params: Parameters to filter event by, keys should match the ones in your devtools
        :param timeout: Duration in seconds to listen for event
        :return: Waits and returns and event that matches the supplied parameters
        """

        start_time = time.time()

        while True:
            if isinstance(timeout, int) and time.time() - start_time > timeout:
                raise ElementNotFound('Could not find element in the specified timeout period.')

            try:
                event = self.find_event(self.get_events(), params)

                return event

            except ElementNotFound:
                continue

    def find_event(self, events: list, params: dict) -> any:
        """
        :param events: List of events in log format
        :param params: Parameters to filter event by, keys should match the ones in your devtools
        :return: Event that matches supplied conditions
        :raises ElementNotFound: If event with supplied conditions isn't located
        """

        for event in events:
            if not self.check_params_match(event, params):
                continue

            return event

        raise ElementNotFound('Could not find event with supplied parameters.')

    @staticmethod
    def check_params_match(event: dict, params: dict) -> bool:
        """
        :param event: Event to check matches parameters
        :param params: Parameters to check event against
        :return: True if matches, else False
        """

        for k in params:
            if params[k] != event.get(k):
                return False

        return True
