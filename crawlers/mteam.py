from typing import List

from .base import Base
from .base import User
from .base import Torrent
from .base import Task
from .base import Promotion
from .base import get_id_from_href
from .base import find_element
from .base import Status
from .base import calculate_bytes
from .base import convert_to_bytes

class MTeam(Base):
    def get_user(self) -> User:
        response = self.session.post(
            # url=self.base_url + '/api/member/profile',
            url='https://api.m-team.cc/api/member/profile'
        )
        breakpoint()


    def get_torrents(self, pages: int = 1) -> List[Torrent]:
        pass

    def get_torrent(self, torrent_id: str) -> Torrent:
        pass

    def download_torrent(self, torrent_id: str, file_path: str) -> bool:
        pass

    def get_tasks(self) -> List[Task]:
        pass
