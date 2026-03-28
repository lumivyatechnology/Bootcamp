# 📚 Get Started Guide

This guide will help you set up your development environment and get started with the projects in this bootcamp.

---

## 1. Prerequisites

Make sure you have the following tools installed before you begin:

| Tool | Version | Notes |
|------|---------|-------|
| Python | >= 3.10 | Use [pyenv](https://github.com/pyenv/pyenv) to manage versions (recommended) |
| Node.js | >= 20.9.0 | Use [nvm](https://github.com/nvm-sh/nvm) to manage versions (recommended) |
| npm | Bundled with Node.js | — |
| uv | Latest | Python package manager |
| Git | Latest | Version control |
| VS Code | Latest | Recommended editor — [download here](https://code.visualstudio.com/) |
| Postman | Latest | API testing (optional but recommended) |
| Docker | Latest | Containerization (optional but recommended) |

Inside the project root directory `Bootcamp`  
Create a virtual environment using uv which will later be used in jupyter notebooks.
```
uv venv --python 3.12
```
---

## 2. Scrape the Data

The scraper collects **Samsung phone listings from Amazon** — pulling key specs (name, price, brand, OS, RAM, CPU details, ratings count, URL) from both search result pages and individual product pages.

**Stack:** [Scrapy](https://scrapy.org/) for crawling + [Selenium](https://www.selenium.dev/) (Chrome WebDriver) for rendering dynamic content.

> ⚠️ Amazon may block automated traffic, show CAPTCHAs, or return partial data. Always comply with the site's Terms of Service and applicable laws.

### Folder Structure

```
data_acquisition/
├── amazon_samsung/
│   ├── __init__.py
│   ├── items.py
│   ├── middlewares.py
│   ├── pipelines.py
│   ├── settings.py
│   └── spiders/
│       ├── __init__.py
│       └── samsung_phones.py   ← spider must live here
├── env/                        # optional virtual environment
├── scrapy.cfg
└── samsung_phones_specs.csv    # example output
```

### Requirements

- Python 3.9+ (3.10+ recommended)
- Google Chrome installed
- Python packages: `scrapy`, `selenium`, `webdriver-manager`, `scrapy-fake-useragent`

### Setup

```bash
# Navigate to the data acquisition directory
cd data_acquisition

# Create and activate a virtual environment
uv venv --python 3.12

#activate
source .venv/bin/activate

# Install dependencies
uv pip install scrapy selenium webdriver-manager scrapy-fake-useragent
```

### Running the Spider

```bash
# Export to CSV (overwrites existing file)
uv run scrapy crawl samsung_phones -O samsung_phones_specs.csv

# Export to JSON
uv run scrapy crawl samsung_phones -O samsung_phones_specs.json
```

> Use `-o` instead of `-O` to append to an existing file rather than overwrite it.

### Configuration

In `amazon_samsung/spiders/samsung_phones.py`:

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
The scraped data is raw data which needs to be cleaned before we can use it for our mobile phone data analyzer system, so we will perform data cleaning and normalization to make this data ready for our further AI operations. 

### Steps
1. Navigate to **data_processing** and populate the .env file considering .env.example.
2. Run the cells in **etl.ipynb** to run the extract, transform, normalize and load the raw data into our postgresql database.

---

## 4. Run the Chatbot Frontend

```bash
# Navigate to the frontend directory
cd data_bot/ui

# Copy the example env file and fill in your values
cp .env.example .env

# Install dependencies
npm install

# Start the development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to view the app.

---

## 5. Run the Chatbot Backend

```bash
# Navigate to the backend directory
cd data_bot/analytics_agent

# Copy the example env file and fill in your values
cp .env.example .env
```

Edit the `.env` file with your credentials:

```env
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_BASE_URL=https://cloud.langfuse.com
GROQ_API_KEY=your_groq_key
DATA_BASE_PATH=
POSTGRES_USER=postgres
POSTGRES_PASSWORD=root
POSTGRES_DB=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

```bash
# Install dependencies
uv sync && uv sync --dev

# Start the server
uv run --env-file .env src/main.py

#If you have make installed locally, you can also use make commands to run this directly
make run_ui_backend
```

The backend will be available at [http://localhost:3050](http://localhost:3050). You can test the API using Postman or any HTTP client.

---

## 6. Containerize the Backend for Production
Docker is used for containerization of the application backend file, and we use the following commands for dockerization. We containerize an app and then use it in production.
```
To build the image
docker build -t analytics_agent .

To run the container
docker run --env-file .env -p 3050:3050 --name analytics_agent analytics_agent

You can also use docker compose to run the container
docker compose up --build
```
