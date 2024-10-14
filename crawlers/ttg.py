from re import match
from math import inf
from typing import List
from typing import Dict
from typing import Optional
from http import HTTPStatus
from logging import Logger

from lxml import etree # pylint: disable=c-extension-no-member

from pydantic import ValidationError

from .base import Crawler
from .base import User
from .base import Torrent
from .base import Task
from .base import Promotion
from .base import get_id_from_href
from .base import find_element
from .base import Status
from .base import calculate_bytes
from .base import convert_to_bytes
from .exceptions import CannotGetUserInformationException
from .exceptions import CannotGetTorrentInformationException
from .exceptions import RequestException

def get_promotion(element: Optional[etree._Element]) -> Promotion: # pylint: disable=c-extension-no-member
    src = element.get('src') if element is not None else None

    if src == '/pic/ico_free.gif':
        return Promotion(upload_ratio=1, download_ratio=0)

    if src == '/pic/ico_30.gif':
        return Promotion(upload_ratio=1, download_ratio=0.3)

    if src == '/pic/ico_half.gif':
        return Promotion(upload_ratio=1, download_ratio=0.5)

    return Promotion(upload_ratio=1, download_ratio=1)
class TTG(Crawler):
    def __init__(
        self,
        headers: Dict[str, str],
        base_url: str = 'https://totheglory.im/',
        proxy: Optional[str] = None,
        logger: Optional[Logger] = None,
        qps: float = inf,
        hr_policy: Optional[Dict[str, int]] = None,
    ) -> None:
        super().__init__(
            headers=headers,
            base_url=base_url,
            proxy=proxy,
            logger=logger,
            qps=qps
        )

    def get_user(self) -> User:
        pattern = r'[\s\S]*'.join(
            [
                '',
                rf'上传量 :  (?P<upload_number>{self.number_pattern}) (?P<upload_unit>{self.unit_pattern})\xa0\xa0',
                rf'下载量 : (?P<download_number>{self.number_pattern}) (?P<download_unit>{self.unit_pattern})\xa0\xa0',
                rf'积分 : (?P<bonus>{self.number_pattern})\xa0\xa0'
            ]
        )

        response = self.session.get(
            url=self.base_url + '/my.php',
        )

        html = etree.HTML(response.content.decode('utf8')) # pylint: disable=c-extension-no-member

        email_element = find_element(html, '//*[@id="main_table"]/tr[1]/td/table/tr[2]/td/form/table/tr[5]/td[2]')
        passkey_element = find_element(html, '//*[@id="main_table"]/tr[1]/td/table/tr[2]/td/form/table/tr[6]/td[2]')
        title_element = find_element(html, '/html/body/table[2]/tr/td/table/tr/td[1]')
        user_id_element = find_element(html, '//*[@id="main_table"]/tr[1]/td/h1/a')

        if email_element is None or user_id_element is None or title_element is None or passkey_element is None:
            raise CannotGetUserInformationException()

        result = match(pattern, ''.join(title_element.itertext()))
        if not result:
            raise CannotGetUserInformationException()

        user_id = get_id_from_href(user_id_element.get('href'))
        if not user_id:
            raise CannotGetUserInformationException()

        return User(
            user_id=user_id,
            user_name=user_id_element.text,
            upload_bytes=calculate_bytes(result.group('upload_number'), result.group('upload_unit')),
            download_bytes=calculate_bytes(result.group('download_number'), result.group('download_unit')),
            email=email_element.text,
            bonus=float(result.group('bonus')),
            passkey=passkey_element.text
        )

    def get_torrents(self, pages: int = 1) -> List[Torrent]:
        torrents = []

        for page in range(pages):
            response = self.session.get(url=self.base_url + '/browse.php', params={'c': 'M', 'page': str(page)})
            if not response.status_code == HTTPStatus.OK:
                raise RequestException(response)

            html = etree.HTML(response.content.decode('utf8')) # pylint: disable=c-extension-no-member
            _, *rows = html.xpath('/html/body/table[3]/tr[1]/td/form/table/tr')
            for row in rows:
                torrent_id_element = find_element(row, './td[2]/div[1]/a')
                title_element = find_element(row, './td[2]/div[1]/a/b')
                size_element = find_element(row, './td[7]')
                seeders_and_leechers_element = find_element(row, './td[9]')

                if torrent_id_element is None or title_element is None or size_element is None or seeders_and_leechers_element is None:
                    self.logger.warning(CannotGetTorrentInformationException())
                    continue

                torrent_id_result = match(r'/t/(?P<torrent_id>.+)/', torrent_id_element.get('href') or '')
                size = convert_to_bytes(' '.join(size_element.itertext()))

                seeders_and_leechers_result = match(r'(?P<seeders>\d+)/\n(?P<leechers>\d+)', ''.join(seeders_and_leechers_element.itertext()))
                if not size or not torrent_id_result or not seeders_and_leechers_result or torrent_id_element is None or seeders_and_leechers_element is None:
                    self.logger.warning(CannotGetTorrentInformationException())
                    continue

                promotion_element = find_element(row, './/img[starts-with(@src, "/pic/ico_")]')
                hit_and_run_element = find_element(row, './/img[@title="Hit and Run"]')

                try:
                    torrent = Torrent(
                        torrent_id=torrent_id_result.group('torrent_id'),
                        torrent_name=title_element.text,
                        size=size,
                        seeders=seeders_and_leechers_result.group('seeders'),
                        leechers=seeders_and_leechers_result.group('leechers'),
                        hit_and_run=60 * 3600 if hit_and_run_element is not None else 0,
                        promotion=get_promotion(promotion_element),
                        crawler=self,
                    )
                except ValidationError as exception:
                    self.logger.warning(exception)
                    continue
                else:
                    torrents.append(torrent)

        return torrents

    def get_torrent(self, torrent_id: str) -> Torrent:
        response = self.session.get(self.base_url + f'/t/{torrent_id}/')
        if not response.status_code == HTTPStatus.OK:
            raise RequestException(response)

        html = etree.HTML(response.content.decode('utf8')) # pylint: disable=c-extension-no-member

        title_element = find_element(html, '//*[@id="main_table"]/tr[1]/td/h1')
        size_element = find_element(html, "//td[preceding-sibling::td[1][text()='尺寸']]")
        seeders_and_leechers_element = find_element(html, "//td[preceding-sibling::td[1][text()='活跃用户']]")

        if title_element is None or size_element is None or seeders_and_leechers_element is None:
            raise CannotGetTorrentInformationException()

        size_result = match(rf'(?P<size_number>{self.number_pattern}) (?P<size_unit>{self.unit_pattern})', size_element.text)
        seeders_and_leechers_result = match(r'(?P<seeders>.+) 做种者，(?P<leechers>.+) 下载者', ''.join(seeders_and_leechers_element.itertext()))
        if not size_result or not seeders_and_leechers_result:
            raise CannotGetTorrentInformationException()

        hit_and_run_element = find_element(html, './/img[@alt="Hit & Run"]')
        promotion_element = find_element(html, './/img[starts-with(@src, "/pic/ico_")]')

        return Torrent(
            torrent_id=torrent_id,
            torrent_name=title_element.text,
            size=calculate_bytes(size_result.group('size_number'), size_result.group('size_unit')),
            seeders=seeders_and_leechers_result.group('seeders'),
            leechers=seeders_and_leechers_result.group('leechers'),
            hit_and_run=60 * 3600 if hit_and_run_element is not None else 0,
            promotion=get_promotion(promotion_element),
            crawler=self,
        )

    def download_torrent(self, torrent_id: str, file_path: str) -> bool:
        response = self.session.get(self.base_url + f'/t/{torrent_id}/')
        if not response.status_code == HTTPStatus.OK:
            self.logger.warning(RequestException(response))
            return False

        html = etree.HTML(response.content.decode('utf8')) # pylint: disable=c-extension-no-member
        download_url_element = find_element(html, '//*[@id="main_table"]/tr[1]/td/table[1]/tr[1]/td[2]/a[1]')
        if download_url_element is None:
            self.logger.warning(CannotGetTorrentInformationException())
            return False

        href = download_url_element.get('href')
        if download_url_element is None:
            self.logger.warning(CannotGetTorrentInformationException())
            return False

        response = self.session.get(self.base_url + href)
        if not response.status_code == HTTPStatus.OK:
            self.logger.warning(RequestException(response))
            return False

        with open(file_path, 'wb') as file:
            file.write(response.content)
            return True

    def get_tasks(self) -> List[Task]:
        user = self.get_user()

        response = self.session.get(self.base_url + '/userdetails.php', params={'id': user.user_id})
        if not response.status_code == HTTPStatus.OK:
            raise RequestException(response)

        html = etree.HTML(response.content.decode('utf8')) # pylint: disable=c-extension-no-member

        tasks = []
        for keyword, status in [('当前上传', Status.SEEDING), ('当前下载', Status.LEECHING)]:
            try:
                _, *rows = html.xpath(f'''//td[preceding-sibling::td[1][text()={repr(keyword)}]]//tr''')
            except ValueError:
                continue

            for row in rows:
                title_element = find_element(row, './/td[2]/a/b')
                link_element = find_element(row, './/td[2]/a')

                if title_element is None or link_element is None:
                    self.logger.warning(CannotGetTorrentInformationException())
                    continue

                torrent_id = get_id_from_href(self.base_url + link_element.get('href', '/'))
                tasks.append(Task(torrent_id=torrent_id, torrent_name=title_element.text, status=status))
        return tasks
