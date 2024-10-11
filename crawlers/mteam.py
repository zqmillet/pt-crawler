from typing import List
from typing import Dict
from typing import Optional
from http import HTTPStatus
from math import inf
from logging import Logger

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator
from pydantic import ValidationError

from .base import Crawler
from .base import User
from .base import Task
from .base import Torrent
from .base import Status
from .base import Promotion
from .exceptions import RequestException

class SearchItemStatus(BaseModel):
    seeders: int
    leechers: int
    promotion: Promotion = Field(alias='discount')

    @validator('promotion', pre=True)
    def promotion_validator(cls, value: str) -> Promotion:
        if value == 'FREE':
            return Promotion(upload_ratio=1, download_ratio=0)

        if value == 'PERCENT_50':
            return Promotion(upload_ratio=1, download_ratio=0.5)

        if value == 'PERCENT_70':
            return Promotion(upload_ratio=1, download_ratio=0.3)

        if value == 'NORMAL':
            return Promotion(upload_ratio=1, download_ratio=1)

        return Promotion(upload_ratio=1, download_ratio=1)

class TaskTorrent(BaseModel):
    id: str
    name: str

class TaskItem(BaseModel):
    torrent: TaskTorrent

class TaskData(BaseModel):
    items: List[TaskItem] = Field(alias='data')
    page_number: int = Field(alias='pageNumber')
    total_pages: int = Field(alias='totalPages')

class TaskResponse(BaseModel):
    code: str
    message: str
    data: TaskData

class SearchItem(BaseModel):
    name: str
    size: int
    id: str
    status: SearchItemStatus

class SearchData(BaseModel):
    items: List[SearchItem] = Field(alias='data')

class SearchResponse(BaseModel):
    code: str
    message: str
    search_data: SearchData = Field(alias='data')

class MemberCount(BaseModel):
    upload_bytes: int = Field(alias='uploaded')
    download_bytes: int = Field(alias='downloaded')
    bonus: float

class ProfileData(BaseModel):
    user_id: str = Field(alias='id')
    user_name: str = Field(alias='username')
    email: str
    member_count: MemberCount = Field(alias='memberCount')

class ProfileResponse(BaseModel):
    code: str
    message: str
    data: ProfileData

class TorrentData(BaseModel):
    id: str
    name: str
    size: int
    status: SearchItemStatus

class TorrentResponse(BaseModel):
    code: str
    message: str
    data: TorrentData

class DITokenResponse(BaseModel):
    code: str
    message: str
    download_url: str = Field(alias='data')

class MTeam(Crawler):
    def __init__(
        self,
        headers: Dict[str, str],
        base_url: str = 'https://api.m-team.cc',
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
            response = self.session.post(
                url=self.base_url + '/api/torrent/search',
                json={
                    'mode': 'normal',
                    'categories': [],
                    'visible': 1,
                    'pageNumber': page + 1,
                    'pageSize': 100,
                }
            )

            if not response.status_code == HTTPStatus.OK:
                raise RequestException(response)

            search_response: SearchResponse = SearchResponse.parse_raw(response.text)
            for item in search_response.search_data.items:
                try:
                    torrent = Torrent(
                        torrent_id=item.id,
                        torrent_name=item.name,
                        size=item.size,
                        hit_and_run=False,
                        promotion=item.status.promotion,
                        seeders=item.status.seeders,
                        leechers=item.status.leechers,
                        crawler=self,
                    )
                except ValidationError as exception:
                    self.logger.warning(exception)
                else:
                    torrents.append(torrent)

        return torrents

    def get_user(self) -> User:
        response = self.session.post(
            url=self.base_url + '/api/member/profile',
        )

        if not response.status_code == HTTPStatus.OK:
            raise RequestException(response)

        profile_response: ProfileResponse = ProfileResponse.parse_raw(response.text)
        return User(
            user_id=profile_response.data.user_id,
            user_name=profile_response.data.user_name,
            email=profile_response.data.email,
            upload_bytes=profile_response.data.member_count.upload_bytes,
            download_bytes=profile_response.data.member_count.download_bytes,
            bonus=profile_response.data.member_count.bonus,
        )

    def get_torrent(self, torrent_id: str) -> Torrent:
        response = self.session.post(self.base_url + '/api/torrent/detail', data={'id': torrent_id})

        if not response.status_code == HTTPStatus.OK:
            raise RequestException(response)

        torrent_response: TorrentResponse = TorrentResponse.parse_raw(response.text)
        return Torrent(
            torrent_id=torrent_response.data.id,
            torrent_name=torrent_response.data.name,
            size=torrent_response.data.size,
            hit_and_run=False,
            promotion=torrent_response.data.status.promotion,
            seeders=torrent_response.data.status.seeders,
            leechers=torrent_response.data.status.leechers,
            crawler=self
        )

    def download_torrent(self, torrent_id: str, file_path: str) -> bool:
        response = self.session.post(self.base_url + '/api/torrent/genDlToken', data={'id': torrent_id})

        if not response.status_code == HTTPStatus.OK:
            self.logger.warning(RequestException(response))
            return False

        di_token_response: DITokenResponse = DITokenResponse.parse_raw(response.text)
        response = self.session.get(di_token_response.download_url)

        if not response.status_code == HTTPStatus.OK:
            self.logger.warning(RequestException(response))
            return False

        with open(file_path, 'wb') as file:
            file.write(response.content)
            return True

    def get_tasks(self, page_size: int = 100) -> List[Task]:
        tasks = []
        user = self.get_user()

        for status in [Status.SEEDING, Status.LEECHING]:
            page_number = 1

            while True:
                response = self.session.post(
                    url=self.base_url + '/api/member/getUserTorrentList',
                    json={
                        "userid": user.user_id,
                        "type": status.upper(),
                        "pageNumber": page_number,
                        "pageSize": page_size
                    }
                )

                if not response.status_code == HTTPStatus.OK:
                    raise RequestException(response)

                task_response: TaskResponse = TaskResponse.parse_raw(response.text)
                for item in task_response.data.items:
                    task = Task(
                        torrent_id=item.torrent.id,
                        torrent_name=item.torrent.name,
                        status=status
                    )
                    tasks.append(task)

                if task_response.data.total_pages == page_number:
                    break

                page_number += 1

        return tasks
