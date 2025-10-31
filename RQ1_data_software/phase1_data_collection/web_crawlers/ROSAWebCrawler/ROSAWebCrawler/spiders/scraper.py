import scrapy, json, re, os
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
        "DOWNLOAD_DELAY": 0.5,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 2,
        "AUTOTHROTTLE_MAX_DELAY": 10,
        "CONCURRENT_REQUESTS": 12,
        "RETRY_TIMES": 2,
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawled_ids = set()

        data_path = "../../../../data/rosa_new_data.json"
        if os.path.exists(data_path):
            try:
                with open(data_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                for item in existing_data:
                    # Extract numeric question_id from URL if present
                    if "url" in item:
                        m = re.search(r"/questions/(\d+)", item["url"])
                        if m:
                            self.crawled_ids.add(int(m.group(1)))
                self.logger.info(f"Loaded {len(self.crawled_ids)} previously crawled questions.")
            except Exception as e:
                self.logger.warning(f"Could not load existing data: {e}")

    def parse(self, response):
        """Parse one page of questions."""
        data = json.loads(response.text)
        questions = data.get("items", [])

        question_ids = []
        for q in questions:
            qid = q["question_id"]
            if qid in self.crawled_ids:
                continue  # skip already saved question

            question_ids.append(qid)

            item = ROSAItem()
            item["title"] = unescape(q.get("title", ""))
            item["time"] = datetime.utcfromtimestamp(
                q.get("creation_date", 0)
            ).strftime("%Y-%m-%d %H:%M:%S")
            item["post_content"] = [self.clean_html(q.get("body", ""))]
            item["question_details"] = self.extract_list_items(q.get("body", ""))
            item["url"] = q.get("link", "")

            if not hasattr(self, "question_cache"):
                self.question_cache = {}
            self.question_cache[qid] = item

        # If there are any uncrawled questions on this page
        if question_ids:
            ids_str = ";".join(map(str, question_ids))
            api_url = (
                f"https://api.stackexchange.com/2.3/questions/{ids_str}/answers"
                f"?order=desc&sort=creation&site=robotics&filter=withbody"
            )
            if self.API_KEY:
                api_url += f"&key={self.API_KEY}"

            yield scrapy.Request(
                api_url, callback=self.parse_answers_batch, meta={"question_ids": question_ids}
            )

        # Pagination
        if data.get("has_more"):
            current_page = int(re.search(r"&page=(\d+)", response.url).group(1))
            next_page = current_page + 1
            next_url = re.sub(r"&page=\d+", f"&page={next_page}", response.url)
            yield scrapy.Request(next_url, callback=self.parse)

    def parse_answers_batch(self, response):
        """Process answers for multiple questions at once."""
        question_ids = response.meta["question_ids"]

        try:
            data = json.loads(response.text)
            answers_by_question = {}

            # Group answers by question_id
            for answer in data.get("items", []):
                qid = answer.get("question_id")
                if qid not in answers_by_question:
                    answers_by_question[qid] = []
                answers_by_question[qid].append(self.clean_html(answer.get("body", "")))

            # Yield items with their answers
            for qid in question_ids:
                if qid in self.question_cache:
                    item = self.question_cache[qid]
                    item["answer"] = answers_by_question.get(qid, [])
                    yield item
                    del self.question_cache[qid]

        except Exception as e:
            self.logger.error(f"Error parsing batch answers: {e}")
            # Yield items without answers if error
            for qid in question_ids:
                if qid in self.question_cache:
                    item = self.question_cache[qid]
                    item["answer"] = []
                    yield item
                    del self.question_cache[qid]

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
