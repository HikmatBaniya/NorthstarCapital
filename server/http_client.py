from __future__ import annotations

import random
import threading
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

import requests

from .config import Settings

_cache_lock = threading.Lock()
_cache: Dict[Tuple[str, str, str], Tuple[float, Any]] = {}
_rate_lock = threading.Lock()
_last_request: Dict[str, float] = {}


def _cache_key(method: str, url: str, params: Optional[Dict[str, Any]]) -> Tuple[str, str, str]:
    params_str = ""
    if params:
        params_str = "&".join(f"{k}={params[k]}" for k in sorted(params))
    return method.upper(), url, params_str


def _rate_limit(host: str, min_interval: float) -> None:
    if min_interval <= 0:
        return
    with _rate_lock:
        last = _last_request.get(host, 0.0)
        now = time.time()
        wait = min_interval - (now - last)
        if wait > 0:
            time.sleep(wait)
        _last_request[host] = time.time()


def _request_with_retries(
    method: str,
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int,
    retries: int = 3,
    backoff_base: float = 0.4,
) -> requests.Response:
    if retries <= 0:
        return requests.request(
            method,
            url,
            params=params,
            data=data,
            headers=headers,
            timeout=timeout,
        )
    attempt = 0
    while True:
        response = requests.request(
            method,
            url,
            params=params,
            data=data,
            headers=headers,
            timeout=timeout,
        )
        if response.status_code not in (429, 500, 502, 503, 504):
            return response
        attempt += 1
        if attempt > retries:
            return response
        sleep_for = backoff_base * (2 ** (attempt - 1)) + random.uniform(0, 0.2)
        time.sleep(sleep_for)


def http_get(
    settings: Settings,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    cache_ttl: Optional[int] = None,
) -> requests.Response:
    ttl = settings.cache_ttl_seconds if cache_ttl is None else cache_ttl
    key = _cache_key("GET", url, params)
    if ttl > 0:
        with _cache_lock:
            cached = _cache.get(key)
            if cached and cached[0] > time.time():
                return cached[1]

    host = urlparse(url).netloc
    _rate_limit(host, settings.rate_limit_min_interval)
    response = _request_with_retries(
        "GET",
        url,
        params=params,
        headers=headers,
        timeout=settings.http_timeout_seconds,
        retries=settings.http_retry_count,
        backoff_base=settings.http_retry_backoff_seconds,
    )
    if ttl > 0:
        with _cache_lock:
            _cache[key] = (time.time() + ttl, response)
    return response


def http_post(
    settings: Settings,
    url: str,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    cache_ttl: Optional[int] = None,
) -> requests.Response:
    ttl = settings.cache_ttl_seconds if cache_ttl is None else cache_ttl
    key = _cache_key("POST", url, data)
    if ttl > 0:
        with _cache_lock:
            cached = _cache.get(key)
            if cached and cached[0] > time.time():
                return cached[1]

    host = urlparse(url).netloc
    _rate_limit(host, settings.rate_limit_min_interval)
    response = _request_with_retries(
        "POST",
        url,
        data=data,
        headers=headers,
        timeout=settings.http_timeout_seconds,
        retries=settings.http_retry_count,
        backoff_base=settings.http_retry_backoff_seconds,
    )
    if ttl > 0:
        with _cache_lock:
            _cache[key] = (time.time() + ttl, response)
    return response
