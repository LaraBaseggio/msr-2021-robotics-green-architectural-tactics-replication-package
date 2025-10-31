import scrapy
import json
import os
import re
from WikiStats.items import WikiItem 

class WikiStatsAPISpider(scrapy.Spider):
    name = "wiki_stats"
    allowed_domains = ["index.ros.org"]
    
    start_urls = ["https://index.ros.org/search/packages/data.humble.json"]

    def parse(self, response):
        """
        Parses the JSON response from the ROS Index API and extracts 
        url, last_commit_time, and authors.
        """
        try:
            # Load the entire list of package data from the JSON API response
            packages_data = json.loads(response.text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON from {response.url}: {e}")
            return

        self.logger.info(f"Successfully loaded {len(packages_data)} package entries.")

        for data in packages_data:
            item = WikiItem()
            
            url_path = data.get('url', '')
            url_path_clean = url_path.split('#')[0]
            item['url'] = f"https://index.ros.org{url_path_clean}"
            
            item['time'] = data.get('last_commit_time', 'N/A')

            authors_data = data.get('authors')
            
            if isinstance(authors_data, list):
                authors = ", ".join(authors_data)
            elif isinstance(authors_data, str):
                authors = authors_data
            else:
                authors = 'N/A'
                
            item['user'] = authors
            
            yield item