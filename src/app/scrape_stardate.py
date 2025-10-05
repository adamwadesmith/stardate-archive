import re, time, html
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup

BASE = "https://stardate.org"
START = f"{BASE}/podcast/"
SITEMAP = f"{BASE}/sitemap"
SLEEP = 0  # be polite

def fetch_podcast_sitemaps(text:str) -> list[str]:
    soup = BeautifulSoup(text, "xml")
    return []
    
def iter_archive_pages():
    url = START
    # while True:
    for i in range(0, 2):   # for testing
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        yield soup

        # pagination: rel=next
        next_link = soup.find("link", rel="next")
        if not next_link:
            break

        url = urljoin(url, next_link.get("href"))
        time.sleep(SLEEP)

def fetch_episode(ep_url):
    r = requests.get(ep_url, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.find(["h1","h2"]).get_text(strip=True)
    # date appears near title/byline
    date_el = soup.find(string=re.compile(r"\b\d{4}\b"))
    pub_date = None
    if date_el:
        pub_date = date_el.strip()

    # description
    desc = soup.find("div", class_=re.compile(r"entry-content|post-content|content", re.I))
    description = desc.get_text(" ", strip=True) if desc else ""

    # MP3 link (“Download file”)
    mp3 = None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".mp3"):
            mp3 = urljoin(ep_url, href)
            break
        
    return {"title": title, "link": ep_url, "pub_date": pub_date, "description": description, "enclosure": mp3}

def gather_all():
    seen = set()
    eps = []
    for soup in iter_archive_pages():
        # episode cards
        for h2 in soup.find_all(["h2","h3"]):
            link = h2.find("a", href=True)
            if not link: 
                continue

            ep_url = urljoin(BASE, link["href"])
            if "/podcast/" not in ep_url: 
                continue

            if ep_url in seen: 
                continue

            seen.add(ep_url)
            try:
                data = fetch_episode(ep_url)
                if data["enclosure"]:
                    eps.append(data)

            except Exception as e:
                print("skip", ep_url, e)

            time.sleep(SLEEP)

    return eps

def build_rss(items, out_path="stardate_full.xml"):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "StarDate (Complete Archive, Personal Feed)"
    ET.SubElement(channel, "link").text = START
    ET.SubElement(channel, "description").text = "Personal archive feed assembled from stardate.org podcast pages."
    now = time.strftime("%a, %d %b %Y %H:%M:%S %z")
    ET.SubElement(channel, "lastBuildDate").text = now
    for it in items:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = it["title"]
        ET.SubElement(item, "link").text = it["link"]
        if it["pub_date"]:
            ET.SubElement(item, "pubDate").text = it["pub_date"]

        ET.SubElement(item, "description").text = html.escape(it["description"][:5000])
        enc = ET.SubElement(item, "enclosure", url=it["enclosure"], type="audio/mpeg")
        guid = ET.SubElement(item, "guid")
        guid.text = it["enclosure"] or it["link"]
        guid.set("isPermaLink", "false")
    ET.ElementTree(rss).write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"Wrote {out_path} with {len(items)} items")

if __name__ == "__main__":
    items = gather_all()
    build_rss(items)
