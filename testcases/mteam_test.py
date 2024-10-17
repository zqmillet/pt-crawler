from typing import Dict
from os import environ
from time import time
from tempfile import NamedTemporaryFile

from pytest import fixture
from loguru import logger
from torrent_parser import parse_torrent_file

from crawlers import MTeam
from crawlers.base import Status

@fixture(name='headers', scope='session')
def _headers() -> Dict[str, str]:
    headers = {}
    for line in environ['MTEAM_HEADERS'].splitlines():
        key, value = line.split(': ', 1)
        headers[key] = value
    return headers

@fixture(name='crawler', scope='session', params = ['normal', 'adult'])
def _crawler(headers, request) -> MTeam:
    return MTeam(headers=headers, logger=logger, qps=0.5, mode=request.param)

def test_get_user(crawler):
    user = crawler.get_user()

    now = time()
    user = crawler.get_user()
    escape = time() - now
    assert escape > 2

    now = time()
    user = crawler.get_user()
    escape = time() - now
    assert escape > 2

    print(user)

def test_get_torrents(crawler):
    torrents = crawler.get_torrents()
    print(torrents[0])
    assert len(torrents) == 100
    assert len(crawler.get_torrents()) == 100
    assert len(crawler.get_torrents(pages=2)) == 200

def test_get_torrent(crawler):
    torrent = crawler.get_torrent('777698')
    print(torrent)

    torrent = crawler.get_torrent('777466')
    print(torrent)

def test_download_torrent(crawler):
    with NamedTemporaryFile('wb') as file:
        crawler.download_torrent('777698', file.name)
        title = parse_torrent_file(file.name)['info']['name']
        assert title

    with NamedTemporaryFile('wb') as file:
        torrent = crawler.get_torrent('777698')
        torrent.save(file.name)

        title = parse_torrent_file(file.name)['info']['name']
        assert title

def test_get_tasks(crawler):
    tasks = crawler.get_tasks()
    print(len([item for item in tasks if item.status == Status.SEEDING]))
    print(len([item for item in tasks if item.status == Status.LEECHING]))

    tasks = crawler.get_tasks(page_size=10)
    print(len([item for item in tasks if item.status == Status.SEEDING]))
    print(len([item for item in tasks if item.status == Status.LEECHING]))
