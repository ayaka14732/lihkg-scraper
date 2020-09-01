from bs4 import BeautifulSoup
from itertools import groupby

def is_alphanum(c):
    p = ord(c)
    return ord('0') <= p <= ord('9') \
        or ord('a') <= p <= ord('z') \
        or ord('A') <= p <= ord('Z')

def is_han(c):
    p = ord(c)
    return 0x4e00 <= p <= 0x9fff \
        or 0x3400 <= p <= 0x4dbf \
        or 0x20000 <= p <= 0x2a6df \
        or 0x2a700 <= p <= 0x2b73f \
        or 0x2b740 <= p <= 0x2b81f \
        or 0x2b820 <= p <= 0x2ceaf \
        or 0x2ceb0 <= p <= 0x2ebef \
        or 0x30000 <= p <= 0x3134f

def split_parts(s):
    return \
        filter(lambda x: len(x) > 4 and not all(is_alphanum(c) for c in x),
            map(lambda xy: ''.join(xy[1]),
                filter(lambda xy: xy[0],
                    groupby(s, key=lambda c: is_alphanum(c) or is_han(c)))))

def sanitize(msg):
    soup = BeautifulSoup(msg, 'lxml')

    # Replace `<br/>` by line break
    for br in soup.find_all('br'):
        br.replace_with('\n')

    # Replace `<img/>` (used for emoticon) by space
    text = soup.get_text(' ', strip=True)

    if not text or text == '此回覆已被刪除':
        return

    yield from split_parts(text)
