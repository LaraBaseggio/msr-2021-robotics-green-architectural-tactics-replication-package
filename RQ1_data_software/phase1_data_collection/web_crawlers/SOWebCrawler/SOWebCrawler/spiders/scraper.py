import scrapy
import json
import re
from html import unescape
from datetime import datetime
from SOWebCrawler.items import SOItem

'''
Old code url (https://stackoverflow.com/questions/tagged/ros?tab=newest&pagesize=50) gave 403 forbidden access error. 
Using stack exchanage API instead (tagged ros) - this is were each question gets redirected to from.  
'''

class SOSpider(scrapy.Spider):
    name = "stackoverflow"
    allowed_domains = ["api.stackexchange.com"]

    api_key = "rl_mYeNdX7JokG4xEpsM3PNhvSm1"
    
    start_urls = [
        f"https://api.stackexchange.com/2.3/questions?order=desc&sort=creation&tagged=ros&site=stackoverflow&pagesize=100&filter=withbody&key={api_key}"
    ]

    def parse(self, response):
        data = json.loads(response.text)
        questions = data.get('items', [])

        for q in questions:
            item = SOItem()
            item['title'] = unescape(q.get('title', ''))
            timestamp = q.get('creation_date')
            if timestamp:
                item['time'] = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%SZ')
            else:
                item['time'] = None
            body = q.get('body', '')

            # Clean and extract data
            item['post_content'] = [self.clean_html(body)]
            item['question_code'] = self.extract_code(body)
            item['quote'] = self.extract_quotes(body)
            item['url'] = q.get('link')

            # Fetch answers via API if any exist
            if q.get('answer_count', 0) > 0:
                answers_api = (
                    f"https://api.stackexchange.com/2.3/questions/{q['question_id']}/answers"
                    f"?order=desc&sort=creation&site=stackoverflow&filter=withbody&key={self.api_key}"
                )
                yield scrapy.Request(
                    answers_api,
                    callback=self.parse_answers,
                    meta={'item': item},
                )
            else:
                item['answer'] = []
                item['answer_code'] = []
                yield item

        # Pagination - continue crawling all pages
        if data.get('has_more'):
            # Extract current page number or default to 1
            current_page = 1
            if "&page=" in response.url:
                try:
                    current_page = int(response.url.split("&page=")[1].split("&")[0])
                except (IndexError, ValueError):
                    current_page = 1
            
            next_page = current_page + 1
            next_url = (
                f"https://api.stackexchange.com/2.3/questions?"
                f"order=desc&sort=creation&tagged=ros&site=stackoverflow"
                f"&pagesize=100&page={next_page}&filter=withbody&key={self.api_key}"
            )
            yield scrapy.Request(next_url, callback=self.parse)

    def parse_answers(self, response):
        """
        Parse answers for each question.
        """
        item = response.meta['item']
        data = json.loads(response.text)
        answers = []
        answer_codes = []

        for ans in data.get('items', []):
            body = ans.get('body', '')
            answers.append(self.clean_html(body))
            answer_codes.extend(self.extract_code(body))

        item['answer'] = answers
        item['answer_code'] = answer_codes
        yield item

    # -------------------------------
    # Helper methods
    # -------------------------------
    def clean_html(self, html_text):
        """
        Remove HTML tags for clean text.
        """
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', html_text)
        return unescape(cleantext.strip())

    def extract_code(self, html_text):
        """
        Extract all <code>...</code> blocks.
        """
        return re.findall(r'<code>(.*?)</code>', html_text, re.DOTALL)

    def extract_quotes(self, html_text):
        """
        Extract all <blockquote>...</blockquote> sections.
        """
        quotes = re.findall(r'<blockquote>(.*?)</blockquote>', html_text, re.DOTALL)
        # Remove inner HTML tags inside blockquotes
        cleaned_quotes = [self.clean_html(q) for q in quotes]
        return cleaned_quotes

