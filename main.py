import logging
from datetime import datetime
from os import path, getenv
from ftplib import FTP

import dateutil.parser
import requests
from bs4 import BeautifulSoup
from dateutil import tz
from dotenv import load_dotenv


def main():
    month = datetime.now().month
    year = datetime.now().year

    # the feed shall only contain posts from the current month; helps to keep the feed small
    res = requests.get(
        f"https://www.1000ps.de/motorrad-testberichte?DatumAb=01.{month}.{year}",
        timeout=10,
    )

    html = BeautifulSoup(res.text, "html.parser")

    if not (container := html.select_one("main div.pt-4:not(.row)")):
        raise ValueError("Container not found.")

    if not (items := container.select(".card:not(.native-ad-story) .boxlink")):
        raise ValueError("No items found in container.")

    testberichte = []
    for item in items:
        title = getattr(item.select_one(".card-body .card-title"), "text", "")
        link = f"https://www.1000ps.de{item.get('href', '')}"

        img = item.select_one(".card-img img")
        img_src = img.get("data-src") if img else ""

        content = item.select_one(".card-body .card-text")

        if not title:
            logging.warning("Title not found for %s", link)
            continue

        if not link:
            logging.warning("Link not found for %s", title)
            continue

        if not img_src:
            logging.warning("Image not found for %s", title)
            # keep going

        if not content:
            logging.warning("Content not found for %s", title)
            continue

        # extract date from content and remove it from the text
        if span := content.select_one("span"):
            date_str = getattr(span, "text", "01-01-1970")
            span.decompose()
            if date_str == "01-01-1970":
                logging.warning("Date not found for %s", title)
                continue

        if img_src:
            content.append(BeautifulSoup(f"<img src='{img_src}' />", features="html.parser"))

        testberichte.append(
            Testbericht(
                title,
                link,
                content.prettify(),
                dateutil.parser.parse(date_str, fuzzy=True),
            )
        )

    Feed(testberichte).save().upload()


class Testbericht:
    def __init__(self, title: str, link: str, description: str, pub_date: datetime):
        self.title: str = title
        self.link: str = link
        self.description: str = description
        self.pub_date: str = pub_date.replace(tzinfo=tz.UTC).strftime("%a, %d %b %Y %H:%M:%S %z")

    def generate_xml(self) -> str:
        return f"""
        <item>
          <title>{self.title}</title>
          <link>{self.link}</link>
          <description><![CDATA[{self.description}]]></description>
          <pubDate>{self.pub_date}</pubDate>
        </item>
        """


class Feed:
    def __init__(self, testberichte: list[Testbericht]):
        self.testberichte = testberichte
        self.file_path = path.join(path.dirname(path.realpath(__file__)), "1000ps.rss")

    def create(self) -> str:
        return f"""
        <rss version="2.0">
        <channel>
            <title>1000PS Testberichte</title>
            <link>https://www.1000ps.de/motorrad-testberichte</link>
            <description>Inoffizieller Feed für die neuesten Testberichte von 1000PS</description>
            <lastBuildDate>
                {datetime.now().replace(tzinfo=tz.tzlocal()).strftime("%a, %d %b %Y %H:%M:%S %z")}
            </lastBuildDate>
            {"".join([testbericht.generate_xml() for testbericht in self.testberichte])}
        </channel>
        </rss>
        """

    def save(self) -> "Feed":
        with open(
            self.file_path,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(BeautifulSoup(self.create(), "xml").prettify())
        return self

    def upload(self) -> None:
        ftp_host = getenv("FTP_HOST")
        ftp_user = getenv("FTP_USER")
        ftp_pass = getenv("FTP_PASS")
        ftp_path = getenv("FTP_PATH")

        if not ftp_host:
            return

        if not ftp_user or not ftp_pass:
            raise ValueError("FTP_USER and FTP_PASS must be set in the .env file.")

        ftp = FTP(ftp_host)
        ftp.login(ftp_user, ftp_pass)

        if ftp_path:
            ftp.cwd(ftp_path)

        with open(self.file_path, "rb") as file:
            ftp.storbinary("STOR 1000ps.rss", file)
            if ftp.lastresp == "226":
                print("Upload successful.")
            else:
                logging.error("Error uploading: %s", ftp.lastresp)

        ftp.quit()


if __name__ == "__main__":
    try:
        load_dotenv()

        logging.basicConfig(
            filename=path.join(path.dirname(path.realpath(__file__)), "app.log"),
            filemode="a",
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        main()
    except Exception as e:
        logging.error(e)
