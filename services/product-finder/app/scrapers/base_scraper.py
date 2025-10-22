import requests
import logging
import time
import random
import os
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

logger = logging.getLogger('base_scraper')

# Tunables via .env (with safe defaults)
DEFAULT_TIMEOUT = float(os.getenv("SCRAPER_TIMEOUT", "25"))     # seconds
MAX_RETRIES     = int(os.getenv("SCRAPER_RETRIES", "3"))
PROXY_HTTP      = os.getenv("SCRAPER_HTTP_PROXY")               # e.g. http://user:pass@host:port
PROXY_HTTPS     = os.getenv("SCRAPER_HTTPS_PROXY")              # e.g. https://user:pass@host:port
RAW_COOKIES     = os.getenv("SCRAPER_COOKIES")                  # "k=v; k2=v2"


class BaseScraper:
    """Base class for web scrapers"""

    def __init__(self, use_selenium=False, cache_dir=None):
        self.use_selenium = use_selenium

        # Default user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15'
        ]

        # Cache
        if cache_dir is None:
            self.cache_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'cache',
                'scrapes'
            )
        else:
            self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

        # Requests session with retries/backoff
        self.session = requests.Session()
        retries = Retry(
            total=MAX_RETRIES,
            backoff_factor=0.8,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))

        # Proxies/cookies
        self.proxies = {}
        if PROXY_HTTP or PROXY_HTTPS:
            self.proxies = {"http": PROXY_HTTP, "https": PROXY_HTTPS}

        self.cookies = {}
        if RAW_COOKIES:
            try:
                self.cookies = dict(
                    [c.strip().split("=", 1) for c in RAW_COOKIES.split(";") if "=" in c]
                )
            except Exception:
                logger.warning("SCRAPER_COOKIES is malformed; ignoring.")

    # ------------------------------------------------------------------

    def get_page_content(self, url, force_refresh=False, cache_timeout_hours=24):
        """Fetch HTML with cache, retries, and optional Selenium fallback"""
        clean_url = (
            url.replace('https://', '')
               .replace('http://', '')
               .replace('/', '_')
               .replace('?', '_')
               .replace('=', '_')
        )
        cache_file = os.path.join(self.cache_dir, f"{clean_url}.html")

        # Serve cached version
        if os.path.exists(cache_file) and not force_refresh:
            file_age_hours = (time.time() - os.path.getmtime(cache_file)) / 3600
            if file_age_hours < cache_timeout_hours:
                logger.info(f"Using cached content for {url}")
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    logger.error(f"Error reading cache file: {e}")

        logger.info(f"Fetching content for {url}")

        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/'
        }

        # --- Retry loop with fallback ---
        attempts = MAX_RETRIES
        last_err = None

        for i in range(attempts):
            try:
                time.sleep(random.uniform(0.8, 1.8))

                if self.use_selenium and i == attempts - 1:
                    logger.info(f"Final attempt with Selenium for {url}")
                    html = self._get_with_selenium(url)
                else:
                    resp = self.session.get(
                        url,
                        headers=headers,
                        timeout=DEFAULT_TIMEOUT,
                        proxies=self.proxies or None,
                        cookies=self.cookies or None,
                    )
                    if resp.status_code == 503:
                        raise Exception("HTTP 503")
                    resp.raise_for_status()
                    html = resp.text

                if html and len(html) > 200:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        f.write(html)
                    return html

            except Exception as e:
                last_err = e
                logger.warning(f"Attempt {i+1}/{attempts} failed for {url}: {e}")
                # switch to Selenium for last retry
                if i == attempts - 2:
                    try:
                        import selenium  # noqa
                        self.use_selenium = True
                    except Exception:
                        pass
                headers['User-Agent'] = random.choice(self.user_agents)

        logger.error(f"Failed all {attempts} attempts for {url}: {last_err}")
        return None

    # ------------------------------------------------------------------

    def _get_with_selenium(self, url):
        """Load page using Selenium"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager

            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"user-agent={random.choice(self.user_agents)}")

            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(url)
            time.sleep(3)
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(2)
            except Exception:
                pass
            html = driver.page_source
            driver.quit()
            return html
        except ImportError:
            logger.error("Selenium not installed; falling back to requests")
            return None
        except Exception as e:
            logger.error(f"Selenium error for {url}: {e}")
            return None

    # ------------------------------------------------------------------

    def parse_html(self, html):
        if not html:
            return None
        try:
            return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return None

    def search_products(self, query, limit=5):
        raise NotImplementedError("Child classes must implement search_products")

    def generate_fake_products(self, query, limit=5, source="generic"):
        products = []
        for i in range(min(limit, 5)):
            products.append({
                "title": f"{source.title()} {query.title()} - Model {i+1}",
                "price": round(random.uniform(10, 500), 2),
                "image": f"https://placehold.co/400x400?text={source}+{i+1}",
                "url": f"https://www.{source.lower()}.com/search?q={query.replace(' ', '+')}",
                "description": f"Sample {query} product from {source}",
                "source": source.lower(),
                "category": query
            })
        return products
