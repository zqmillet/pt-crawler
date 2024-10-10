from pytest import fixture
from loguru import logger
from time import time

from crawlers import CHDBits

@fixture(name='header_file_path', scope='session')
def _header_file_path():
    return 'testcases/headers/chdbits.header'

@fixture(name='crawler', scope='session')
def _crawler(header_file_path) -> CHDBits:
    return CHDBits(base_url='https://ptchdbits.co/', header_file_path=header_file_path, logger=logger, qps=0.5)

def test_get_user(crawler):
    now = time()
    user = crawler.get_user()
    escape = time() - now
    assert escape < 1

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
    assert len(crawler.get_torrents(pages=2)) == 200

def test_get_torrent(crawler):
    torrent = crawler.get_torrent('392799')
    print(torrent)

    torrent = crawler.get_torrent('392050')
    print(torrent)
