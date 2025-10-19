import scrapy
import json
import re
from html import unescape
from SOWebCrawler.items import SOItem


class SOSpider(scrapy.Spider):
    name = "stackoverflow"
    allowed_domains = ["api.stackexchange.com"]
    
    # Stack Exchange API endpoint for newest questions tagged 'ros'
    start_urls = [
        "https://api.stackexchange.com/2.3/questions?order=desc&sort=creation&tagged=ros&site=stackoverflow&pagesize=50&filter=withbody"
    ]

    def parse(self, response):
        data = json.loads(response.text)
        questions = data.get('items', [])

        for q in questions:
            item = SOItem()
            item['title'] = unescape(q.get('title', ''))
            item['time'] = q.get('creation_date')  # Unix timestamp
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
                    f"?order=desc&sort=creation&site=stackoverflow&filter=withbody"
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

        # Pagination if more results exist
        if data.get('has_more'):
            next_page = int(response.url.split("&page=")[-1]) + 1 if "&page=" in response.url else 2
            next_url = (
                f"https://api.stackexchange.com/2.3/questions?"
                f"order=desc&sort=creation&tagged=ros&site=stackoverflow"
                f"&pagesize=50&page={next_page}&filter=withbody"
            )
            yield scrapy.Request(next_url, callback=self.parse)

    def parse_answers(self, response):
        """Parse answers for each question."""
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
        """Remove HTML tags for clean text."""
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', html_text)
        return unescape(cleantext.strip())

    def extract_code(self, html_text):
        """Extract all <code>...</code> blocks."""
        return re.findall(r'<code>(.*?)</code>', html_text, re.DOTALL)

    def extract_quotes(self, html_text):
        """Extract all <blockquote>...</blockquote> sections."""
        quotes = re.findall(r'<blockquote>(.*?)</blockquote>', html_text, re.DOTALL)
        # Remove inner HTML tags inside blockquotes
        cleaned_quotes = [self.clean_html(q) for q in quotes]
        return cleaned_quotes
