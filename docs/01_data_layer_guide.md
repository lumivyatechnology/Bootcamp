# 01 — Data Layer Guide: From Raw Scraping to Normalized Database

> **Session:** 10:50–11:35 — Data Layer (Data fundamentals, scraping, cleaning, normalization pipeline)

---

## 1. The Scraper: What It Does and How

### Files Involved

| File | Purpose |
|---|---|
| `data_acquisition/amazon_samsung/spiders/samsung_phones.py` | The main spider — crawls Amazon, extracts phone specs |
| `data_acquisition/amazon_samsung/settings.py` | Scrapy settings — concurrency, delays, user-agent rotation |
| `data_acquisition/amazon_samsung/pipelines.py` | Item pipeline — currently pass-through (items flow directly to CSV) |
| `data_acquisition/amazon_samsung/middlewares.py` | Middleware hooks — default Scrapy scaffolding |
| `data_acquisition/scrapy.cfg` | Tells Scrapy where to find the project settings |

### What It Scrapes

The spider crawls **Amazon search results for "samsung phone"** across 10 pages, then visits each individual product page to extract detailed specifications.

**Search URL pattern:** `https://www.amazon.com/s?k=samsung+phone&page={page}`

### Two-Phase Crawl Strategy

**Phase 1 — Collect product URLs (pages 1–10):**
- Scrapy sends a request to each search page
- Selenium renders the page in Chrome (Amazon uses heavy JavaScript)
- Product URLs are extracted from `div[data-cy='title-recipe'] a` links
- URLs are de-duplicated and stored in a list

**Phase 2 — Scrape each product page:**
- For each collected URL, Selenium navigates to the product page
- Waits up to 15 seconds for `#productTitle` to appear
- Extracts 9 fields using CSS selectors:

| Field | CSS Selector | Example Value |
|---|---|---|
| `name` | `#productTitle` | `"Samsung Galaxy S25 FE Cell Phone (2025) 256GB..."` |
| `price` | `span.a-price span.a-offscreen` | `"$402.00"` |
| `brand` | `.po-brand .po-break-word` | `"Samsung"` |
| `operating_system` | `.po-operating_system .po-break-word` | `"Android 16, One UI 8"` |
| `ram` | `.po-ram_memory\.installed_size .po-break-word` | `"8 GB"` |
| `cpu_model` | `.po-cpu_model\.family .po-break-word` | `"Exynos 2400 S5E9945"` |
| `cpu_speed` | `.po-cpu_model\.speed .po-break-word` | `"3.39 GHz"` |
| `ratings_count` | `#acrCustomerReviewText` | `"3,896"` |
| `url` | `driver.current_url` | `"https://www.amazon.com/..."` |

### Key Code Snippet — Product Extraction

From `data_acquisition/amazon_samsung/spiders/samsung_phones.py`:

```python
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
```

### Key Scrapy Settings

| Setting | Value | Why |
|---|---|---|
| `CONCURRENT_REQUESTS` | `1` | Single shared Selenium driver — must be sequential |
| `DOWNLOAD_DELAY` | `2.0s` (in settings) / `0.2s` + autothrottle (in spider) | Avoid Amazon rate-limiting |
| `ROBOTSTXT_OBEY` | `False` | Amazon's robots.txt would block all crawling |
| `FAKEUSERAGENT` | Enabled | Rotates browser User-Agent headers to reduce detection |
| `RETRY_ENABLED` | `False` | Avoids retry storms on blocked requests |

### How to Run the Scraper

```bash
cd data_acquisition
uv pip install scrapy selenium webdriver-manager scrapy-fake-useragent
uv run scrapy crawl samsung_phones -O samsung_phones_specs.csv
```

---

## 2. Raw Data vs. Cleaned/Normalized Data — Before and After

### BEFORE: Raw CSV (`samsung_phones_specs.csv`)

Here's what the raw scraped data actually looks like:

```csv
name,price,brand,operating_system,ram,cpu_model,cpu_speed,ratings_count,url
Scosche MAGDMB MagicMount Magnetic Phone Mount...,,Scosche,,,,,(55803),https://...
Samsung Galaxy S25 Ultra 5G User Guide...,,,,,,,(25),https://...
Samsung EP-DG930 1.5m USB A USB C Male Male Black USB Cable,,Samsung,,,,,(98),https://...
Amazon Basics 10W Qi Certified Wireless Charging Stand...,,Amazon Basics,,,,,(5329),https://...
```

**Problems visible immediately:**
1. **Non-phone products mixed in** — phone cases, cables, chargers, books, USB adapters
2. **Most prices are missing** — empty fields everywhere
3. **Inconsistent brands** — "Scosche", "Amazon Basics", "Head Case Designs", "STENES", "PopSockets"
4. **No specs for non-phones** — RAM, CPU model, CPU speed are all blank
5. **Ratings format is messy** — some have parentheses like `(55803)`, some don't
6. **Duplicate products** — same items appear across different search pages
7. **Flat structure** — brand "Samsung" repeated on every Samsung row

### AFTER: Normalized Tables (5 CSV files in `data_processing/dataset/`)

**brands.csv:**
```csv
brand_id,brand_name
1,Samsung
2,Unknown
3,Verizon
4,TracFone
5,Motorola
```

**operating_systems.csv:**
```csv
os_id,os_name
1,"Android 16.0, One UI 8"
2,Not Specified
3,Android
4,"Android 14, One UI 6.1"
5,Android 14
6,"Android 15, One UI 7"
```

**cpu_models.csv:**
```csv
cpu_id,cpu_model
1,Exynos 2400 S5E9945
2,Not Specified
3,Snapdragon
6,Snapdragon 8 Elite
```

**phones.csv (main table):**
```csv
phone_id,name,price,brand_id,os_id,ratings_count,url
1,Samsung Galaxy S25 FE Cell Phone...,402.0,1,1,3896,https://...
4,Samsung Galaxy Z Flip 6 5G...,406.0,1,3,69,https://...
8,Samsung Galaxy S24 Cell Phone...,914.0,1,4,1051,https://...
```

**phone_specs.csv:**
```csv
spec_id,phone_id,ram,cpu_id,cpu_speed
1,1,8 GB,1,Not Specified
4,4,12 GB,3,3.39 GHz
8,8,8 GB,3,Not Specified
```

---

## 3. What the Normalization Script Does Step by Step

**File:** `data_acquisition/amazon_samsung/normalization.ipynb` (and `data_processing/normalization.ipynb`)

### Step 1: Load the Raw CSV
```python
df = pd.read_csv("samsung_phones_specs.csv")
```
Reads the flat CSV into a Pandas DataFrame. Inspects shape, column names, and data types.

### Step 2: Handle Missing Prices
```python
# Fill null prices with random values between $300-$1000
df['price'] = df['price'].apply(lambda x: np.random.randint(300, 1001) if pd.isna(x) else x)
```
Since many prices are missing (Amazon doesn't always show price on the listing page), the notebook fills them with random realistic values for demo purposes.

### Step 3: Fill Other Missing Values
```python
# Replace blanks with meaningful defaults
df['brand'].fillna('Unknown', inplace=True)
df['operating_system'].fillna('Not Specified', inplace=True)
df['cpu_model'].fillna('Not Specified', inplace=True)
df['ram'].fillna('Not Specified', inplace=True)
df['cpu_speed'].fillna('Not Specified', inplace=True)
```

### Step 4: Clean Ratings Count
```python
# Remove parentheses and commas, convert to integer
# "(55,803)" → 55803
df['ratings_count'] = df['ratings_count'].str.replace(r'[(),]', '', regex=True).astype(int)
```

### Step 5: Extract Lookup Tables (Normalization to 3NF)

**Brands table:**
```python
brands_df = df[['brand']].drop_duplicates().reset_index(drop=True)
brands_df['brand_id'] = range(1, len(brands_df) + 1)
```

**Operating Systems table:**
```python
os_df = df[['operating_system']].drop_duplicates().reset_index(drop=True)
os_df['os_id'] = range(1, len(os_df) + 1)
```

**CPU Models table:**
```python
cpu_df = df[['cpu_model']].drop_duplicates().reset_index(drop=True)
cpu_df['cpu_id'] = range(1, len(cpu_df) + 1)
```

### Step 6: Build Phones Table with Foreign Keys
```python
# Replace string values with integer IDs
phones_df = df.merge(brands_df, on='brand').merge(os_df, on='operating_system')
phones_df = phones_df[['phone_id', 'name', 'price', 'brand_id', 'os_id', 'ratings_count', 'url']]
```

### Step 7: Build Phone Specs Table
```python
specs_df = df.merge(cpu_df, on='cpu_model')
specs_df = specs_df[['spec_id', 'phone_id', 'ram', 'cpu_id', 'cpu_speed']]
```

### Step 8: Save to CSV Files
```python
brands_df.to_csv('dataset/brands.csv', index=False)
os_df.to_csv('dataset/operating_systems.csv', index=False)
cpu_df.to_csv('dataset/cpu_models.csv', index=False)
phones_df.to_csv('dataset/phones.csv', index=False)
specs_df.to_csv('dataset/phone_specs.csv', index=False)
```

### Step 9: Load into PostgreSQL
```python
from sqlalchemy import create_engine
engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{dbname}")
brands_df.to_sql('brands', engine, if_exists='replace', index=False)
# ... same for all 5 tables
```

---

## 4. The Database Schema

After normalization, the data lives in 5 related tables following Third Normal Form (3NF):

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│   brands     │     │     phones        │     │ phone_specs   │
├─────────────┤     ├──────────────────┤     ├──────────────┤
│ brand_id PK │◄────│ brand_id FK       │     │ spec_id PK   │
│ brand_name  │     │ phone_id PK       │◄────│ phone_id FK  │
└─────────────┘     │ name              │     │ ram          │
                    │ price             │     │ cpu_id FK    │──┐
┌─────────────┐     │ os_id FK          │     │ cpu_speed    │  │
│ operating_  │     │ ratings_count     │     └──────────────┘  │
│ systems     │     │ url               │                       │
├─────────────┤     └──────────────────┘     ┌──────────────┐  │
│ os_id PK    │◄────────────┘                 │ cpu_models   │  │
│ os_name     │                               ├──────────────┤  │
└─────────────┘                               │ cpu_id PK    │◄─┘
                                              │ cpu_model    │
                                              └──────────────┘
```

### Table Details

| Table | Columns | Row Count (approx.) | Purpose |
|---|---|---|---|
| `brands` | `brand_id`, `brand_name` | ~5–10 | Lookup: unique brand names |
| `operating_systems` | `os_id`, `os_name` | ~14 | Lookup: unique OS versions |
| `cpu_models` | `cpu_id`, `cpu_model` | ~14 | Lookup: unique CPU families |
| `phones` | `phone_id`, `name`, `price`, `brand_id`, `os_id`, `ratings_count`, `url` | ~200+ | Main product table |
| `phone_specs` | `spec_id`, `phone_id`, `ram`, `cpu_id`, `cpu_speed` | ~200+ | Technical specs per phone |

### Normalization Concepts Applied

| Normal Form | What Was Fixed |
|---|---|
| **1NF** | Each column holds a single atomic value — no lists, no repeating groups |
| **2NF** | Non-key attributes depend on the full primary key, not partial keys |
| **3NF** | Transitive dependencies removed: brand, OS, and CPU are in their own tables instead of being repeated on every phone row |

---

## 5. Talking Points: Why Raw Data Is Not Intelligence

### Talking Point 1: "Garbage In, Garbage Out"
> "Look at this raw CSV — phone cases, USB cables, and books mixed in with actual phones. If we fed this to an AI model, it would recommend you a phone case when you asked for a phone. The data pipeline exists so the AI doesn't have to guess."

### Talking Point 2: "Missing Values Are Silent Killers"
> "90% of the prices are missing. If someone asks 'what's the cheapest phone?', the AI would say $0.00 — because blanks become zeros. This is why cleaning data matters more than building fancy models."

### Talking Point 3: "Flat Doesn't Scale"
> "The string 'Samsung' appears 150 times in the raw CSV. If Samsung changes its name tomorrow, you update 150 rows. In a normalized database, you update one row in the brands table. That's the difference between a CSV and a database."

### Talking Point 4: "Structure Enables Questions"
> "With raw data, you can't ask 'how many phones does each brand have?' because brand is just a text field. With normalized data, you JOIN phones to brands and GROUP BY — done. Structure is what turns data into something you can ask questions about."

### Talking Point 5: "The AI Needs Schema, Not Strings"
> "The AI agent in this system reads the database schema (CREATE TABLE statements) to understand what data exists. It can't do that with a messy CSV. The normalization step is what makes the data queryable by an AI."

---

## 6. One-Paragraph Verbal Explanation (Say This Out Loud)

> "Here's the journey your data takes. We start by scraping Samsung phone listings from Amazon — about 200 products across 10 search pages. But the raw data is a mess: missing prices, USB cables mixed in with actual phones, inconsistent brand names. So we run it through a normalization pipeline that cleans the data, fills in missing values, and splits it into five related tables — brands, operating systems, CPU models, phones, and phone specs. These tables follow what's called Third Normal Form, which means no duplicate information and clean relationships. We save these tables into PostgreSQL, and that's what the AI agent queries when you ask it a question. The key takeaway: raw data is not intelligence. The pipeline that transforms it is what makes AI possible."

---

## Demo Risk Flags

| Risk | Impact | Mitigation |
|---|---|---|
| **Scraper breaks during live demo** | Amazon can block requests, change HTML, or show CAPTCHAs at any time | Never run the scraper live. Use the pre-existing CSV. Show the spider code and explain what it does. |
| **Raw CSV has changed since last scrape** | Data might look different than what normalization expects | Keep a known-good copy of `samsung_phones_specs.csv` as backup |
| **Normalization notebook has cell execution errors** | Pandas version differences or missing dependencies | Run the notebook end-to-end before the bootcamp and confirm all cells pass |
| **PostgreSQL tables are empty** | Agent will return "no data" when queried | Run the notebook's PostgreSQL loading step before the demo |
| **CSV files in `dataset/` are stale or missing** | DuckDB backup path won't work | Verify all 5 files exist: `ls data_processing/dataset/` |
| **normalization.ipynb exists in two locations** | Confusion about which is the "real" one | The one in `data_processing/` is the canonical version; `amazon_samsung/normalization.ipynb` may be a working copy |
