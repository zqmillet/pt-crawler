from re import match

from lxml import etree

from .base import Base
from .base import User
from .base import get_id_from_href
from .base import find_element
from .base import convert_to_bytes

class CHDBits(Base):
    def get_user(self) -> User:
        pattern = r'[\s\S]*'.join(
            [
                fr'欢迎回来, (?P<user_name>.+)  \[退出\]',
                fr'\[使用\]: (?P<bonus>{self.number_pattern}) 邀请',
                fr'上传量： (?P<upload>{self.number_pattern}) (?P<upload_unit>{self.unit_pattern})',
                fr'下载量： (?P<download>{self.number_pattern}) (?P<download_unit>{self.unit_pattern})'
            ]
        )

        response = self.session.get(url='https://ptchdbits.co/usercp.php')

        html = etree.HTML(response.text)

        email_element = find_element(html, '//*[@id="outer"]/table[2]/tr[2]/td[2]')
        user_id_element = find_element(html, '//*[@id="info_block"]/tr/td/table/tr/td[1]/span/span/a')
        title_element = find_element(html, '//*[@id="info_block"]/tr/td/table/tr/td[1]/span')

        if not all(item is not None for item in [email_element, user_id_element, title_element]):
            self.logger.warning('Failed to find user information')
            return None

        result = match(pattern, ''.join(title_element.itertext()))
        if not result:
            self.logger.warning('Failed to match user information')
            return None

        return User(
            user_id=get_id_from_href(user_id_element.get('href')),
            user_name=result.group('user_name'),
            upload_bytes=convert_to_bytes(f"{result.group('upload')} {result.group('upload_unit')}"),
            download_bytes=convert_to_bytes(f"{result.group('download')} {result.group('download_unit')}"),
            email=email_element.text,
            bonus=float(result.group('bonus').replace(',', ''))
        )
