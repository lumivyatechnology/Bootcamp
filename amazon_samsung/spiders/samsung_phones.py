import time
import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class SamsungPhonesSpider(scrapy.Spider):
    name = "samsung_phones"

    # Keep it single-threaded because you use ONE shared self.driver
    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 0.2,
        "AUTOTHROTTLE_ENABLED": True,
    }

    handle_httpstatus_list = [503, 403, 429]

    max_pages = 10
    search_url = "https://www.amazon.com/s?k=samsung+phone&page={page}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        # opts.add_argument("--headless=new")

        opts.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=opts
        )

        # store links across pages
        self._seen_links = set()
        self._product_links = []

    def closed(self, reason):
        if getattr(self, "driver", None):
            self.driver.quit()

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        return text.replace('"', "").replace(",", "").strip()

    async def start(self):
        # start at page 1
        yield scrapy.Request(
            self.search_url.format(page=1),
            callback=self.parse_search,
            cb_kwargs={"page": 1},
            dont_filter=True,
        )

    def parse_search(self, response, page: int):
        self.logger.info(f"parse_search(page={page}) called (HTTP {response.status})")
        self.driver.get(response.url)

        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div.s-main-slot div[data-component-type='s-search-result']")
                )
            )
        except Exception:
            self.logger.warning(f"Search page {page} did not load properly; skipping.")
        else:
            # Collect product URLs from this page
            for a in self.driver.find_elements(By.CSS_SELECTOR, "div[data-cy='title-recipe'] a"):
                href = a.get_attribute("href")
                if href and href.startswith("http") and href not in self._seen_links:
                    self._seen_links.add(href)
                    self._product_links.append(href)

            self.logger.info(f"After page {page}: total unique products = {len(self._product_links)}")

        # Go to next search page until max_pages
        if page < self.max_pages:
            next_page = page + 1
            yield scrapy.Request(
                self.search_url.format(page=next_page),
                callback=self.parse_search,
                cb_kwargs={"page": next_page},
                dont_filter=True,
            )
            return

        # Once we've collected all pages, scrape product pages
        total = len(self._product_links)
        self.logger.info(f"Collected {total} unique product URLs from {self.max_pages} pages. Scraping products now...")

        for i, url in enumerate(self._product_links, start=1):
            yield scrapy.Request(
                url,
                callback=self.parse_product,
                cb_kwargs={"index": i, "total": total},
                dont_filter=True,
            )

    def parse_product(self, response, index, total):
        self.logger.info(f"[{index}/{total}] Loading {response.url}")
        self.driver.get(response.url)

        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "productTitle"))
            )
        except Exception:
            self.logger.warning("Product page timeout; skipping.")
            return

        def txt(sel):
            try:
                return self.driver.find_element(By.CSS_SELECTOR, sel).text.strip()
            except Exception:
                return ""

        def price():
            for s in self.driver.find_elements(By.CSS_SELECTOR, "span.a-price span.a-offscreen"):
                t = s.text.strip()
                if t:
                    return t
            return ""
        def ratings_count():
            """e.g. '1,234' from review count"""
            try:
                text = self.driver.find_element(By.CSS_SELECTOR, "#acrCustomerReviewText").text.strip()
                return text.split()[0].replace(",", "")
            except Exception:
                return ""

        raw_name = txt("#productTitle")
        clean_name = self.clean_text(raw_name)

        item = {
            "name": clean_name,
            "price": price(),
            "brand": txt(".po-brand .po-break-word"),
            "operating_system": txt(".po-operating_system .po-break-word"),
            "ram": txt(r".po-ram_memory\.installed_size .po-break-word"),
            "cpu_model": txt(r".po-cpu_model\.family .po-break-word"),
            "cpu_speed": txt(r".po-cpu_model\.speed .po-break-word"),
            "ratings_count": ratings_count(),
            
            "url": self.driver.current_url,
        }

        yield item

        print("-" * 80)
        time.sleep(1.5)
