import scrapy
import json
import re
import os
from SOStats.items import SOItem

class SOSpider(scrapy.Spider):
    name = "stackoverflow"
    allowed_domains = ["api.stackexchange.com"]
    
    # Stack Exchange API key
    api_key = "rl_mYeNdX7JokG4xEpsM3PNhvSm1"
    
    spider_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(spider_dir, '../../../../data/stackoverflow_new_data.json')
    
    def start_requests(self):
        """Load the JSON data and create API requests for each question"""
        with open(self.json_path) as f:
            url_data = json.load(f)
        
        for item_data in url_data:
            url = item_data.get('url')
            if url:
                try:
                    question_id = url.split('/questions/')[1].split('/')[0]
                    
                    # Use API to get question details including owner info
                    api_url = (
                        f"https://api.stackexchange.com/2.3/questions/{question_id}"
                        f"?order=desc&sort=activity&site=stackoverflow"
                        f"&filter=!9_bDDxJY5&key={self.api_key}"
                    )
                    
                    yield scrapy.Request(
                        api_url,
                        callback=self.parse,
                        meta={'original_url': url}
                    )
                except (IndexError, AttributeError):
                    self.logger.warning(f"Could not extract question ID from URL: {url}")

    def parse(self, response):
        item = SOItem()
        
        # Only include url and user
        item['url'] = response.meta['original_url']
        
        # Parse API response
        data = json.loads(response.text)
        questions = data.get('items', [])
        
        if questions:
            question = questions[0]
            owner = question.get('owner', {})
            
            # Get only the user display name
            item['user'] = owner.get('display_name')
        else:
            self.logger.warning(f"No data returned for URL: {item['url']}")
            item['user'] = None
        
        yield item