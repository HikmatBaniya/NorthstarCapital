from typing import Any, Dict, List
import time
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from ..config import Settings
from ..http_client import http_get, http_post


def _ddg_html_search(settings: Settings, query: str, max_results: int) -> List[Dict[str, Any]]:
    headers = {"User-Agent": settings.user_agent}
    response = http_post(
        settings,
        "https://duckduckgo.com/html/",
        data={"q": query},
        headers=headers,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    results: List[Dict[str, Any]] = []
    for result in soup.select("div.result"):
        link = result.select_one("a.result__a")
        snippet = result.select_one("a.result__snippet") or result.select_one("div.result__snippet")
        if not link:
            continue
        results.append(
            {
                "title": link.get_text(strip=True),
                "href": link.get("href"),
                "body": snippet.get_text(strip=True) if snippet else "",
            }
        )
        if len(results) >= max_results:
            break
    return results


def web_search(settings: Settings, query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    try:
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                results.append(
                    {
                        "title": item.get("title"),
                        "href": item.get("href"),
                        "body": item.get("body"),
                    }
                )
        if results:
            return results
    except Exception:
        pass
    return _ddg_html_search(settings, query, max_results)


def _browser_headers() -> Dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }


def web_fetch(settings: Settings, url: str, headers: Dict[str, str] | None = None) -> Dict[str, Any]:
    merged = {"User-Agent": settings.user_agent}
    if headers:
        merged.update(headers)
    response = http_get(settings, url, headers=merged, cache_ttl=60)
    response.raise_for_status()
    return {
        "url": response.url,
        "status_code": response.status_code,
        "text": response.text,
    }


def web_fetch_selenium(
    settings: Settings,
    url: str,
    wait_seconds: float | None = None,
    wait_selector: str | None = None,
    user_agent: str | None = None,
) -> Dict[str, Any]:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.edge.options import Options as EdgeOptions

    browser = settings.selenium_browser.lower()
    headless = settings.selenium_headless
    timeout = settings.selenium_page_load_timeout
    delay = settings.selenium_wait_seconds if wait_seconds is None else wait_seconds
    agent = user_agent or settings.selenium_user_agent or settings.user_agent

    if browser == "edge":
        options = EdgeOptions()
        if headless:
            options.add_argument("--headless=new")
        if agent:
            options.add_argument(f"--user-agent={agent}")
        driver = webdriver.Edge(options=options)
    else:
        options = ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        if agent:
            options.add_argument(f"--user-agent={agent}")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=options)

    try:
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        if wait_selector:
            WebDriverWait(driver, delay).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
            )
        elif delay and delay > 0:
            time.sleep(delay)
        html = driver.page_source
        return {
            "url": driver.current_url,
            "status_code": 200,
            "text": html,
            "rendered": True,
        }
    finally:
        driver.quit()


def web_fetch_browser(
    settings: Settings,
    url: str,
    headers: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    merged = _browser_headers()
    if headers:
        merged.update(headers)
    response = http_get(settings, url, headers=merged, cache_ttl=60)
    response.raise_for_status()
    return {
        "url": response.url,
        "status_code": response.status_code,
        "text": response.text,
    }


def web_extract(settings: Settings, html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())
    return {"text": text[:20000]}
