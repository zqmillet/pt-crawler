from re import match
from typing import List
from typing import Optional
from http import HTTPStatus

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

promotion_map = {
    'free': Promotion(upload_ratio=1, download_ratio=0),
    'twoup': Promotion(upload_ratio=2, download_ratio=1),
    'twoupfree': Promotion(upload_ratio=2, download_ratio=0),
    'halfdown': Promotion(upload_ratio=1, download_ratio=0.5),
    'twouphalfdown': Promotion(upload_ratio=2, download_ratio=0.5),
    'thirtypercent': Promotion(upload_ratio=1, download_ratio=0.3),
}

def get_promotion_from_list(element: Optional[etree._Element]) -> Promotion: # pylint: disable=c-extension-no-member
    clazz = element.get('class') if element is not None else 'normal'
    if clazz == 'pro_free':
        return Promotion(upload_ratio=1, download_ratio=0)
    if clazz == 'pro_50pctdown':
        return Promotion(upload_ratio=1, download_ratio=0.5)
    if clazz == 'pro_2up':
        return Promotion(upload_ratio=2, download_ratio=1)
    if clazz == 'pro_free2up':
        return Promotion(upload_ratio=2, download_ratio=0)
    if clazz == 'pro_50pctdown2up':
        return Promotion(upload_ratio=2, download_ratio=0.5)
    if clazz == 'pro_30pctdown':
        return Promotion(upload_ratio=1, download_ratio=0.3)
    return Promotion(upload_ratio=1, download_ratio=1)

def get_promotion_from_detail(element: Optional[etree._Element]) -> Promotion: # pylint: disable=c-extension-no-member
    clazz = element.get('class') if element is not None else 'normal'
    return promotion_map.get(clazz, Promotion(upload_ratio=1, download_ratio=1))

class OurBits(Crawler):
    base_url: str = 'https://ourbits.club'

    def get_user(self) -> User:
        pattern = r'.*'.join(
            [
                r'欢迎回来, (?P<user_name>.+) \[退出\]',
                rf'魔力值 \[使用\]: (?P<bonus>{self.number_pattern}) ',
                rf'上传量： (?P<upload_number>{self.number_pattern}) (?P<upload_unit>{self.unit_pattern}) ',
                rf'下载量： (?P<download_number>{self.number_pattern}) (?P<download_unit>{self.unit_pattern}) '
                ''
            ]
        )

        response = self.session.get(url=self.base_url + '/usercp.php', timeout=self.timeout)
        if not response.status_code == HTTPStatus.OK:
            raise RequestException(response)

        html = etree.HTML(response.text) # pylint: disable=c-extension-no-member

        email_element = find_element(html, "//td[preceding-sibling::td[1][text()='邮箱地址']]")
        passkey_element = find_element(html, "//td[preceding-sibling::td[1][text()='密钥']]")
        user_id_element = find_element(html, '//*[@id="info_block"]/tr/td/table/tr/td[1]/span/span[1]/a')
        title_element = find_element(html, '//*[@id="info_block"]/tr/td/table/tr/td[1]/span')

        if email_element is None or user_id_element is None or title_element is None or passkey_element is None:
            raise CannotGetUserInformationException()

        result = match(pattern, ' '.join(''.join(title_element.itertext()).split()))
        if not result:
            raise CannotGetUserInformationException()

        user_id = get_id_from_href(user_id_element.get('href'))
        if not user_id:
            raise CannotGetUserInformationException()

        return User(
            user_id=user_id,
            user_name=result.group('user_name'),
            upload_bytes=calculate_bytes(result.group('upload_number'), result.group('upload_unit')),
            download_bytes=calculate_bytes(result.group('download_number'), result.group('download_unit')),
            email=email_element.text,
            bonus=float(result.group('bonus').replace(',', '')),
            passkey=''.join(passkey_element.itertext())
        )

    def get_torrents(self, pages: int = 1) -> List[Torrent]:
        torrents = []
        for page in range(pages):
            response = self.session.get(
                url=self.base_url + '/torrents.php',
                params={'page': str(page), 'incldead': '0', 'spstate': '0'},
                timeout=self.timeout
            )

            if not response.status_code == HTTPStatus.OK:
                raise RequestException(response)

            html = etree.HTML(response.text) # pylint: disable=c-extension-no-member
            _, *rows = html.xpath('//*[@id="torrenttable"]/tr')

            for row in rows:
                title_element = find_element(row, 'td[2]/table/tr/td[1]/a')
                size_element = find_element(row, 'td[5]')
                seeders_element = find_element(row, 'td[6]')
                leechers_element = find_element(row, 'td[7]')
                promotion_element = find_element(row, './/img[starts-with(@class, "pro_")]')

                if title_element is None or size_element is None or seeders_element is None or leechers_element is None:
                    self.logger.warning(CannotGetTorrentInformationException())
                    continue

                torrent_id = get_id_from_href(title_element.get('href'))
                size = convert_to_bytes(' '.join(size_element.itertext()))

                if not torrent_id or not size:
                    self.logger.warning(CannotGetTorrentInformationException())
                    continue

                try:
                    torrent = Torrent(
                        torrent_id=torrent_id,
                        torrent_name=''.join(title_element.itertext()).strip(),
                        size=size,
                        seeders=int(''.join(seeders_element.itertext()).replace(',', '')),
                        leechers=int(''.join(leechers_element.itertext()).replace(',', '')),
                        hit_and_run=False,
                        promotion=get_promotion_from_list(promotion_element),
                        crawler=self,
                    )
                except ValidationError as exception:
                    self.logger.warning(exception)
                else:
                    torrents.append(torrent)

        return torrents

    def get_torrent(self, torrent_id: str) -> Torrent:
        response = self.session.get(
            url=self.base_url + '/details.php',
            params={'hit': '1', 'id': torrent_id}
        )

        if not response.status_code == HTTPStatus.OK:
            raise RequestException(response)

        html = etree.HTML(response.text) # pylint: disable=c-extension-no-member

        title_element = find_element(html, '//*[@id="top"]')
        size_element = find_element(html, "//td[preceding-sibling::td[1][text()='基本信息']]")
        seeder_and_leecher_element = find_element(html, "//td[preceding-sibling::td[1][text()='同伴']]")
        promotion_element = find_element(title_element, './/font[@class="free" or @class="twoup" or @class="twoupfree" or @class="halfdown" or @class="twouphalfdown" or @class="thirtypercent"]')

        if title_element is None or size_element is None or seeder_and_leecher_element is None:
            raise CannotGetTorrentInformationException()

        result = match('大小：(?P<size>.+) 类型', ' '.join(''.join(size_element.itertext()).split()))
        if not result:
            raise CannotGetTorrentInformationException()

        size = convert_to_bytes(result.group('size'))
        torrent_name = title_element.text.strip()

        result = match(r'(?P<seeder_number>.+)个做种者\|(?P<leecher_number>.+)个下载者', ''.join(item.strip() for item in list(seeder_and_leecher_element.itertext())))
        if not result or not size:
            raise CannotGetTorrentInformationException()

        return Torrent(
            torrent_id=torrent_id,
            torrent_name=torrent_name,
            size=size,
            seeders=int(result.group('seeder_number')),
            leechers=int(result.group('leecher_number')),
            promotion=get_promotion_from_detail(promotion_element),
            crawler=self,
            hit_and_run=False
        )

    def download_torrent(self, torrent_id: str, file_path: str) -> bool:
        response = self.session.get(
            url=self.base_url + '/download.php',
            params={'id': torrent_id}
        )

        if not response.status_code == HTTPStatus.OK:
            self.logger.warning(RequestException(response))
            return False

        with open(file_path, 'wb') as file:
            file.write(response.content)
            return True

    def get_tasks(self) -> List[Task]:
        user = self.get_user()
        tasks = []

        for status in [Status.LEECHING, Status.SEEDING]:
            response = self.session.get( # pylint: disable = missing-timeout
                url=self.base_url + '/getusertorrentlistajax.php',
                params={'userid': user.user_id, 'type': status},
                timeout=self.timeout
            )

            if not response.status_code == HTTPStatus.OK:
                self.logger.warning(RequestException(response))
                continue

            html = etree.HTML(response.text) # pylint: disable = c-extension-no-member

            try:
                _, *rows = html.xpath('//tr')
            except ValueError:
                continue

            for row in rows:
                title_element = find_element(row, 'td[2]/a')
                href = title_element.get('href') or '' if title_element is not None else ''
                torrent_id = get_id_from_href(href)
                torrent_name = title_element.get('title') if title_element is not None else ''

                if not torrent_name or not torrent_id:
                    self.logger.warning('2333')
                    continue

                tasks.append(Task(torrent_id=torrent_id, torrent_name=torrent_name, status=status))

        return tasks
