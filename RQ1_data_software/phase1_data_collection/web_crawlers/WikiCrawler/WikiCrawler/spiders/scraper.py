import os
import json
import scrapy
from scrapy.spiders import CrawlSpider
from WikiCrawler.items import WikiItem


class WikiSpider(CrawlSpider):
    name = "wiki"
    
    # Settings to avoid being blocked
    custom_settings = {
        'DOWNLOAD_DELAY': 1,                
        'RANDOMIZE_DOWNLOAD_DELAY': True,     
        'CONCURRENT_REQUESTS': 2,             
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': True,               # still obey robots.txt
    }

    def start_requests(self):
        """Load urls.json and yield requests."""
        urls_file = os.path.join(os.path.dirname(__file__), 'urls.json')
        try:
            with open(urls_file, 'r') as f:
                url_data = json.load(f)
        except FileNotFoundError:
            self.logger.error('urls.json not found at %s', urls_file)
            return
        except json.JSONDecodeError as e:
            self.logger.error('Failed to parse urls.json: %s', e)
            return

        url_list = [item.get('urls') for item in url_data if item.get('urls')]
        wiki_urls = ['https://wiki.ros.org/{0}'.format(i) for i in url_list]

        for u in wiki_urls:
            yield scrapy.Request(
                url=u, 
                meta={"playwright": True},
                callback=self.parse,
                headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                },
                dont_filter=True
            )

    def parse(self, response):
      item = WikiItem()
      item['url'] = response.url
      item['package'] = response.url.rstrip('/').split('/')[-1]

      for version_class in ['noetic', 'melodic']:
        summary_selector = f'#content div.version.{version_class} p[id^="package-info-"]::text'
        package_summary = response.css(summary_selector).getall()
        package_summary = [s.strip() for s in package_summary if s.strip()]

        if package_summary:  # stop at the first non-empty version
            break
        
      item['package_summary'] = package_summary

      # Extract package details from line867 and line862 paragraphs
      package_details1 = response.css('#content > p.line867::text').getall()
      package_details2 = response.css('#content > p.line862::text').getall()
      package_details = [d.strip() for d in (package_details1 + package_details2) if d.strip()]
      item['package_details'] = package_details

      yield item

