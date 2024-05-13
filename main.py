from datetime import datetime
import requests
from bs4 import BeautifulSoup, Tag
import dateutil.parser
from dateutil import tz


def main():
    # get current month and year
    month = datetime.now().month
    year = datetime.now().year

    res = requests.get(
        f"https://www.1000ps.de/motorrad-testberichte?DatumAb=01.{month}.{year}",
        timeout=5,
    )

    html = BeautifulSoup(res.text, "html.parser")
    container = html.select_one("main div.pt-4:not(.row)")

    if not isinstance(container, Tag):
        raise ValueError("Container not found")

    items = container.select(".card:not(.native-ad-story) .boxlink")
    print(f"{len(items)} Testberichte.")

    testberichte = []
    for item in items:
        title = getattr(item.select_one(".card-body .card-title"), "text", "")
        link = f"https://www.1000ps.de{item.get('href', '')}"

        img = item.select_one(".card-img img")
        # for some fucking reason, img_src = getattr(img, "data-src", "") returns None
        img_src = img.get("data-src") if img else None

        content = item.select_one(".card-body .card-text")

        if not content:
            raise ValueError(f"Content not found for {title}")

        if span := content.select_one("span"):
            date_str = getattr(span, "text", "01-01-1970")
            span.decompose()

        if img_src:
            content.append(
                BeautifulSoup(f"<img src='{img_src}' />", features="html.parser")
            )

        description = content.prettify()

        testberichte.append(
            Testbericht(
                title,
                link,
                description,
                dateutil.parser.parse(date_str, fuzzy=True),
            )
        )

    feed = generate_feed(testberichte)
    with open("1000ps.xml", "w", encoding="utf-8") as f:
        f.write(BeautifulSoup(feed, "xml").prettify())


class Testbericht:
    def __init__(self, title: str, link: str, description: str, pub_date: datetime):
        self.title: str = title
        self.link: str = link
        self.description: str = description
        self.pub_date: str = pub_date.replace(tzinfo=tz.UTC).strftime(
            "%a, %d %b %Y %H:%M:%S %z"
        )

    def generate_xml(self) -> str:
        return f"""
        <item>
          <title>{self.title}</title>
          <link>{self.link}</link>  
          <description><![CDATA[{self.description}]]></description>
          <pubDate>{self.pub_date}</pubDate>
        </item>
        """


def generate_feed(testberichte: list[Testbericht]) -> str:
    items = "".join([testbericht.generate_xml() for testbericht in testberichte])

    return f"""
    <rss version="2.0">
      <channel>
        <title>1000PS Testberichte</title>
        <link>https://www.1000ps.de/motorrad-testberichte</link>
        <description>Die neuesten Testberichte von 1000PS</description>
        {items}
      </channel>
    </rss>
    """


if __name__ == "__main__":
    main()
