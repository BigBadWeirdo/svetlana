import requests
import logging
import time
import re

from datetime import datetime


class DiplomacyGame(object):
    """Contains information about a WebDiplomacy game."""
    def __init__(self, deadline, defeated, not_ready, ready, won, drawn,
            pregame):
        self.deadline = datetime.fromtimestamp(int(deadline[0])) if deadline \
                else None
        self.defeated = defeated
        self.not_ready = not_ready
        self.ready = ready
        self.won = won[0] if won else None
        self.drawn = drawn
        self.pregame = pregame != []

    @property
    def _timedelta(self):
        """Returns the time until the deadline."""
        return self.deadline - datetime.now()

    @property
    def days_left(self):
        """Returns the number of days left."""
        return self._timedelta.days if self.deadline else None

    @property
    def hours_left(self):
        """Returns the number of hours left."""
        return self._timedelta.seconds//3600 if self.deadline else None

    @property
    def minutes_left(self):
        """Returns the number of minutes left."""
        return (self._timedelta.seconds//60)%60 if self.deadline else None


class WebDiplomacyClient(object):
    """Acts as an interface to the WebDiplomacy website."""
    def __init__(self, url='https://webdiplomacy.net/'):
        self.url = url

    def _request(self, url, timeout=1, threshold=300):
        """Performs a HTTPS request and returns the response body.

        When it fails, it tries again after an increasing timeout until the
        timeout reaches a given threshold.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logging.error('Request failed: "%s" "%s"', url, e)
            time.sleep(timeout)
            self._request(url, timeout=timeout*2)

    def _parse(self, content):
        """Parses the contents of a WebDiplomacy game page.

        Returns a dict with country and game info.

        Note that exceptions are not caught by design, these should be handled
        outside of this function.
        """
        patterns = {
            'defeated':  r'.*memberCountryName.*memberStatusDefeated">(.*?)<.*',
            'drawn':     r'.*memberCountryName.*memberStatusDrawn">(.*?)<.*',
            'ready':     r'.*memberCountryName.*tick.*rStatusPlaying">(.*?)<.*',
            'not_ready': r'.*memberCountryName.*alert.*StatusPlaying">(.*?)<.*',
            'won':       r'.*memberCountryName.*memberStatusWon">(.*?)<.*',
            'deadline':  r'.*gameTimeRemaining.*unixtime="([0-9]+)".*',
            'pregame':   r'.*(memberPreGameList)">.*',
        }
        data = { k: [] for k in patterns }

        for line in content.split('\n'):
            for key, pattern in patterns.items():
                match = re.match(pattern, line.strip())
                if match:
                    current_list = data.get(key, [])
                    data[key] = current_list + [match.group(1)]

        logging.debug('Parsed data: %s', data)

        return data

    def fetch(self, id, endpoint='board.php?gameID={}'):
        """Fetches info from WebDiplomacy, parses it and returns the data."""
        try:
            response = self._request(self.url + endpoint.format(id))
            data = self._parse(response)
            game = DiplomacyGame(**data)
            return game
        except Exception as e:
            logging.error('Problems while fetching data: %s', e)
