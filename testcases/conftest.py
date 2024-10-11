from pytest import fixture

def pytest_addoption(parser):
    parser.addoption(
        '--proxy',
        action='store',
        type=str,
        help='specify the proxy',
        default=None
    )

@fixture(name='proxy', scope='session')
def _proxy(request):
    return request.config.getoption('proxy')
