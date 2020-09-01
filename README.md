# LIHKG Scraper

## Sample result

```
等自己發到個夢係完整有頭有尾
因為知道醒咗下次唔會再發返同樣嘅夢
今朝試過同菲利拗手瓜
但情況似全職獵人信長對手剛咁
係撚咁比佢手拗爆
最後唔知見到斯路
個夢就完左
勁鍾意發夢
長期有夢發
有時可以控制到
印象最深刻係去海洋公園玩完旋轉木馬之後趕纜車
個世界變咗無咩引力
可以月球漫步咁彈下彈下行路
個感覺勁真實
個陣以為係真
點知原來係夢
又試過發好得意嘅夢之後發完好清醒
我唔肯定有冇醒到
之後我就同自己講要記實個夢之後講俾fd知因為一定好快唔記得
點知又繼續訓
就咩都唔記得哂
```

## Setup

### Specify proxies

Save a list of proxies to `proxies.txt`.

You should specify one proxy per line. Each proxy is in the format defined by the Request library.

### Configure the scraper

Copy `config.template.py` to `config.py`, then change the parameters to meet your need.

You can change the following parameters:

- `first_post`: (`int`) The first post to scrape
- `last_post`: (`int`) The last post to scrape (exclusive)
- `thread_count`: (`int`) Number of threads used to scrape the pages
- `server_address`: (`str`) Listen address of the proxy management server
- `server_port`: (`int`) Listen port of the proxy management server

### Install dependencies

- Arch Linux: `pacman -S python-requests python-lxml python-beautifulsoup4`
- openSUSE: `zypper install python3-requests python3-lxml python3-beautifulsoup4`
- Other systems: `pip install -r requirements.txt`

### Run the scraper

```sh
python3 main.py
```

## Usage

### Operate the proxy list

The scraper contains a proxy management server that listens on port `18000`. You can operate the proxy list when the scraper is running by sending requests to that port.

Supported operations:

- `GET`: View the proxies that are currently working properly.
- `POST`: View the proxies that are currently blocked.
- `PUT`: Add new proxies to the proxy list from `proxies.txt`. If a proxy is currently in the blocklist, it will be removed from the blocklist.

## Design

### Get data from LIHKG API

The method of obtaining data is roughly equivalent to:

```sh
curl \
-H "Accept: application/json, text/plain, */*" \
-H "Accept-Language: en-US,en;q=0.5" \
-H "Host: lihkg.com" \
-H "Referer: https://lihkg.com/thread/1081676/page/1" \
-H "User-Agent: Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0" \
-H "X-LI-DEVICE: 6c7a86608385347a9cb7f1d1436199c47e250c49" \
-H "X-LI-DEVICE-TYPE: browser" \
-H "X-LI-LOAD-TIME: 6.135287" \
https://lihkg.com/api_v2/thread/1081676/page/1\?order\=reply_time
```

Significant fields in the result:

- `res["success"]` should be `1`.
- `res["response"]["total_page"]` is the total pages of the thread.
- `res["response"]["item_data"]` is the list of messages.
- `res["response"]["item_data"][0]["msg"]` is the text of the first message. Change `0` to other numbers to get other messages.

### Error handling

HTTP status code:

- `403`: The proxy IP is banned by LIHKG. The scraper should retry with another proxy and permanently remove the current proxy from proxy list.
- `429`: The proxy IP is temporarily blocked by LIHKG. The scraper should retry with another proxy and temporarily remove the current proxy from proxy list.
- `404`: The requested thread does not exists. The scraper should move on to the next thread.

### Sanitize

Sample raw text from LIHKG API:

```
我成日擺好啲公仔，做做下嘢唔覺意望過去都見到佢地望住我<img src="/assets/faces/normal/cry.gif" class="hkgmoji" /> <img src="/assets/faces/normal/cry.gif" class="hkgmoji" /> 點解會咁<img src="/assets/faces/normal/frown.gif" class="hkgmoji" />
```

Things to deal with:

- Line breaks are represented by `<br/>`
- There are emoticons in the text, which are represented by `<img/>`
- The content of the text may be 此回覆已被刪除 (This reply has been deleted)

Algorithm:

- Replace `<br/>` by line break
- Replace `<img/>` and other HTML tags by space
- Split the string into parts by the characters which are neither Han characters, letters nor numbers
- Remove the substrings which does not contain Han characters
- Remove the substrings which are less than five characters
- Yield the remaining substrings

Sample result:

```
我成日擺好啲公仔
做做下嘢唔覺意望過去都見到佢地望住我
```

You can also modify the algorithm (in `sanitize.py`) to meet your needs.
