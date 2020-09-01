from config import CONFIG
import crawler
import logging
from proxiesmanager import ProxiesManager
from proxyset import ProxySet
import requests
from requests.exceptions import RequestException
from resultwriter import ResultWriter
import threading
from utils import gen_ranges

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

rw = ResultWriter()
ps = ProxySet()

def crawl_range(start, end):
    session = requests.Session()
    proxy = ps.get_proxy()

    for thread_id in range(start, end):
        page = 1

        while True:
            try:
                lines, has_next = crawler.crawl_page(session, proxy, thread_id, page)
            except crawler.Lihkg404RequestException:
                # If 404, this thread has been removed, so we move on to the next thread
                logging.info('Page %d/%d proxy %s responses 404', thread_id, page, proxy)
                break
            except crawler.Lihkg429RequestException as e:
                # If 429, the proxy is rate-limited and should sleep for some time
                logging.info('Page %d/%d proxy %s responses 429, retry after %d', thread_id, page, proxy, e.retry_after)
                ps.block_proxy_for(proxy, e.retry_after)
                proxy = ps.get_proxy()
                session = requests.Session()
                continue
            except crawler.Lihkg403RequestException:
                # If 403, the proxy is blocked and should no longer be used
                logging.info('Page %d/%d proxy %s responses 403', thread_id, page, proxy)
                ps.block_proxy(proxy)
                proxy = ps.get_proxy()
                session = requests.Session()
                continue
            except RequestException as e:
                logging.info('Page %d/%d proxy %s error %s', thread_id, page, proxy, str(e))
                ps.block_proxy(proxy)
                proxy = ps.get_proxy()
                session = requests.Session()
                continue

            rw.write_lines(lines)  # Write results to file
            logging.info('Wrote %d lines from page %d/%d', len(lines), thread_id, page)

            if has_next:
                page += 1  # Same thread, go to next page
            else:
                break  # Move on to the next thread

if __name__ == '__main__':
    pm = ProxiesManager(ps)
    pm.start()

    ts = []

    for start, end in gen_ranges(CONFIG['first_post'], CONFIG['last_post'], CONFIG['thread_count']):
        t = threading.Thread(target=crawl_range, args=(start, end))
        t.start()
        ts.append(t)

    for t in ts:
        t.join()  # Wait until all tasks have finished

    logging.info('Done')
