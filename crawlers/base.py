from __future__ import annotations
from typing import Optional
from typing import List
from typing import Dict
from logging import Logger
from logging import getLogger
from abc import ABC
from abc import abstractmethod
from urllib.parse import urlparse
from urllib.parse import parse_qs
from re import match

from pydantic import BaseModel
from requests import Session
from lxml import etree

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
        'pb': 1024 ** 5
    }

    return int(float(number) * units.get(unit.lower(), 1))

def find_element(html: etree._Element, xpath: str) -> Optional[etree._Element]: # pylint: disable=c-extension-no-member
    elements = html.xpath(xpath)
    return elements[0] if elements else None

class User(BaseModel):
    user_id: str
    user_name: str
    upload_bytes: int
    download_bytes: int
    email: str
    bonus: float

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
    crawler: Base

    class Config:
        arbitrary_types_allowed = True

class Base(ABC):
    def __init__(
        self,
        header_file_path: str,
        proxy: Optional[str] = None,
        logger: Optional[Logger] = None,
        interval: int = 1,
        hr_policy: Optional[Dict[str, int]] = None
    ) -> None:
        self.headers = get_headers(header_file_path)
        self.proxies = {'http': proxy, 'https': proxy} if proxy else {}
        self.logger = logger or getLogger('dummy')
        self.interval = interval
        self.hr_policy = hr_policy or {}

        self.session = Session()
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)

        self.number_pattern = r'\d+([\,]\d+)*([\.]\d+)'
        self.unit_pattern = r'KB|MB|GB|TB|PB'

    @abstractmethod
    def get_user(self) -> User:
        return NotImplemented

    @abstractmethod
    def get_torrents(self, pages: int = 1) -> List[Torrent]:
        return NotImplemented

Torrent.update_forward_refs()
