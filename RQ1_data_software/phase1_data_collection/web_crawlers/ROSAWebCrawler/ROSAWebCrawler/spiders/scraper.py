import scrapy, json, re
from html import unescape
from datetime import datetime
from ROSAWebCrawler.items import ROSAItem


class ROSASpider(scrapy.Spider):
    name = "ros-answers"
    allowed_domains = ["api.stackexchange.com"]

    API_KEY = "rl_u8yNRWLcWXZVUvFgQCyGt7GMy"  # optional
    BASE_URL = (
        "https://api.stackexchange.com/2.3/questions?"
        "order=desc&sort=creation&site=robotics&pagesize=100&page={page}"
        "&filter=withbody"
    )

    if API_KEY:
        BASE_URL += f"&key={API_KEY}"

    start_urls = [BASE_URL.format(page=1)]

    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 2,
        "AUTOTHROTTLE_MAX_DELAY": 10,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1,
        "CONCURRENT_REQUESTS": 1,
        "RETRY_TIMES": 3,
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        ),
    }

    def parse(self, response):
        """Parse one page of questions."""
        data = json.loads(response.text)
        questions = data.get("items", [])
      #  self.logger.info(f"Fetched {len(questions)} questions from {response.url}")

        for q in questions:
            question_id = q["question_id"]

            item = ROSAItem()
            item["title"] = unescape(q.get("title", ""))
            item["time"] = datetime.utcfromtimestamp(
                q.get("creation_date", 0)
            ).strftime("%Y-%m-%d %H:%M:%S")
            item["post_content"] = [self.clean_html(q.get("body", ""))]
            item["question_details"] = self.extract_list_items(q.get("body", ""))
            item["url"] = q.get("link", "")

            # Request answers for this question (even if 0)
            api_url = (
                f"https://api.stackexchange.com/2.3/questions/{question_id}/answers"
                f"?order=desc&sort=creation&site=robotics&filter=withbody"
            )
            if self.API_KEY:
                api_url += f"&key={self.API_KEY}"

            yield scrapy.Request(
                api_url, callback=self.parse_answers, meta={"item": item}
            )

        # Pagination
        if data.get("has_more"):
            current_page = int(re.search(r"&page=(\d+)", response.url).group(1))
            next_page = current_page + 1
            next_url = re.sub(r"&page=\d+", f"&page={next_page}", response.url)
            yield scrapy.Request(next_url, callback=self.parse)

    def parse_answers(self, response):
        """Attach answers to the question item."""
        item = response.meta["item"]
        try:
            data = json.loads(response.text)
            answers = data.get("items", [])
            item["answer"] = [self.clean_html(a.get("body", "")) for a in answers]
        except Exception as e:
          #  self.logger.error(f"Error parsing answers: {e}")
            item["answer"] = []

        yield item

    # -------------------------------
    # Helper methods
    # -------------------------------
    def clean_html(self, html_text):
        """Remove tags and decode entities."""
        text = re.sub(r"<[^>]+>", "", html_text or "")
        return unescape(text).strip()

    def extract_list_items(self, html_text):
        """Extract bullet or numbered list items."""
        return re.findall(r"<li>(.*?)</li>", html_text or "", re.DOTALL)

    
'''Code that shows the redirection and then gets blocked 40 forbidden 
import scrapy
import re
import json
from scrapy.selector import Selector
from html import unescape
from ROSAWebCrawler.items import ROSAItem

class ROSASpider(scrapy.Spider):
    name = "ros-answers"
    allowed_domains = ["answers.ros.org", "robotics.stackexchange.com", "stackexchange.com", "api.stackexchange.com"]
    start_urls = ["https://answers.ros.org/questions/"]

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS": 1,
        "RETRY_TIMES": 3,
    }

    def parse(self, response):
        """Parse question listings page"""
        question_links = response.css("section.questions div.question > a:first-child::attr(href)").getall()
        self.logger.info(f"Found {len(question_links)} questions on {response.url}")

        for link in question_links:
            full_url = response.urljoin(link)
            yield scrapy.Request(url=full_url, callback=self.parse_detail)

        # Pagination
        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse)

    def parse_detail(self, response):
        """Parse individual question page"""
        url = response.url

        # Check if redirected to Stack Exchange - SKIP and log for debugging
        if any(domain in url for domain in ["stackexchange.com", "robotics.stackexchange.com"]):
            self.logger.info(f"SKIPPED - Redirected to Stack Exchange: {url}")
            return

        # ROS Answers HTML scraping
        try:
            item = ROSAItem()
            item["title"] = response.css("div#main div.question h2 a::text").get(default="").strip()
            item["post_content"] = [self.clean_html(p) for p in response.css("div#main div.question p").getall()]
            item["question_details"] = self.extract_list_items("".join(response.css("div#main div.question").getall()))
            item["comment"] = [self.clean_html(p) for p in response.css("div#main section.comments div.comment p").getall()]
            item["answer"] = [
                " ".join([p.strip() for p in a.css("p::text").getall() if p.strip()])
                for a in response.css("div#main section.answers div.answer")
            ]
            item["url"] = url
            
            if item["title"]:  # Only yield if we got a title
                self.logger.info(f"✓ Scraped: {item['title']} ({len(item['answer'])} answers)")
                yield item
            else:
                self.logger.warning(f"No title found for {url}")
        except Exception as e:
            self.logger.error(f"Error parsing {url}: {e}")

    # -------------------------------
    # Helper methods
    # -------------------------------
    def clean_html(self, html_text):
        """Remove HTML tags for clean text"""
        if not html_text:
            return ""
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', html_text)
        return unescape(cleantext.strip())

    def extract_list_items(self, html_text):
        """Extract <li> items from HTML body"""
        if not html_text:
            return []
        return [self.clean_html(li) for li in re.findall(r'<li>(.*?)</li>', html_text, re.DOTALL)]
'''