from math import inf
from time import time
from time import sleep

from requests import Session as BaseSession
from requests.adapters import HTTPAdapter as BaseHTTPAdapter


class HTTPAdapter(BaseHTTPAdapter):
    def __init__(self, timeout: int, *args, **kwargs): # type: ignore
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, *args, **kwargs): # type: ignore
        kwargs['timeout'] = kwargs.get('timeout', self.timeout)
        return super().send(*args, **kwargs)

class Session(BaseSession):
    def __init__(self, *args, qps: float = inf, timeout: int = 1, **kwargs): # type: ignore
        super().__init__(*args, **kwargs)
        self.mount('http://', HTTPAdapter(timeout=timeout))
        self.mount('https://', HTTPAdapter(timeout=timeout))
        self.interval = 1 / qps
        self.last_request_time = time() - self.interval

    def request(self, *args,**kwargs): # type: ignore
        sleep_time = max(self.last_request_time + self.interval - time(), 0)
        sleep(sleep_time)

        response = super().request(*args, **kwargs)
        self.last_request_time = time()
        return response
