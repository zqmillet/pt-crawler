from typing import Dict
from os import environ
from time import time
from tempfile import NamedTemporaryFile

from pytest import fixture
from loguru import logger
from torrent_parser import parse_torrent_file

from crawlers import TTG

@fixture(name='headers', scope='session')
def _headers() -> Dict[str, str]:
    headers = {}
    for line in environ['TTG_HEADERS'].splitlines():
        key, value = line.split(': ', 1)
        headers[key] = value
    return headers

@fixture(name='crawler', scope='session')
def _crawler(headers) -> TTG:
    return TTG(headers=headers, logger=logger, qps=0.5)

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
    assert len(crawler.get_torrents()) == 100
    torrents = crawler.get_torrents(pages=2)
    assert len(torrents) == 200

    for torrent in torrents:
        if torrent.hit_and_run > 0:
            print(torrent)

def test_get_torrent(crawler):
    torrent = crawler.get_torrent('688981')
    print(torrent)

    torrent = crawler.get_torrent('688424')
    print(torrent)

def test_download_torrent(crawler):
    with NamedTemporaryFile('wb') as file:
        crawler.download_torrent('688424', file.name)
        title = parse_torrent_file(file.name)['info']['name']
        print(title)
        assert title

    with NamedTemporaryFile('wb') as file:
        torrent = crawler.get_torrent('688424')
        torrent.save(file.name)
        title = parse_torrent_file(file.name)['info']['name']
        print(title)
        assert title

def test_get_tasks(crawler):
    tasks = crawler.get_tasks()
    for task in tasks:
        print(task)
