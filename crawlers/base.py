from __future__ import annotations

from typing import Optional
from typing import List
from typing import Dict
from logging import Logger
from logging import getLogger
from abc import ABC
from abc import abstractmethod
from enum import Enum
from urllib.parse import urlparse
from urllib.parse import parse_qs
from re import match

from pydantic import BaseModel
from pydantic import Field
from lxml import etree

from .session import Session

def format_size(size: int) -> str:
    units = ['KB', 'MB', 'GB', 'TB', 'PB']
    for index, unit in enumerate(units, start=1):
        if size / 1024 ** index < 1024:
            return f'{size / 1024 ** index:.2f} {unit}'
    return 'Error Size'

def get_headers(header_file_path: str) -> Dict[str, str]:
    with open(header_file_path, 'r', encoding='utf8') as file:
        headers = {}
        for line in file.readlines()[1:]:
            key, value = line.strip().split(': ', 1)
            headers[key] = value
        return headers

def get_parameters_from_href(href: str) -> Dict[str, List[str]]:
    return parse_qs(urlparse(href).query)

def get_id_from_href(href: str) -> Optional[str]:
    return get_parameters_from_href(href).get('id', [None])[0]

def convert_to_bytes(size: str) -> Optional[int]:
    result = match(r"([0-9\. ]+)([a-zA-Z]+)", size.strip())
    if not result:
        return None

    groups = result.groups()
    if not len(groups) == 2:
        return None

    number, unit = groups
    return calculate_bytes(number, unit)

def calculate_bytes(number: str, unit: str) -> int:
    units: Dict[str, int] = {
        'kb': 1024,
        'mb': 1024 ** 2,
        'gb': 1024 ** 3,
        'tb': 1024 ** 4,
        'pb': 1024 ** 5,
        'kib': 1024,
        'mib': 1024 ** 2,
        'gib': 1024 ** 3,
        'tib': 1024 ** 4,
        'pib': 1024 ** 5
    }

    return int(float(number) * units.get(unit.lower(), 1))

def find_element(html: etree._Element, xpath: str) -> Optional[etree._Element]: # pylint: disable=c-extension-no-member
    elements = html.xpath(xpath)
    return elements[0] if elements else None

class Status(str, Enum):
    LEECHING = 'leeching'
    SEEDING = 'seeding'

class Task(BaseModel):
    torrent_id: str
    torrent_name: str
    status: Status

class User(BaseModel):
    user_id: str
    user_name: str
    upload_bytes: int
    download_bytes: int
    email: Optional[str]
    bonus: float
    passkey: Optional[str] = Field(default=None)

class Promotion(BaseModel):
    upload_ratio: float
    download_ratio: float

class Torrent(BaseModel):
    torrent_id: str
    torrent_name: str
    size: int
    seeders: int
    leechers: int
    hit_and_run: int
    promotion: Promotion
    crawler: Crawler

    class Config:
        arbitrary_types_allowed = True

    def save(self, file_path: str) -> None:
        self.crawler.download_torrent(self.torrent_id, file_path)

    def __repr__(self) -> str:
        return f'<Torrent {self.crawler.__class__.__name__} {self.torrent_id} {self.torrent_name} up/down ' \
            f'{self.seeders}/{self.leechers} promotion {self.promotion.upload_ratio}/{self.promotion.download_ratio} {format_size(self.size)}>'

class Crawler(ABC):
    base_url = ''

    def __init__(
        self,
        headers: Dict[str, str],
        base_url: str = '',
        proxy: Optional[str] = None,
        logger: Optional[Logger] = None,
        qps: float = 1,
        timeout: Optional[float] = None
    ) -> None:
        self.base_url = base_url or self.base_url
        self.headers = headers
        self.proxy = proxy
        self.proxies = {'http': proxy, 'https': proxy} if proxy else {}
        self.logger = logger or getLogger('dummy')
        self.qps = qps
        self.timeout = timeout

        self.session = Session(qps=qps)
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)

        self.number_pattern = r'\d+([\,]\d+)*([\.]\d+)'
        self.unit_pattern = r'KB|MB|GB|TB|PB|KiB|MiB|GiB|TiB|PiB'

    def __repr__(self) -> str:
        return f'<Crawler {self.__class__.__name__} {self.base_url} proxy: {self.proxy}, qps: {self.qps}>'

    @abstractmethod
    def get_user(self) -> User:
        return NotImplemented

    @abstractmethod
    def get_torrents(self, pages: int = 1) -> List[Torrent]:
        return NotImplemented

    @abstractmethod
    def get_torrent(self, torrent_id: str) -> Torrent:
        return NotImplemented

    @abstractmethod
    def download_torrent(self, torrent_id: str, file_path: str) -> bool:
        return NotImplemented

    @abstractmethod
    def get_tasks(self) -> List[Task]:
        return NotImplemented

Torrent.update_forward_refs()
