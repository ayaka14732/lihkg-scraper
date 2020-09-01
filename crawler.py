import logging
import random
import requests
from requests.exceptions import RequestException
from sanitize import sanitize

DEFAULT_HEADER = \
    { 'Accept': 'application/json'
    , 'Accept-Language': 'en'
    , 'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'
    , 'Host': 'lihkg.com'
    , 'TE': 'trailers'
    , 'X-LI-DEVICE': 'a56d070d211c2acb3f4beb2e6f9160ac4f957ef9'
    , 'X-LI-DEVICE-TYPE': 'browser'
    }

def make_url(thread_id, page):
    return 'https://lihkg.com/api_v2/thread/%d/page/%d?order=reply_time' % (thread_id, page)

def make_referer(thread_id, page):
    return 'https://lihkg.com/thread/%d/page/%d' % (thread_id, page)

class Lihkg403RequestException(RequestException):
    pass

class Lihkg404RequestException(RequestException):
    pass

class Lihkg429RequestException(RequestException):
    def __init__(self, retry_after, *args, **kwargs):
        self.retry_after = retry_after
        super().__init__(*args, **kwargs)

def crawl_page(session: requests.Session, proxy, thread_id, page):
    url = make_url(thread_id, page)
    headers = \
        { **DEFAULT_HEADER
        , 'Referer': make_referer(thread_id, page)
        , 'X-LI-LOAD-TIME': '4.3%06d' % random.randrange(0, 1000000)
        }

    try:
        logging.info('Retreiving page %s with proxy %s', url, proxy)
        r = session.get(url, headers=headers, proxies={'https': proxy}, timeout=300)
    except RequestException as e:
        raise e
    if r.status_code == 403:
        raise Lihkg403RequestException
    elif r.status_code == 404:
        raise Lihkg404RequestException
    elif r.status_code == 429:
        # If no Retry-After is specified in header, default to 5 min
        retry_after = int(r.headers.get('Retry-After', 300))
        raise Lihkg429RequestException(retry_after)
    elif not r.ok:
        raise RequestException

    obj = r.json()
    if obj['success'] != 1:
        return [], False

    resp = obj['response']

    if resp['cat_id'] == '32':  # 黑 洞
        return [], False

    lines = [text for item in resp['item_data'] for text in sanitize(item['msg'])]
    has_next = page < resp['total_page']

    return lines, has_next
