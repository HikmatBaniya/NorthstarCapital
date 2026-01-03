from __future__ import annotations

from typing import Any, Dict, List, Optional

from .config import Settings
from .http_client import http_get, http_post
from .tools.news_tools import news_search
from .tools.sec_tools import sec_company_facts


WIKIDATA_API = "https://www.wikidata.org/w/api.php"


def enrich_company_data(settings: Settings, name: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "company": {},
        "profile": {},
        "identifiers": [],
        "people": [],
        "images": [],
        "documents": [],
        "coverage": [],
    }
    entity = _wikidata_company_entity(settings, name)
    if entity:
        data.update(_extract_company_from_entity(settings, entity))
    data["documents"] = _fetch_company_news(settings, name)
    data["documents"].extend(_fetch_company_news_gdelt(settings, name))
    if settings.openfigi_api_key:
        data.update(_openfigi_enrich(settings, name, data))
    return data


def _wikidata_company_entity(settings: Settings, name: str) -> Optional[Dict[str, Any]]:
    response = http_get(
        settings,
        WIKIDATA_API,
        params={
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "format": "json",
            "limit": 1,
        },
        headers={"User-Agent": settings.user_agent},
        cache_ttl=3600,
    )
    response.raise_for_status()
    results = response.json().get("search", [])
    if not results:
        return None
    entity_id = results[0].get("id")
    if not entity_id:
        return None
    return _wikidata_entity(settings, entity_id)


def _wikidata_entity(settings: Settings, entity_id: str) -> Optional[Dict[str, Any]]:
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"
    response = http_get(settings, url, headers={"User-Agent": settings.user_agent}, cache_ttl=3600)
    response.raise_for_status()
    payload = response.json()
    return payload.get("entities", {}).get(entity_id)


def _wikidata_labels(settings: Settings, ids: List[str]) -> Dict[str, str]:
    if not ids:
        return {}
    response = http_get(
        settings,
        WIKIDATA_API,
        params={
            "action": "wbgetentities",
            "ids": "|".join(ids),
            "props": "labels",
            "languages": "en",
            "format": "json",
        },
        headers={"User-Agent": settings.user_agent},
        cache_ttl=3600,
    )
    response.raise_for_status()
    entities = response.json().get("entities", {})
    labels: Dict[str, str] = {}
    for entity_id, entity in entities.items():
        label = entity.get("labels", {}).get("en", {}).get("value")
        if label:
            labels[entity_id] = label
    return labels


def _extract_company_from_entity(settings: Settings, entity: Dict[str, Any]) -> Dict[str, Any]:
    claims = entity.get("claims", {})
    descriptions = entity.get("descriptions", {})
    description = descriptions.get("en", {}).get("value")
    label = entity.get("labels", {}).get("en", {}).get("value")
    aliases = [a.get("value") for a in entity.get("aliases", {}).get("en", []) if a.get("value")]

    wikidata_id = entity.get("id")
    wikidata_url = f"https://www.wikidata.org/wiki/{wikidata_id}" if wikidata_id else None
    wikipedia_url = None
    sitelinks = entity.get("sitelinks", {})
    if "enwiki" in sitelinks:
        title = sitelinks["enwiki"].get("title")
        if title:
            wikipedia_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"

    website = _get_first_claim_value(claims, "P856")
    ticker = _get_first_claim_value(claims, "P249")
    isin = _get_first_claim_value(claims, "P946")
    lei = _get_first_claim_value(claims, "P1278")
    country_id = _get_first_entity_id(claims, "P17")
    industry_id = _get_first_entity_id(claims, "P452")
    sector_id = _get_first_entity_id(claims, "P361")
    headquarters_id = _get_first_entity_id(claims, "P159")
    inception = _get_first_time_value(claims, "P571")
    image_name = _get_first_claim_value(claims, "P18")
    subsidiary_ids = _get_entity_ids(claims, "P355")
    owner_ids = _get_entity_ids(claims, "P127")
    parent_ids = _get_entity_ids(claims, "P749")

    label_map = _wikidata_labels(
        settings,
        [
            cid
            for cid in [
                country_id,
                industry_id,
                sector_id,
                headquarters_id,
                *subsidiary_ids,
                *owner_ids,
                *parent_ids,
            ]
            if cid
        ],
    )

    people = _extract_people(settings, claims)
    people_images = [p.pop("image") for p in people if p.get("image")]
    people_images = [img for img in people_images if img]

    images = []
    if image_name:
        images.append(
            {
                "entity_type": "company",
                "image_url": _commons_image_url(image_name),
                "license": "Wikimedia Commons",
                "attribution": "Wikidata",
                "source": wikidata_url,
            }
        )

    profile: Dict[str, Any] = {
        "wikidata_id": wikidata_id,
        "wikidata_url": wikidata_url,
        "wikipedia_url": wikipedia_url,
        "description": description,
        "aliases": aliases,
        "headquarters": label_map.get(headquarters_id),
        "inception": inception,
        "official_website": website,
        "industry": label_map.get(industry_id),
        "sector": label_map.get(sector_id),
        "country": label_map.get(country_id),
        "ticker": ticker,
        "isin": isin,
        "lei": lei,
    }

    company_fields = {
        "name": label,
        "description": description,
        "sector": label_map.get(sector_id),
        "industry": label_map.get(industry_id),
        "country": label_map.get(country_id),
        "website": website,
    }

    identifiers = []
    if wikidata_id:
        identifiers.append({"id_type": "wikidata", "id_value": wikidata_id, "source": wikidata_url})
    if ticker:
        identifiers.append({"id_type": "ticker", "id_value": ticker, "source": wikidata_url})
    if isin:
        identifiers.append({"id_type": "isin", "id_value": isin, "source": wikidata_url})
    if lei:
        identifiers.append({"id_type": "lei", "id_value": lei, "source": wikidata_url})

    subsidiaries = [
        {
            "name": label_map.get(sub_id),
            "source": wikidata_url,
        }
        for sub_id in subsidiary_ids
        if label_map.get(sub_id)
    ]

    ownership = []
    for owner_id in owner_ids:
        owner_name = label_map.get(owner_id)
        if owner_name:
            ownership.append(
                {
                    "holder_name": owner_name,
                    "holder_type": "owner",
                    "source": f"https://www.wikidata.org/wiki/{owner_id}",
                }
            )
    for parent_id in parent_ids:
        parent_name = label_map.get(parent_id)
        if parent_name:
            ownership.append(
                {
                    "holder_name": parent_name,
                    "holder_type": "parent",
                    "source": f"https://www.wikidata.org/wiki/{parent_id}",
                }
            )

    if wikipedia_url:
        summary = _wikipedia_summary(settings, wikipedia_url)
        if summary.get("extract"):
            profile["summary"] = summary.get("extract")
        if summary.get("thumbnail"):
            images.append(
                {
                    "entity_type": "company",
                    "image_url": summary.get("thumbnail"),
                    "license": "Wikipedia",
                    "attribution": "Wikipedia",
                    "source": wikipedia_url,
                }
            )

    coverage = ["wikidata"]
    if wikipedia_url:
        coverage.append("wikipedia")

    return {
        "company": company_fields,
        "profile": profile,
        "identifiers": identifiers,
        "people": people,
        "images": images,
        "ownership": ownership,
        "subsidiaries": subsidiaries,
        "people_images": people_images,
        "coverage": coverage,
    }


def _extract_people(settings: Settings, claims: Dict[str, Any]) -> List[Dict[str, Any]]:
    people: List[Dict[str, Any]] = []
    ceo_ids = _get_entity_ids(claims, "P169")
    board_ids = _get_entity_ids(claims, "P3320")
    role_map: Dict[str, str] = {}
    for person_id in ceo_ids:
        role_map[person_id] = "Chief Executive Officer"
    for person_id in board_ids:
        role_map.setdefault(person_id, "Board Member")

    labels = _wikidata_labels(settings, list(role_map.keys()))
    for person_id, role in role_map.items():
        name = labels.get(person_id)
        if not name:
            continue
        person_entity = _wikidata_entity(settings, person_id)
        image_name = None
        if person_entity:
            image_name = _get_first_claim_value(person_entity.get("claims", {}), "P18")
        people.append(
            {
                "name": name,
                "role": role,
                "source": f"https://www.wikidata.org/wiki/{person_id}",
                "image": _commons_image_url(image_name) if image_name else None,
            }
        )
    return people


def _fetch_company_news(settings: Settings, name: str) -> List[Dict[str, Any]]:
    results = news_search(settings, f"{name} company news", max_results=6)
    documents = []
    for item in results:
        documents.append(
            {
                "doc_type": "news",
                "title": item.get("title"),
                "url": item.get("href"),
                "content": item.get("body"),
                "source": "duckduckgo",
            }
        )
    return documents


def _fetch_company_news_gdelt(settings: Settings, name: str) -> List[Dict[str, Any]]:
    try:
        response = http_get(
            settings,
            "https://api.gdeltproject.org/api/v2/doc/doc",
            params={
                "query": f"{name} company",
                "mode": "ArtList",
                "maxrecords": str(settings.gdelt_max_records),
                "format": "json",
                "sort": "HybridRel",
            },
            headers={"User-Agent": settings.user_agent},
            cache_ttl=600,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []

    documents = []
    for item in payload.get("articles", []):
        documents.append(
            {
                "doc_type": "news",
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get("seendate"),
                "source": "gdelt",
                "published_at": item.get("seendate"),
            }
        )
    return documents


def _wikipedia_summary(settings: Settings, wikipedia_url: str) -> Dict[str, Any]:
    title = wikipedia_url.rsplit("/", 1)[-1]
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
    response = http_get(settings, summary_url, headers={"User-Agent": settings.user_agent}, cache_ttl=3600)
    response.raise_for_status()
    payload = response.json()
    return {
        "extract": payload.get("extract"),
        "thumbnail": payload.get("thumbnail", {}).get("source"),
    }


def extract_financials_from_sec(settings: Settings, ticker: str) -> List[Dict[str, Any]]:
    try:
        payload = sec_company_facts(settings, ticker)
    except Exception:
        return []
    facts = payload.get("facts", {}).get("us-gaap", {})
    if not facts:
        return []

    metric_map = {
        "Assets": "assets",
        "Liabilities": "liabilities",
        "Revenues": "revenue",
        "NetIncomeLoss": "net_income",
        "OperatingIncomeLoss": "operating_income",
        "EarningsPerShareBasic": "eps_basic",
        "EarningsPerShareDiluted": "eps_diluted",
    }

    rows: List[Dict[str, Any]] = []
    for tag, metric_name in metric_map.items():
        entry = facts.get(tag, {})
        units = entry.get("units", {})
        for unit, items in units.items():
            for item in items:
                value = item.get("val")
                if value is None:
                    continue
                rows.append(
                    {
                        "metric": metric_name,
                        "value": value,
                        "period_start": item.get("start"),
                        "period_end": item.get("end") or item.get("date"),
                        "unit": unit,
                        "source": "sec",
                    }
                )
    return rows


def _openfigi_enrich(settings: Settings, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    headers = {
        "User-Agent": settings.user_agent,
        "Content-Type": "application/json",
        "X-OPENFIGI-APIKEY": settings.openfigi_api_key,
    }
    payload = [{"name": name}]
    import json as _json

    response = http_post(
        settings,
        "https://api.openfigi.com/v3/mapping",
        data=_json.dumps(payload),
        headers=headers,
        cache_ttl=3600,
    )
    try:
        response.raise_for_status()
    except Exception:
        return data
    try:
        results = response.json()
    except Exception:
        return data

    if not isinstance(results, list) or not results:
        return data
    match = results[0].get("data", [])
    if not match:
        return data

    row = match[0]
    figi = row.get("figi")
    composite_figi = row.get("compositeFIGI")
    share_figi = row.get("shareClassFIGI")
    ticker = row.get("ticker")
    exch = row.get("exchCode")
    market_sector = row.get("marketSector")
    name = row.get("name")

    identifiers = data.get("identifiers", [])
    if figi:
        identifiers.append({"id_type": "figi", "id_value": figi, "source": "openfigi"})
    if composite_figi:
        identifiers.append({"id_type": "composite_figi", "id_value": composite_figi, "source": "openfigi"})
    if share_figi:
        identifiers.append({"id_type": "share_class_figi", "id_value": share_figi, "source": "openfigi"})
    if ticker:
        identifiers.append({"id_type": "ticker", "id_value": ticker, "source": "openfigi"})
    data["identifiers"] = identifiers

    profile = data.get("profile", {})
    if exch:
        profile["exchange"] = exch
    if market_sector:
        profile["market_sector"] = market_sector
    if name:
        profile["openfigi_name"] = name
    data["profile"] = profile

    coverage = data.get("coverage", [])
    if "openfigi" not in coverage:
        coverage.append("openfigi")
    data["coverage"] = coverage
    return data


def _get_first_claim_value(claims: Dict[str, Any], pid: str) -> Optional[str]:
    values = _get_claim_values(claims, pid)
    return values[0] if values else None


def _get_first_entity_id(claims: Dict[str, Any], pid: str) -> Optional[str]:
    ids = _get_entity_ids(claims, pid)
    return ids[0] if ids else None


def _get_first_time_value(claims: Dict[str, Any], pid: str) -> Optional[str]:
    values = _get_claim_values(claims, pid, value_type="time")
    return values[0] if values else None


def _get_entity_ids(claims: Dict[str, Any], pid: str) -> List[str]:
    values = _get_claim_values(claims, pid, value_type="wikibase-entityid")
    return [value for value in values if value]


def _get_claim_values(
    claims: Dict[str, Any],
    pid: str,
    value_type: Optional[str] = None,
) -> List[str]:
    items = claims.get(pid, [])
    results: List[str] = []
    for item in items:
        mainsnak = item.get("mainsnak", {})
        datavalue = mainsnak.get("datavalue", {})
        if not datavalue:
            continue
        if value_type and datavalue.get("type") != value_type:
            continue
        value = datavalue.get("value")
        if isinstance(value, dict):
            if value_type == "wikibase-entityid":
                entity_id = value.get("id")
                if entity_id:
                    results.append(entity_id)
            elif value_type == "time":
                time_value = value.get("time")
                if time_value:
                    results.append(time_value)
        elif isinstance(value, str):
            results.append(value)
    return results


def _commons_image_url(filename: Optional[str]) -> Optional[str]:
    if not filename:
        return None
    cleaned = filename.replace(" ", "_")
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{cleaned}"
