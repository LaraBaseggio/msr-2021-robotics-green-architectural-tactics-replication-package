import scrapy
import json
import re
from ROSAStats.items import RosaItem


class RosaSpider(scrapy.Spider):
    """
    Minimal ROSA Spider:
    - Reads URLs from rosa_data.json
    - Extracts question IDs from URLs
    - Fetches user (owner) info via Stack Exchange API
    - Saves only 'url' and 'user' in RosaItem
    """
    name = "rosa"
    allowed_domains = ["api.stackexchange.com"]

    # Load URLs from local JSON file
    with open('../../../../data/rosa_new_data.json') as f:
        url_data = json.load(f)
    wiki_urls = [item.get('url') for item in url_data if item.get('url')]

    # Extract question IDs from URLs
    question_ids = []
    for url in wiki_urls:
        match = re.search(r'/questions/(\d+)', url)
        if match:
            question_ids.append((match.group(1), url))

    # Build Stack Exchange API URLs for each question
    start_urls = [
        f"https://api.stackexchange.com/2.3/questions/{qid}?order=desc&sort=creation&site=robotics&filter=default"
        for qid, _ in question_ids
    ]

    # Map API URL → original ROS Answers URL
    url_lookup = { 
        f"https://api.stackexchange.com/2.3/questions/{qid}?order=desc&sort=creation&site=robotics&filter=default": orig_url
        for qid, orig_url in question_ids
    }

    def parse(self, response):
        """Parse Stack Exchange API response to extract user info"""
        data = json.loads(response.text)
        questions = data.get('items', [])

        if not questions:
            return

        question = questions[0]
        user = question.get('owner', {}).get('display_name', '')

        item = RosaItem()
        item['url'] = self.url_lookup.get(response.url, '')
        item['user'] = user
        yield item
