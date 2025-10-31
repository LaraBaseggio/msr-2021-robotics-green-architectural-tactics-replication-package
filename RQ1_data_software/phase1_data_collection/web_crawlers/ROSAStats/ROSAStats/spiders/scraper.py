import scrapy
import json
import re
from ROSAStats.items import RosaItem

class RosaBatchSpider(scrapy.Spider):
    name = "rosa_batch"
    allowed_domains = ["api.stackexchange.com"]

    API_KEY = "rl_u8yNRWLcWXZVUvFgQCyGt7GMy"
    MAX_BATCH_SIZE = 100  # Max IDs per request allowed by SE API

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

        # Load URLs from JSON
        self.json_path = "../../../../data/rosa_new_data.json"
        with open(self.json_path, "r") as f:
            url_data = [json.loads(line) for line in f if line.strip()]
        all_urls = [item.get("url") for item in url_data if item.get("url")]

        # Extract question IDs
        self.question_ids = []
        for url in all_urls:
            match = re.search(r"/questions/(\d+)", url) or re.search(r"/question/(\d+)", url)
            if match:
                self.question_ids.append((match.group(1), url))

        # Prepare batches
        self.batches = [
            self.question_ids[i:i + self.MAX_BATCH_SIZE]
            for i in range(0, len(self.question_ids), self.MAX_BATCH_SIZE)
        ]

    def start_requests(self):
        for batch in self.batches:
            ids_str = ";".join([qid for qid, _ in batch])
            url = f"https://api.stackexchange.com/2.3/questions/{ids_str}?order=desc&sort=creation&site=robotics&filter=withbody"
            if self.API_KEY:
                url += f"&key={self.API_KEY}"
            yield scrapy.Request(url, callback=self.parse, meta={"batch": batch})

    def parse(self, response):
        if response.status == 429:
            self.logger.error("Rate limit reached (429)")
            return

        data = json.loads(response.text)
        quota_remaining = data.get("quota_remaining")
        if quota_remaining is not None:
            self.logger.info(f"API quota remaining: {quota_remaining}")

        batch = response.meta["batch"]
        questions = data.get("items", [])

        returned_ids = set()
        for question in questions:
            qid = str(question.get("question_id"))
            returned_ids.add(qid)
            url = next((u for i, u in batch if i == qid), "")
            user = question.get("owner", {}).get("display_name", "")

            item = RosaItem()
            item["url"] = url
            item["user"] = user
            yield item

        # Optionally log missing/deleted questions
        original_ids = {qid for qid, _ in batch}
        missing_ids = original_ids - returned_ids
        if missing_ids:
            self.logger.warning(f"Skipped {len(missing_ids)} missing/deleted questions in batch")
