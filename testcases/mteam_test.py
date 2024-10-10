from tempfile import NamedTemporaryFile

from pytest import fixture
from loguru import logger
from libtorrent import torrent_info

from crawlers import MTeam

@fixture(name='header_file_path', scope='session')
def _header_file_path():
    return 'testcases/headers/mteam.header'

@fixture(name='crawler', scope='session')
def _crawler(header_file_path) -> MTeam:
    return MTeam(base_url='https://api.m-team.cc', header_file_path=header_file_path, logger=logger, qps=0.5)

def test_get_user(crawler):
    user = crawler.get_user()
