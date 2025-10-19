import scrapy
import json
from scrapy.spiders import CrawlSpider
from ROSDWebCrawler.items import ROSDItem


class ROSDSpider(CrawlSpider):
  name = "ros-discourse"
  # general fallback URL
  start_urls = ["https://discourse.openrobotics.org"]

  def __init__(self, category_slug: str = "ng-ros", *args, **kwargs):
    """Allow selecting a category by slug at crawl time.

    Usage: scrapy crawl ros-discourse -a category_slug=ng-ros
    """
    super().__init__(*args, **kwargs)
    self.category_slug = category_slug
    # resolved category id (set after fetching categories.json)
    self.target_category_id = None

  def start_requests(self):
    """Bootstrap crawl by fetching the site categories, then latest.json.

    We avoid any network I/O at import time and make decisions at
    runtime. We first fetch /categories.json to map slug -> id, then
    request /latest.json and filter topics by the resolved id.
    """
    base = "https://discourse.openrobotics.org"
    categories_url = f"{base}/categories.json"
    yield scrapy.Request(categories_url, callback=self.parse_categories, dont_filter=True)

  def parse_categories(self, response):
    try:
      data = json.loads(response.text)
    except Exception:
      self.logger.warning("Failed to parse categories.json")
      data = {}

    categories = data.get("category_list", {}).get("categories", [])
    slug = (self.category_slug or "").strip()
    found = None
    for c in categories:
      # match by slug first, fall back to a normalized name
      if c.get("slug") == slug or (c.get("name") or "").lower().replace(" ", "-") == slug:
        found = c
        break

    if found:
      self.target_category_id = found.get("id")
      self.logger.info(f"Resolved category '{slug}' -> id={self.target_category_id}")
    else:
      self.logger.warning(f"Category slug '{slug}' not found in categories.json; proceeding without filtering")

    # fetch the site-wide feed and filter topics in parse_json
    base = "https://discourse.openrobotics.org"
    latest_url = f"{base}/latest.json"
    yield scrapy.Request(latest_url, callback=self.parse_json, dont_filter=True)

  def parse_json(self, response):
    try:
      data = json.loads(response.text)
    except Exception:
      self.logger.warning("Failed to parse latest.json")
      return

    topics = data.get("topic_list", {}).get("topics", [])
    base = "https://discourse.openrobotics.org"
    for t in topics:
      # filter by resolved category id when available
      if self.target_category_id is not None:
        if t.get("category_id") != self.target_category_id:
          continue

      slug = t.get("slug")
      if slug:
        topic_url = f"{base}/t/{slug}"
        yield scrapy.Request(topic_url, callback=self.parse_detail_page)

  def parse_detail_page(self, response):
    item = ROSDItem()
    # scrape title of post
    title = response.css("h1 > a::text").get()
    item["title"] = title
    # scrape thread content
    thread_contents = response.css(".wrap p::text").getall()
    item["thread_contents"] = thread_contents
    # scrape thread details
    temp = response.css("li::text").getall()
    if temp and not all(p.strip() == "" for p in temp):
      item["thread_details"] = temp

    item["url"] = response.url
    yield item
