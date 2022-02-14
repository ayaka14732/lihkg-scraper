# lihkg-scraper

A Python script for scraping LIHKG and saving the data to a local file.

The previous version, which is elegant but no longer work, can be found in the [`v1`](https://github.com/ayaka14732/lihkg-scraper/tree/v1) branch.

## Prerequisites

The script is designed to be executed on a typical Ubuntu 20.04 VPS server.

Install Chrome:

```sh
sudo apt install -y unzip xvfb libxi6 libgconf-2-4
curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add
echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | sudo tee -a /etc/apt/sources.list.d/google-chrome.list
sudo apt update -y
sudo apt install -y google-chrome-stable
```

Install ChromeDriver:

```sh
wget https://chromedriver.storage.googleapis.com/98.0.4758.80/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
rm -f chromedriver_linux64.zip
sudo mv chromedriver /usr/bin
```

Install Xvfb:

```sh
sudo apt install -y xvfb xserver-xephyr tigervnc-standalone-server x11-utils gnumeric
```

Install Python dependencies:

```sh
pip install -r requirements.txt
```

The script is also tested on Arch Linux. In this case, you can install the dependencies from `pacman`.

## Usage

The script is designed to be executed with a HTTP proxy server with authentication.

```sh
export FROM_THREAD 800000
export TO_THREAD 900000
export PROXY_HOST 127.0.0.1
export PROXY_PORT 20000
export PROXY_USER testuser
export PROXY_PASS test123
python main.py $FROM_THREAD $TO_THREAD $PROXY_HOST $PROXY_PORT $PROXY_USER $PROXY_PASS
```

You need to modify the values according to your demand and your configuration.
