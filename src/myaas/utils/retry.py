import random
import time


class RetryPolicy(object):
    def __init__(self, maxtries, delay=None, exceptions=(Exception,)):
        if delay is None:
            # 100ms +/- 50ms of randomized jitter
            self.delay = lambda i: 0.1 + ((random.random() - 0.5) / 10)
        else:
            self.delay = lambda i: delay

        self.maxtries = maxtries
        self.exceptions = exceptions

    def __call__(self, function):
        for i in range(0, self.maxtries):
            try:
                return function()
            except self.exceptions as error:
                last_exception = error
                time.sleep(self.delay(i))
        raise last_exception
