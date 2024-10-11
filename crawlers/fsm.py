from math import inf
from typing import List
from typing import Optional
from typing import Dict
from logging import Logger
from http import HTTPStatus

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator
from pydantic import ValidationError

from .base import Crawler
from .base import Torrent
from .base import Status
from .base import User
from .base import Task
from .base import convert_to_bytes
from .base import Promotion
from .exceptions import RequestException

class Peers(BaseModel):
    upload: int
    download: int

class TorrentStatus(BaseModel):
    download_ratio: float = Field(alias='downCoefficient')
    upload_ratio: float = Field(alias='upCoefficient')

class TaskItem(BaseModel):
    torrent_id: str = Field(alias='tid')
    torrent_name: str = Field(alias='title')

class TaskData(BaseModel):
    items: List[TaskItem] = Field(alias='list')
    total_pages: int = Field(alias='maxPage')

class ListTaskResponse(BaseModel):
    data: TaskData

class TorrentItem(BaseModel):
    torrent_id: str = Field(alias='tid')
    torrent_name: str = Field(alias='title')
    size: str = Field(alias='fileSize')
    peers: Peers
    promotion: TorrentStatus = Field(alias='status')

    @validator('size')
    def size_validator(cls, value: str) -> int:
        result = convert_to_bytes(value)
        if not result:
            raise ValueError(f'Invalid size {value}')
        return result

    @validator('promotion')
    def promotion_validator(cls, value: TorrentStatus) -> Promotion:
        return Promotion(upload_ratio=value.upload_ratio, download_ratio=value.download_ratio)

class TorrentList(BaseModel):
    items: List[TorrentItem] = Field(alias='list')

class ListTorrentsResponse(BaseModel):
    data: TorrentList

class UserData(BaseModel):
    upload_bytes: int = Field(alias='upload')
    download_bytes: int = Field(alias='download')
    user_id: str = Field(alias='uid')
    user_name: str = Field(alias='username')
    bonus: float = Field(alias='point')
    passkey: str

class GetUserResponse(BaseModel):
    data: UserData

class GetTorrentData(BaseModel):
    torrent: TorrentItem

class GetTorrentResponse(BaseModel):
    data: GetTorrentData

class FSM(Crawler):
    def __init__(
        self,
        headers: Dict[str, str],
        base_url: str = 'https://fsm.name',
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

    def get_torrents(self, pages: int = 1) -> List[Torrent]:
        torrents = []

        for page in range(pages):
            response = self.session.get(
                url=self.base_url + '/api/Torrents/listTorrents',
                params={
                    'type': '0',
                    'systematics': '0',
                    'tags': '[]',
                    'keyword': '',
                    'page': str(page + 1)
                }
            )

            if not response.status_code == HTTPStatus.OK:
                raise RequestException(response)

            list_torrents_response = ListTorrentsResponse.parse_obj(response.json())
            for item in list_torrents_response.data.items:
                try:
                    torrent = Torrent(
                        torrent_id=item.torrent_id,
                        torrent_name=item.torrent_name,
                        size=item.size,
                        hit_and_run=False,
                        promotion=item.promotion,
                        seeders=item.peers.upload,
                        leechers=item.peers.download,
                        crawler=self
                    )
                except ValidationError as exception:
                    self.logger.warning(exception)
                    continue
                else:
                    torrents.append(torrent)

        return torrents

    def get_user(self) -> User:
        response = self.session.get(self.base_url + '/api/Users/infos')
        if not response.status_code == HTTPStatus.OK:
            raise RequestException(response)

        get_user_response: GetUserResponse = GetUserResponse.parse_obj(response.json())

        return User(
            user_id=get_user_response.data.user_id,
            user_name=get_user_response.data.user_name,
            email=None,
            upload_bytes=get_user_response.data.upload_bytes,
            download_bytes=get_user_response.data.download_bytes,
            bonus=get_user_response.data.bonus,
            passkey=get_user_response.data.passkey
        )

    def get_torrent(self, torrent_id: str) -> Torrent:
        response = self.session.get(
            url=self.base_url + '/api/Torrents/details',
            params={'tid': torrent_id}
        )

        if not response.status_code == HTTPStatus.OK:
            raise RequestException(response)

        get_torrent_response: GetTorrentResponse = GetTorrentResponse.parse_obj(response.json())
        item = get_torrent_response.data.torrent

        return Torrent(
            torrent_id=item.torrent_id,
            torrent_name=item.torrent_name,
            size=item.size,
            hit_and_run=False,
            promotion=item.promotion,
            seeders=item.peers.upload,
            leechers=item.peers.download,
            crawler=self
        )

    def download_torrent(self, torrent_id: str, file_path: str) -> bool:
        user = self.get_user()

        response = self.session.get(
            url='https://api.fsm.name/Torrents/download',
            params={'passkey': user.passkey, 'tid': torrent_id, 'source': 'direct'}
        )

        if not response.status_code == HTTPStatus.OK:
            self.logger.warning(RequestException(response))
            return False

        with open(file_path, 'wb') as file:
            file.write(response.content)
            return True

    def get_tasks(self) -> List[Task]:
        page = 1
        tasks = []
        for api_path, status in [('/api/Torrents/listMyDownload', Status.LEECHING), ('/api/Torrents/listMySeed', Status.SEEDING)]:
            while True:
                response = self.session.get(self.base_url + api_path, params={'page': str(page)})

                if not response.status_code == HTTPStatus.OK:
                    self.logger.warning(RequestException(response))

                list_tasks_response: ListTaskResponse = ListTaskResponse.parse_obj(response.json())

                for item in list_tasks_response.data.items:
                    tasks.append(Task(torrent_id=item.torrent_id, torrent_name=item.torrent_name, status=status))

                if page >= list_tasks_response.data.total_pages:
                    break

                page += 1
        return tasks
