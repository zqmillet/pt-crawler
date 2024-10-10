from math import inf
from time import time
from time import sleep

from requests import Session as BaseSession

class Session(BaseSession):
    def __init__(self, *args, qps: float = inf, **kwargs): # type: ignore
        super().__init__(*args, **kwargs)
        self.interval = 1 / qps
        self.last_request_time = time() - self.interval

    def request(self, *args,**kwargs): # type: ignore
        sleep_time = max(self.last_request_time + self.interval - time(), 0)
        sleep(sleep_time)

        response = super().request(*args, **kwargs)
        self.last_request_time = time()
        return response
