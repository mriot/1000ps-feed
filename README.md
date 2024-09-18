# 1000ps-feed
RSS Feed generator for 1000PS Testberichte <https://www.1000ps.de/motorrad-testberichte>

A version that is updated every 6 hours is hosted here: <https://riotcoding.com/feeds/1000ps.rss>

# Usage

> [!NOTE]
> Runs on Python 3.9+ to maximize compatibility with most Raspberry Pis.

Clone/download this repository and install the dependencies using:

```bash
pip install -r requirements.txt
```

## Configure a cron job

To run the script every 6 hours, you can set up a cron job. Open your crontab with the following command:

```bash
crontab -e
```

Then add the following line:

```bash
0 */6 * * * /path/to/python /path/to/main.py
```

> [!IMPORTANT]
> If you are using a virtual environment, make sure to specify the path to the Python interpreter in your virtual environment.

## FTP upload

> [!NOTE]
> If `FTP_HOST` is not configured, upload is skipped.  
> `FTP_PATH` is optional

Create a `.env` file in the root directory with the following content:

```
FTP_HOST = ftp-host
FTP_USER = username
FTP_PASS = password
FTP_PATH = target-path
```

---

## Disclaimer

This project is not affiliated with 1000PS. The RSS feed is generated from publicly available information on their website.
