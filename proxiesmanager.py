from config import CONFIG
from http.server import BaseHTTPRequestHandler, HTTPServer
from proxyset import ProxySet
import threading

class ProxiesManager:
    def __init__(self, proxyset: ProxySet):
        class ProxyModifyRequestHandler(BaseHTTPRequestHandler):
            def do_PUT(self):
                try:
                    with open('proxies.txt') as f:
                        proxyset.renew_proxies({line.rstrip('\n') for line in f})
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(str(e).encode('utf-8'))
                    return
                self.send_response(200)
                self.end_headers()

            def do_POST(self):
                self.send_response(200)
                self.end_headers()
                for proxy in proxyset.get_blocked_proxies():
                    self.wfile.write(proxy.encode('utf-8'))
                    self.wfile.write(b'\n')

            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                for proxy in proxyset.get_avail_proxies():
                    self.wfile.write(proxy.encode('utf-8'))
                    self.wfile.write(b'\n')

        self.handler = ProxyModifyRequestHandler

    def start(self):
        httpd = HTTPServer((CONFIG['server_address'], CONFIG['server_port']), self.handler)
        threading.Thread(target=lambda: httpd.serve_forever(), daemon=True).start()
