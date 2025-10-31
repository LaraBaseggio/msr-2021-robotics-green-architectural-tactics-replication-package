import scrapy
import json
from scrapy.spiders import CrawlSpider
from ROSDWebCrawler.items import ROSDItem

"""
Old code used to fetch: https://discourse.ros.org
This url has been modified -> redirected to https://discourse.openrobotics.org/

Old code: hardcoded 21 different categories
New code: changed all urls to the new categories/subcategories 
"""

class ROSDSpider(CrawlSpider):
    name = "ros-discourse"
    start_urls = ["https://discourse.openrobotics.org"]

    # Updated category URLs to crawl
    category_urls = [
        'https://discourse.openrobotics.org/c/archive/humanoids/35',
        'https://discourse.openrobotics.org/c/archive/robot-description-formats/7',
        'https://discourse.openrobotics.org/c/archive/ariac-users/24',
        'https://discourse.openrobotics.org/c/community-groups/marine-robotics/36',
        'https://discourse.openrobotics.org/c/community-groups/aerial-robotics/14',
        'https://discourse.openrobotics.org/c/turtlebot/12',
        'https://discourse.openrobotics.org/c/archive/perception/30',
        'https://discourse.openrobotics.org/c/community-groups/industrial/39',
        'https://discourse.openrobotics.org/c/archive/drivers/54',
        'https://discourse.openrobotics.org/c/infrastructure-project/infra-buildfarm/20',
        'https://discourse.openrobotics.org/c/archive/quality/37',
        'https://discourse.openrobotics.org/c/ros/release/16',
        'https://discourse.openrobotics.org/c/archive/embedded/9',
        'https://discourse.openrobotics.org/c/archive/multi-robot-systems/60',
        'https://discourse.openrobotics.org/c/community-groups/openembedded/26',
        'https://discourse.openrobotics.org/c/community-groups/manipulation/13',
        'https://discourse.openrobotics.org/c/ros/ros-general/8',
        'https://discourse.openrobotics.org/c/archive/autoware/46',
    ]

    def start_requests(self):
        """Fetch JSON feeds for all hardcoded categories with pagination."""
        for category_url in self.category_urls:
            # Fetch up to 20 pages per category (matching Code1's range(1,20))
            for page in range(0, 20):
                json_url = f"{category_url}/l/latest.json?page={page}"
                yield scrapy.Request(
                    json_url,
                    callback=self.parse_json,
                    dont_filter=True,
                    meta={'page': page, 'category_url': category_url}
                )

    def parse_json(self, response):
        """Parse JSON feed and extract topic URLs."""
        try:
            data = json.loads(response.text)
        except Exception as e:
            self.logger.warning(f"Failed to parse JSON from {response.url}: {e}")
            return

        topics = data.get("topic_list", {}).get("topics", [])
        
        if not topics:
            # No more topics on this page, stop paginating this category
            return

        base = "https://discourse.openrobotics.org"
        for topic in topics:
            slug = topic.get("slug")
            if slug:
                topic_url = f"{base}/t/{slug}"
                yield scrapy.Request(topic_url, callback=self.parse_detail_page)

    def parse_detail_page(self, response):
        """Extract data from individual topic pages."""
        item = ROSDItem()
        
        # Scrape title of post
        title = response.css("h1 > a::text").get()
        item["title"] = title
        
        # Scrape thread content
        thread_contents = response.css(".wrap p::text").getall()
        item["thread_contents"] = thread_contents
        
        # Scrape thread details
        temp = response.css("li::text").getall()
        if temp and not all(p.strip() == "" for p in temp):
            item["thread_details"] = temp

        item["url"] = response.url
        yield item