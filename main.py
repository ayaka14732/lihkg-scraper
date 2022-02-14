import json
import os.path
import random
import signal
import string
import sys
from tqdm import tqdm
from typing import TextIO, Tuple
import zipfile

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def random_string() -> str:
    '''
    Generate a random string that is suitable to be an identifier.
    '''

    length = random.randrange(10, 20)
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def make_filename(from_thread: int) -> str:
    '''
    Create the file name using the format `lihkg-{from_thread}.csv`.
    '''

    filename = f'lihkg-{from_thread}.csv'
    print('INFO: Writing to file', filename)
    return filename

def get_next_page_from_json(obj: object, thread_id: int, page: int) -> Tuple[int, int]:
    '''
    Determine the next `thread_id` and `page` from the JSON object.
    If the current value of `page` is equal to `total_page`, we go to the next thread.
    Otherwise we increment the value of `page`.
    '''

    if 'response' not in obj:
        return thread_id + 1, 1

    total_pages = obj['response'].get('total_page', 0)
    if page >= total_pages:
        return thread_id + 1, 1

    return thread_id, page + 1

def get_resume_position(filename: str, from_thread: int) -> Tuple[int, int]:
    if not os.path.exists(filename):
        return from_thread, 1

    with open(filename) as f:
        for line in f:
            pass  # locate the last line
    thread_id_str, page_str, obj_str = line.rstrip('\n').split('\t')
    thread_id = int(thread_id_str)
    page = int(page_str)
    obj = json.loads(obj_str)  # will throw an exception if the string is not a valid json object

    thread_id_new, page_new = get_next_page_from_json(obj, thread_id, page)
    print('INFO: Resuming from thread', thread_id_new, 'page', page_new)
    return thread_id_new, page_new

def read_command_line() -> Tuple[int, int, str, str, str, str]:
    '''
    Read the command line arguments in a fixed format.
    '''

    from_thread = int(sys.argv[1])
    to_thread = int(sys.argv[2])

    proxy_host = sys.argv[3]
    proxy_port = sys.argv[4]
    proxy_user = sys.argv[5]
    proxy_pass = sys.argv[6]

    return from_thread, to_thread, proxy_host, proxy_port, proxy_user, proxy_pass

def make_proxy_file(proxy_host: str, proxy_port: str, proxy_user: str, proxy_pass: str) -> str:
    '''
    Unfortunately We cannot set proxy with authentication by options directly.
    So we need to write the proxy to a file and ask Chrome to load the file.
    This function creates this file on the disk and returns the file name.
    See https://stackoverflow.com/a/55582859.
    '''

    manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""

    background_js = """
var config = {
    mode: "fixed_servers",
    rules: {
    singleProxy: {
        scheme: "http",
        host: "%s",
        port: %s
    },
    bypassList: ["localhost"]
    }
};

chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}

chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
    {urls: ["<all_urls>"]},
    ['blocking']
);
""" % (proxy_host, proxy_port, proxy_user, proxy_pass)

    plugin_file = 'proxy_auth_plugin_' + random_string() + '.zip'
    print('INFO: Using plugin file', plugin_file)

    with zipfile.ZipFile(plugin_file, 'w') as f:
        f.writestr('manifest.json', manifest_json)
        f.writestr('background.js', background_js)

    return plugin_file

def init_browser(plugin_file: str) -> WebDriver:
    options = webdriver.ChromeOptions()
    options.add_argument('start-maximized')
    options.add_argument('disable-blink-features=AutomationControlled')
    options.add_extension(plugin_file)
    browser = webdriver.Chrome(options=options)
    return browser

def init_lihkg_context(browser: WebDriver) -> WebElement:
    '''
    We need to open a LIHKG page and then jump to the API URL.
    This process is wrapped as the LIHKG context.
    '''

    browser.get('https://lihkg.com/thread/2256553/page/1')
    body = WebDriverWait(browser, timeout=5).until(
        EC.presence_of_element_located((By.TAG_NAME, 'body'))
    )
    element_id = random_string()
    browser.execute_script(f'a = document.createElement("a"); a.id = arguments[1]; a.target = "_blank"; arguments[0].appendChild(a)', body, element_id)
    context = browser.find_element(By.ID, element_id)
    return context

def get_json(browser: WebDriver, context: WebElement, url: str) -> object:
    browser.execute_script('arguments[0].href = arguments[1]', context, url)
    browser.execute_script('arguments[0].click()', context)
    browser.switch_to.window(browser.window_handles[1])
    pre = WebDriverWait(browser, timeout=5).until(
        EC.presence_of_element_located((By.TAG_NAME, 'pre'))
    )
    text = pre.text
    obj = json.loads(text)
    browser.close()
    browser.switch_to.window(browser.window_handles[0])
    return obj

def get_json_of_position(browser: WebDriver, context: WebElement, thread_id: int, page: int) -> object:
    url = f'https://lihkg.com/api_v2/thread/{thread_id}/page/{page}?order=reply_time'
    obj = get_json(browser, context, url)
    return obj

def minimize_json(obj: object) -> str:
    '''
    Return the most compact representation of a JSON object.
    '''

    return json.dumps(obj, separators=(',', ':'), ensure_ascii=False)

def write_file(f: TextIO, obj: object, thread_id: int, page: int) -> None:
    '''
    Write a result to the output file.
    '''

    # ignore keyboard interrupt to ensure the integrity of file
    old_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    print(thread_id, page, minimize_json(obj), sep='\t', file=f)
    signal.signal(signal.SIGINT, old_handler)

def start_browser(filename: str, thread_id: int, to_thread: int, page: int, plugin_file: str, pbar: tqdm):
    display = Display()
    display.start()

    browser = init_browser(plugin_file)
    context = init_lihkg_context(browser)

    has_exception = False

    try:
        with open(filename, 'a') as f:
            while thread_id < to_thread:
                obj = get_json_of_position(browser, context, thread_id, page)
                write_file(f, obj, thread_id, page)
                thread_id_new, page = get_next_page_from_json(obj, thread_id, page)
                if thread_id_new > thread_id:
                    pbar.update()
                    thread_id = thread_id_new
    except (TimeoutException, WebDriverException):
        has_exception = True

    browser.quit()
    display.stop()

    return has_exception, thread_id, page

def main():
    from_thread, to_thread, proxy_host, proxy_port, proxy_user, proxy_pass = read_command_line()
    plugin_file = make_proxy_file(proxy_host, proxy_port, proxy_user, proxy_pass)
    filename = make_filename(from_thread)
    thread_id, page = get_resume_position(filename, from_thread)
    pbar = tqdm(initial=thread_id-from_thread, total=to_thread-from_thread, smoothing=0.)
    while True:
        has_exception, thread_id, page = start_browser(filename, thread_id, to_thread, page, plugin_file, pbar)
        if not has_exception:
            break
    pbar.close()

if __name__ == '__main__':
    main()
