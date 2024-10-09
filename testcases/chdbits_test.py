from pytest import fixture
from loguru import logger

from crawlers import CHDBits

@fixture(name='header_file_path')
def _header_file_path():
    return 'testcases/headers/chdbits.header'

@fixture(name='crawler')
def _crawler(header_file_path) -> CHDBits:
    return CHDBits(header_file_path=header_file_path, logger=logger)

def test_interval(crawler):
    assert crawler.interval == 1

def test_get_user(crawler):
    user = crawler.get_user()
    print(user)
