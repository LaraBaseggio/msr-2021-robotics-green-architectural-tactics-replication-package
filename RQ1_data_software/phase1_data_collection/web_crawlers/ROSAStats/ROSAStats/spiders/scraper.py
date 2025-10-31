import scrapy
import json
import re
import os
from ROSAStats.items import RosaItem

class RosaBatchSpider(scrapy.Spider):
    name = "rosa_batch"
    allowed_domains = ["api.stackexchange.com"]

    API_KEY = "rl_u8yNRWLcWXZVUvFgQCyGt7GMy"
    MAX_BATCH_SIZE = 100 

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
        spider_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(spider_dir, '../../../../data/rosa_new_data.json')
        
        # This fix is critical for reading the standard array format JSON
        with open(json_path, "r") as f:
            url_data = json.load(f)
            
        all_urls = [item.get("url") for item in url_data if item and item.get("url")]

        # Extract question IDs
        self.question_ids = []
        for url in all_urls:
            match = re.search(r"/questions/(\d+)", url) or re.search(r"/question/(\d+)", url)
            if match:
                self.question_ids.append((match.group(1), url))

        # Initialize list to track missing question IDs
        self.all_missing_ids = []  # <--- CORRECTLY INITIALIZED

        # Prepare batches
        self.batches = [
            self.question_ids[i:i + self.MAX_BATCH_SIZE]
            for i in range(0, len(self.question_ids), self.MAX_BATCH_SIZE)
        ]

    def start_requests(self):
        for batch in self.batches:
            ids_str = ";".join([qid for qid, _ in batch])
            
            # FIX APPLIED: Added &pagesize=100 to the request URL
            url = f"https://api.stackexchange.com/2.3/questions/{ids_str}?order=desc&sort=creation&site=robotics&filter=withbody&pagesize=100"
            
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

        questions_by_id = {str(q.get("question_id")): q for q in questions}

        for qid, url in batch:
            if qid in questions_by_id:
                question = questions_by_id[qid]
                user = question.get("owner", {}).get("display_name", "")
                
                item = RosaItem()
                item["url"] = url
                item["user"] = user
                yield item
            else:
                # Track missing question
                self.all_missing_ids.append({"question_id": qid, "url": url})

        missing_count = len(batch) - len(questions_by_id)
        if missing_count > 0:
            self.logger.warning(f"Skipped {missing_count} missing/deleted questions in this batch")

    def closed(self, reason):
        """Called when spider is closed - save missing IDs to file"""
        if self.all_missing_ids:
            spider_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(spider_dir, '../../../../data/missing_questions.json')
            
            # Ensure the output directory exists before writing
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(self.all_missing_ids, f, indent=2)
            
            self.logger.info(f"Saved {len(self.all_missing_ids)} missing question IDs to {output_path}")