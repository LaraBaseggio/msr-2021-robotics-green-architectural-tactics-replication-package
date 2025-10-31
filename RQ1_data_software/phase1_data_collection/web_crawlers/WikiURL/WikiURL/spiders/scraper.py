import scrapy
import json
from WikiURL.items import WikiItem

"""
Old start_url was expired, new url: https://index.ros.org/?search_packages=true/page/1/time
Instead of fetching data using Playwright (first solution I tried), fetch data using the API found in Network -> Fetch/XHR
"""
class WikiSpider(scrapy.Spider):
    name = "wikiurl"
    allowed_domains = ["index.ros.org"]
    start_urls = ["https://index.ros.org/search/packages/data.humble.json"]

    def parse(self, response):
        data = json.loads(response.text)
        
        print(f"Total packages found: {len(data)}")
        
        for package in data:
            item = WikiItem()
            item["urls"] = package.get('url', '')
            yield item