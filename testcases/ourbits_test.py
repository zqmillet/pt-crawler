from typing import Dict
from os import environ
from time import time
from tempfile import NamedTemporaryFile

from pytest import fixture
from loguru import logger
from torrent_parser import parse_torrent_file

from crawlers import OurBits

@fixture(name='headers', scope='session')
def _headers() -> Dict[str, str]:
    headers = {}
    for line in environ['OURBITS_HEADERS'].splitlines():
        key, value = line.split(': ', 1)
        headers[key] = value
    return headers

@fixture(name='crawler', scope='session')
def _crawler(headers, proxy) -> OurBits:
    return OurBits(headers=headers, logger=logger, qps=0.5, proxy=proxy)

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
    for torrent in torrents:
        print(torrent)
    assert len(torrents) == 100

    assert len(crawler.get_torrents(pages=2)) == 200

def test_get_torrent(crawler):
    torrent = crawler.get_torrent('279088')
    print(torrent)

    torrent = crawler.get_torrent('279130')
    print(torrent)

def test_download_torrent(crawler):
    with NamedTemporaryFile('wb') as file:
        crawler.download_torrent('279088', file.name)

        title = parse_torrent_file(file.name)['info']['name']
        print(title)
        assert title

    with NamedTemporaryFile('wb') as file:
        torrent = crawler.get_torrent('279130')
        torrent.save(file.name)

        title = parse_torrent_file(file.name)['info']['name']
        print(title)
        assert title

def test_get_tasks(crawler):
    tasks = crawler.get_tasks()
    for task in tasks:
        print(task)
