from re import match

from lxml import etree # pylint: disable=c-extension-no-member

from .base import Base
from .base import User
from .base import get_id_from_href
from .base import find_element
from .base import calculate_bytes
from .exceptions import CannotGetUserInformationException

class CHDBits(Base):
    def get_user(self) -> User:
        pattern = r'[\s\S]*'.join(
            [
                r'欢迎回来, (?P<user_name>.+)  \[退出\]',
                fr'\[使用\]: (?P<bonus>{self.number_pattern}) 邀请',
                fr'上传量： (?P<upload>{self.number_pattern}) (?P<upload_unit>{self.unit_pattern})',
                fr'下载量： (?P<download>{self.number_pattern}) (?P<download_unit>{self.unit_pattern})'
            ]
        )

        response = self.session.get(url='https://ptchdbits.co/usercp.php')

        html = etree.HTML(response.text) # pylint: disable=c-extension-no-member

        email_element = find_element(html, '//*[@id="outer"]/table[2]/tr[2]/td[2]')
        user_id_element = find_element(html, '//*[@id="info_block"]/tr/td/table/tr/td[1]/span/span/a')
        title_element = find_element(html, '//*[@id="info_block"]/tr/td/table/tr/td[1]/span')

        if email_element is None or user_id_element is None or title_element is None:
            raise CannotGetUserInformationException()

        result = match(pattern, ''.join(title_element.itertext()))
        if not result:
            raise CannotGetUserInformationException()

        user_id = get_id_from_href(user_id_element.get('href'))
        if not user_id:
            raise CannotGetUserInformationException()

        return User(
            user_id=user_id,
            user_name=result.group('user_name'),
            upload_bytes=calculate_bytes(result.group('upload'), result.group('upload_unit')),
            download_bytes=calculate_bytes(result.group('download'), result.group('download_unit')),
            email=email_element.text,
            bonus=float(result.group('bonus').replace(',', ''))
        )
