from selenium.webdriver.chrome.webdriver import WebDriver


class SeleniumNetworkScraper:
    def __init__(self, driver: WebDriver):
        self._driver = driver

    def get_events(self) -> list:
        """
        :return: Get webdriver logs
        """

        return self._driver.get_log('performance')

    def listen_for_event(self, params: dict) -> any:
        """
        :param params: Parameters to filter event by, keys should match the ones in your devtools
        :return: Waits and returns and event that matches the supplied parameters
        """

        while True:
            event = self.find_event(self.get_events(), params)

            if not event:
                continue

            return event

    def find_event(self, events: list, params: dict) -> any:
        for event in events:
            if not self.match_params(event, params):
                continue

            return event

    @staticmethod
    def match_params(event: dict, params: dict) -> bool:
        for k in params:
            if params[k] != event.get(k):
                return False

        return True
