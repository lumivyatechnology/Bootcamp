# 📚 Get Started Guide

This guide will help you set up your development environment and get started with the projects in this bootcamp.

---

## 1. Prerequisites

Make sure you have the following tools installed before you begin:

| Tool    | Version              | Notes                                                                        |
| ------- | -------------------- | ---------------------------------------------------------------------------- |
| Python  | >= 3.10              | Use [pyenv](https://github.com/pyenv/pyenv) to manage versions (recommended) |
| Node.js | >= 20.9.0            | Use [nvm](https://github.com/nvm-sh/nvm) to manage versions (recommended)    |
| npm     | Bundled with Node.js | —                                                                            |
| uv      | Latest               | Python package manager                                                       |
| Git     | Latest               | Version control                                                              |
| VS Code | Latest               | Recommended editor — [download here](https://code.visualstudio.com/)         |
| Postman | Latest               | API testing (optional but recommended)                                       |
| Docker  | Latest               | Containerization (optional but recommended)                                  |

At the project root directory:
Create a virtual environment using uv which will later be used in jupyter notebooks.

```
# Create and activate a virtual environment
uv venv --python 3.12
uv sync

#activate
source .venv/bin/activate # for linux
.venv\Scripts\activate  # for windows

```

## 2. Scrape the Data

The scraper collects **Samsung phone listings from Amazon** — pulling key specs (name, price, brand, OS, RAM, CPU details, ratings count, URL) from both search result pages and individual product pages.

**Stack:** [Scrapy](https://scrapy.org/) for crawling + [Selenium](https://www.selenium.dev/) (Chrome WebDriver) for rendering dynamic content.

> ⚠️ Amazon may block automated traffic, show CAPTCHAs, or return partial data. Always comply with the site's Terms of Service and applicable laws.

### Requirements

- Python 3.9+ (3.10+ recommended)
- Google Chrome installed
- Python packages: `scrapy`, `selenium`, `webdriver-manager`, `scrapy-fake-useragent`

### Running the Spider

```bash
# Navigate to backend directory
cd backend

# Export to CSV (overwrites existing file)
uv run scrapy crawl samsung_phones -O samsung_phones_specs.csv

# Export to JSON
uv run scrapy crawl samsung_phones -O samsung_phones_specs.json
```

> Use `-o` instead of `-O` to append to an existing file rather than overwrite it.

### Configuration

In `backend/src/scraper/data_acquisition/amazon_samsung/spiders/samsung_phones.py`:

```python
max_pages = 10  # number of Amazon search pages to crawl
search_url = "https://www.amazon.com/s?k=samsung+phone&page={page}"
```

To run Chrome without opening a browser window, uncomment this line in the spider:

```python
# opts.add_argument("--headless=new")
```

### Output Format

```json
{
    "name": "Samsung Galaxy ...",
    "price": "$199.99",
    "brand": "SAMSUNG",
    "operating_system": "Android",
    "ram": "8 GB",
    "cpu_model": "Snapdragon ...",
    "cpu_speed": "3.2 GHz",
    "ratings_count": "1234",
    "url": "https://www.amazon.com/..."
}
```

### Known Limitations

- Amazon page structure varies by region, account, and session — some selectors may fail intermittently.
- The spider uses a **single shared Selenium driver**, so concurrency is limited to 1 request at a time.
- Scraping too fast may trigger blocks or CAPTCHAs — be respectful of rate limits.

---

## 3. Normalize and Load the Data

```bash
# Navigate to the backend directory
cd backend/

# Copy the example env file and fill in your values
cp .env.example .env
```

Edit the `.env` file with your credentials:

```env
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_BASE_URL=https://cloud.langfuse.com
GROQ_API_KEY=your_groq_key
DB_USER=postgres
DB_PASSWORD=root
DB_NAME=postgres
DB_HOST=localhost
DB_PORT=5432
```

The scraped data is raw data which needs to be cleaned before we can use it for our mobile phone data analyzer system, so we will perform data cleaning and normalization to make this data ready for our further AI operations.

### Steps

1. Navigate to **backend\src\scraper\data_ingestion** and populate the .env file considering .env.example.
2. Run the cells in **etl.ipynb** to run the extract, transform, normalize and load the raw data into our postgresql database.

---

## 4. Run the analytics agent notebook

### Steps

1. Navigate to **backend\ai-notebooks**.
2. Run the cells in **analytics_agent_cli.ipynb** to run the analytics agent and analyze the data loaded into the database.

---

## 5. Run the analytics agent cli

```bash

cd backend

# Start the server
uv run --env-file .env src/run_cli.py
```

---

## 6. Run the Chatbot Backend

```bash
# Install dependencies
uv sync && uv sync --dev

# Start the server
uv run --env-file .env src/main.py
```

The backend will be available at [http://localhost:3050](http://localhost:3050). You can test the API using Postman or any HTTP client.

---

## 7. Run the Chatbot Frontend

```bash
# Navigate to the frontend directory
cd frontend

# Copy the example env file and fill in your values
cp .env.example .env

# Install dependencies
npm install

# Start the development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to view the app.

---
