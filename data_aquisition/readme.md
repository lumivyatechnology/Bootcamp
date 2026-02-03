# Amazon Samsung Phones Scraper (Scrapy + Selenium)

This project scrapes **Samsung phone listings from Amazon search pages** and then visits each product page to extract key specs (name, price, brand, OS, RAM, CPU details, ratings count, URL). It uses:

- **Scrapy** for crawling/orchestration and exporting data
- **Selenium (Chrome WebDriver)** for rendering Amazon pages (dynamic content)

> ⚠️ Note: Amazon may block automated traffic, show CAPTCHAs, or return partial data. Always follow the website’s Terms of Service and applicable laws.

---

## Features

- Collects product links from multiple Amazon search pages (`max_pages`)
- Visits each product page and extracts:
  - `name`, `price`, `brand`, `operating_system`, `ram`, `cpu_model`, `cpu_speed`, `ratings_count`, `url`
- Exports to CSV/JSON using Scrapy output options

---

## Folder Structure

Recommended Scrapy structure:

```text
amazon_samsung/
├── amazon_samsung/
│   ├── __init__.py
│   ├── items.py
│   ├── middlewares.py
│   ├── pipelines.py
│   ├── settings.py
│   └── spiders/
│       ├── __init__.py
│       └── samsung_phones.py
├── env/                      # (optional) virtual environment folder
├── scrapy.cfg
└── samsung_phones_specs.csv  # output file (example)
```

✅ **Important:** Your spider file should be inside:  
`amazon_samsung/spiders/samsung_phones.py`

If your `samsung_phones.py` is currently outside the `spiders/` folder, move it there (recommended) so `scrapy crawl samsung_phones` works properly.

---

## Requirements

- Python **3.9+** (recommended 3.10+)
- Google Chrome installed
- Packages:
  - `scrapy`
  - `selenium`
  - `webdriver-manager`

---

## Setup

### 1) Create and activate a virtual environment

**macOS/Linux**
```bash
uv venv
```

**Windows (PowerShell)**
```powershell
uv venv
```

### 2) Install dependencies

```bash
uv pip install scrapy selenium webdriver-manager scrapy-fake-useragent 
```

---

## How to Run

### Option A (Recommended): Run as a Scrapy spider

From the project root (where `scrapy.cfg` is):

```bash
uv run scrapy crawl samsung_phones -O samsung_phones_specs.csv

```

- `-O` overwrites the file  
- Use `-o` to append instead

Export JSON:

```bash
uv run scrapy crawl samsung_phones -O samsung_phones_specs.json
```


---

## Configuration

In `samsung_phones.py`:

```python
max_pages = 10
search_url = "https://www.amazon.com/s?k=samsung+phone&page={page}"
```

Change `max_pages` to scrape more/less search pages.

### Headless Mode (optional)

You have:

```python
# opts.add_argument("--headless=new")
```

Uncomment it to run Chrome without opening a browser window.

---

## Output Fields

Each item contains:

```json
{
  "name": "Samsung ...",
  "price": "$199.99",
  "brand": "SAMSUNG",
  "operating_system": "Android",
  "ram": "8 GB",
  "cpu_model": "...",
  "cpu_speed": "...",
  "ratings_count": "1234",
  "url": "https://www.amazon.com/..."
}
```

---

## Notes / Known Limitations

- Amazon pages can vary by region/account/session, so some selectors may fail.
- This spider uses **one shared Selenium driver**, so concurrency is set to **1**:
  ```python
  "CONCURRENT_REQUESTS": 1,
  "CONCURRENT_REQUESTS_PER_DOMAIN": 1
  ```
- Scraping too fast can lead to blocks or CAPTCHAs. Be respectful.




