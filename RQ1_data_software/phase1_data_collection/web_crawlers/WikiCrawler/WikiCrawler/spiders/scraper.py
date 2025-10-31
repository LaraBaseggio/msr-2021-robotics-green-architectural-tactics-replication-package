import scrapy
import json
from WikiCrawler.items import WikiItem


class WikiSpider(scrapy.Spider):
    name = "wiki"
    allowed_domains = ["index.ros.org", "ros.org", "wiki.ros.org"]
    start_urls = ["https://index.ros.org/search/packages/data.humble.json"]
  
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': True,
        # Disable Playwright for this spider
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
            "https": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
        },
    }

    def parse(self, response):
        """Parse the JSON API response and extract package data."""
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            self.logger.error('Failed to parse JSON: %s', e)
            return

        self.logger.info(f"Total packages found: {len(data)}")
        
        # Extract data from each package in the JSON
        for package_data in data:
            url_path = package_data.get('url', '')
            # Remove the fragment (#humble) to avoid redirects
            url_path_clean = url_path.split('#')[0]
            full_url = f"https://index.ros.org{url_path_clean}"
            readme = package_data.get('readme', '')
            
            # If readme is empty, fetch the package page to get Website link
            if not readme:
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_package_page,
                    meta={
                        'package_data': package_data,
                        'full_url': full_url,
                    },
                    dont_filter=True
                )
            else:
                # If readme exists, yield the item directly
                item = WikiItem()
                item['url'] = full_url
                item['package'] = package_data.get('package', '')
                item['package_summary'] = package_data.get('description', '')
                item['package_details'] = readme
                yield item

    def parse_package_page(self, response):
        """Parse the package page to extract the Website link."""
        package_data = response.meta['package_data']
        full_url = response.meta['full_url']
        
        # Extract the first link that contains "Website" text in the parent li
        website_links = response.css('div.panel-body ul.list-unstyled li')
        website_url = None
        
        for li in website_links:
            link_text = li.css('a::text').get()
            if link_text and 'Website' in link_text:
                website_url = li.css('a::attr(href)').get()
                break
        
        # Alternative: just get the first link in the list
        if not website_url:
            website_url = response.css('div.panel-body ul.list-unstyled li a::attr(href)').get()
        
        self.logger.info(f"Found website URL: {website_url} for package: {package_data.get('package')}")
        
        if website_url and ('ros.org/wiki' in website_url or 'wiki.ros.org' in website_url):
            # Fetch the wiki page for package details
            yield scrapy.Request(
                url=website_url,
                callback=self.parse_wiki_page,
                meta={
                    'package_data': package_data,
                    'full_url': full_url,
                },
                dont_filter=True,
                errback=self.handle_error
            )
        else:
            # No valid wiki link, yield item with empty details
            self.logger.warning(f"No valid wiki URL found for package: {package_data.get('package')}")
            item = WikiItem()
            item['url'] = full_url
            item['package'] = package_data.get('package', '')
            item['package_summary'] = package_data.get('description', '')
            item['package_details'] = ''
            yield item

    def parse_wiki_page(self, response):
        """Parse the ROS wiki page to extract package details."""
        package_data = response.meta['package_data']
        full_url = response.meta['full_url']
        
        self.logger.info(f"Parsing wiki page: {response.url} for package: {package_data.get('package')}")
        
        item = WikiItem()
        item['url'] = full_url
        item['package'] = package_data.get('package', '')
        
        # Extract package summary from version-specific sections
        package_summary = []
        for version_class in ['noetic', 'melodic']:
            summary_selector = f'#content div.version.{version_class} p[id^="package-info-"]::text'
            package_summary = response.css(summary_selector).getall()
            package_summary = [s.strip() for s in package_summary if s.strip()]

            if package_summary:  # stop at the first non-empty version
                break
        
        # Use the original description if no summary found on wiki
        if not package_summary:
            package_summary = package_data.get('description', '')
        
        item['package_summary'] = package_summary

        # Extract package details from line867 and line862 paragraphs
        package_details1 = response.css('#content > p.line867::text').getall()
        package_details2 = response.css('#content > p.line862::text').getall()
        package_details = [d.strip() for d in (package_details1 + package_details2) if d.strip()]
        item['package_details'] = package_details if package_details else ''

        yield item

    def handle_error(self, failure):
        """Handle errors when fetching wiki pages."""
        package_data = failure.request.meta.get('package_data', {})
        full_url = failure.request.meta.get('full_url', '')
        
        self.logger.error(f"Error fetching wiki page for {package_data.get('package')}: {failure}")
        
        # Yield item with empty details on error
        item = WikiItem()
        item['url'] = full_url
        item['package'] = package_data.get('package', '')
        item['package_summary'] = package_data.get('description', '')
        item['package_details'] = ''
        yield item