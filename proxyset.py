import random
import threading
import time
from typing import Set

class ProxySet:
    def __init__(self):
        with open('proxies.txt') as f:
            self.proxies_avail = {line.rstrip('\n') for line in f}
        self.proxies_banned = set()
        self.cv_proxies_avail = threading.Condition()
        self.lock_proxies_banned = threading.Lock()

    def get_proxy(self):
        with self.cv_proxies_avail:
            self.cv_proxies_avail.wait_for(lambda: len(self.proxies_avail) > 0)
            return random.choice(list(self.proxies_avail))

    def add_proxy(self, proxy):
        with self.lock_proxies_banned:
            self.proxies_banned.discard(proxy)
        with self.cv_proxies_avail:
            self.proxies_avail.add(proxy)
            self.cv_proxies_avail.notify_all()

    def block_proxy(self, proxy):
        with self.cv_proxies_avail:
            self.proxies_avail.discard(proxy)
        with self.lock_proxies_banned:
            self.proxies_banned.add(proxy)

    def _block_proxy_for_inner(self, proxy, duration):
        time.sleep(duration)
        self.add_proxy(proxy)

    def block_proxy_for(self, proxy, duration):
        self.block_proxy(proxy)
        threading.Thread(target=self._block_proxy_for_inner, args=(proxy, duration), daemon=True).start()

    def renew_proxies(self, proxies):
        with self.lock_proxies_banned:
            self.proxies_banned -= proxies
        with self.cv_proxies_avail:
            self.proxies_avail |= proxies
            self.cv_proxies_avail.notify_all()

    def get_blocked_proxies(self) -> Set[str]:
        with self.lock_proxies_banned:
            return set(self.proxies_banned)

    def get_avail_proxies(self) -> Set[str]:
        with self.cv_proxies_avail:
            return set(self.proxies_avail)
