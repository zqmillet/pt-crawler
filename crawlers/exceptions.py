from requests import Response

class CannotGetUserInformationException(Exception):
    def __init__(self) -> None:
        super().__init__('cannot get user information')

class RequestException(Exception):
    def __init__(self, response: Response) -> None:
        super().__init__(f'request error: {response.status_code} {response.reason}')

class CannotGetTorrentInformationException(Exception):
    def __init__(self) -> None:
        super().__init__('cannot get torrent information')
