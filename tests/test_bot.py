import pytest
import asyncio

from datetime import datetime

from svetlana.bot import DiscordClient, DESCRIPTION
from svetlana.webdiplomacy import DiplomacyGame

MINUTE = 60
HOUR = 60*MINUTE
DAY = 24*HOUR


class MockChannel:
    id = 1

    @asyncio.coroutine
    def send(self, *args, **kwargs):
        return None

class MockAuthor:
    name = 'jhartog'

class MockMessage:
    channel = MockChannel()
    author = MockAuthor()

    def __init__(self, msg):
        self.content = msg

class MockWebDiplomacyClient:
    def __init__(self, data):
        self._response = DiplomacyGame(1, data, 'https://foo.bar/', 'game.php')

    def fetch(self, _):
        return self._response


@pytest.mark.asyncio
async def test_help(mocker, monkeypatch):
    send_spy = mocker.spy(MockMessage.channel, 'send')

    client = DiscordClient(None, ':memory:', False)

    await client.on_message(MockMessage('svetlana help'))
    args, kwargs = send_spy.call_args
    assert args[0] == f'Hello, jhartog!\n{DESCRIPTION}'

@pytest.mark.asyncio
async def test_follow_unfollow_list(mocker, monkeypatch):
    send_spy = mocker.spy(MockMessage.channel, 'send')

    wd_client = MockWebDiplomacyClient({
        'deadline': [str(int(datetime.now().timestamp()))],
        'defeated': [],
        'not_ready': [],
        'ready': [],
        'won': [],
        'drawn': [],
        'pregame': ['foo'],
        'map_link': ['foo.jpg'],
    })
    client = DiscordClient(wd_client, ':memory:', False)

    await client.on_message(MockMessage('svetlana list'))
    args, kwargs = send_spy.call_args
    assert args[0] == "I'm following: []"

    await client.on_message(MockMessage('svetlana follow 1234'))
    args, kwargs = send_spy.call_args
    assert kwargs['embed'].description == 'Now following 1234!'
    assert kwargs['embed'].url == 'https://foo.bar/game.php'
    assert kwargs['embed'].image.url == 'https://foo.bar/foo.jpg'

    await client.on_message(MockMessage('svetlana follow 1234'))
    args, kwargs = send_spy.call_args
    assert kwargs['embed'].description == "I'm already following that game!"

    await client.on_message(MockMessage('svetlana list'))
    args, kwargs = send_spy.call_args
    assert args[0] == "I'm following: [1234]"

    await client.on_message(MockMessage('svetlana unfollow 1234'))
    args, kwargs = send_spy.call_args
    assert args[0] == 'Consider it done!'

    await client.on_message(MockMessage('svetlana unfollow 1234'))
    args, kwargs = send_spy.call_args
    assert args[0] == 'Huh? What game?'

    await client.on_message(MockMessage('svetlana follow 1234a'))
    args, kwargs = send_spy.call_args
    assert args[0] == 'Huh?'

@pytest.mark.asyncio
async def test_poll_pregame(mocker, monkeypatch):
    def _test_days(N):
        wd_client = MockWebDiplomacyClient({
            'deadline': [str(int(datetime.now().timestamp())+N*DAY+MINUTE)],
            'defeated': [],
            'not_ready': [],
            'ready': [],
            'won': [],
            'drawn': [],
            'pregame': ['foo'],
            'map_link': ['foo.jpg'],
        })

        client = DiscordClient(wd_client, ':memory:', False)

        msg = client._poll(None, None)
        assert msg == f'The game starts in {N} days!'

    for N in range(7):
        _test_days(N)

@pytest.mark.asyncio
async def test_poll_two_hours_left_ready(mocker, monkeypatch):
    wd_client = MockWebDiplomacyClient({
        'deadline': [str(int(datetime.now().timestamp())+2*HOUR+MINUTE)],
        'defeated': [],
        'not_ready': [],
        'ready': [],
        'won': [],
        'drawn': [],
        'pregame': [],
        'map_link': ['foo.jpg'],
    })

    client = DiscordClient(wd_client, ':memory:', False)

    msg = client._poll(None, None)
    assert msg == "Two hours left, everybody's ready!"

@pytest.mark.asyncio
async def test_poll_two_hours_left_not_ready(mocker, monkeypatch):
    wd_client = MockWebDiplomacyClient({
        'deadline': [str(int(datetime.now().timestamp())+2*HOUR+MINUTE)],
        'defeated': [],
        'not_ready': ['Turkey', 'France'],
        'ready': [],
        'won': [],
        'drawn': [],
        'pregame': [],
        'map_link': ['foo.jpg'],
    })

    client = DiscordClient(wd_client, ':memory:', False)

    msg = client._poll(None, None)
    assert msg == "Two hours left! These countries aren't ready: Turkey, France"

@pytest.mark.asyncio
async def test_poll_drawn(mocker, monkeypatch):
    wd_client = MockWebDiplomacyClient({
        'deadline': [str(int(datetime.now().timestamp()))],
        'defeated': [],
        'not_ready': [],
        'ready': [],
        'won': [],
        'drawn': ['France', 'Russia'],
        'pregame': [],
        'map_link': ['foo.jpg'],
    })

    client = DiscordClient(wd_client, ':memory:', False)

    msg = client._poll(None, None)
    assert msg == 'The game was a draw between France, Russia!'

@pytest.mark.asyncio
async def test_poll_won(mocker, monkeypatch):
    wd_client = MockWebDiplomacyClient({
        'deadline': [str(int(datetime.now().timestamp()))],
        'defeated': [],
        'not_ready': [],
        'ready': [],
        'won': ['Russia'],
        'drawn': [],
        'pregame': [],
        'map_link': ['foo.jpg'],
    })

    client = DiscordClient(wd_client, ':memory:', False)

    msg = client._poll(None, None)
    assert msg == 'Russia has won!'

@pytest.mark.asyncio
async def test_poll_new_round(mocker, monkeypatch):
    wd_client = MockWebDiplomacyClient({
        'deadline': [str(int(datetime.now().timestamp())+DAY)],
        'defeated': [],
        'not_ready': [],
        'ready': [],
        'won': [],
        'drawn': [],
        'pregame': [],
        'map_link': ['foo.jpg'],
    })

    client = DiscordClient(wd_client, ':memory:', False)

    msg = client._poll(None, None)
    assert msg == 'Starting new round! Good luck :)'

