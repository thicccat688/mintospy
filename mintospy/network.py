from selenium.webdriver.chrome.webdriver import WebDriver
import json


class SeleniumNetworkScraper:
    def __init__(self, driver: WebDriver):
        self._driver = driver

    def get_events(self) -> list:
        logs = self._get_logs()

        network_responses = []

        for log in logs:
            body = self._driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': log['params']['requestId']})

            network_responses.append(json.loads(body))

        return network_responses

    def parse_event(self, event: dict) -> any:
        return [o for o in self._parse_event_gen(event)]

    def _get_logs(self) -> list:
        raw_logs = self._driver.get_log('performance')

        return [self.parse_event(log) for log in raw_logs]

    def _parse_event_gen(self, event: dict) -> any:
        for (k, v) in event.items():
            if isinstance(v, dict):
                yield from self.parse_event(v)

        return json.loads(event['message'])['message']
