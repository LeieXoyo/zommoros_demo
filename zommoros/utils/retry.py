import time
from functools import wraps

def retry(method):
        @wraps(method)
        def retry_method(*args, **kwargs):
            for i in range(3):
                time.sleep(2)
                try:
                    return method(*args, **kwargs)
                except:
                    print('Retrying...')
                    if i == 2:
                        raise
        return retry_method
        