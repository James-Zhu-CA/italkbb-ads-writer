#!/usr/bin/env python3
"""Locked iTalkBB business page cache helper.

Usage examples:
  python3 scripts/business_info_cache.py --list
  python3 scripts/business_info_cache.py --backfill-locales
  python3 scripts/business_info_cache.py --business-id home_phone_plans --locale chs
  python3 scripts/business_info_cache.py --business-id monthly_promotion --locale chs --force-refresh
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen


LOCALES = ("chs", "cht", "en")
DEFAULT_TIMEOUT = 20
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")
    tmp_path.replace(path)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        f.write(content)
    tmp_path.replace(path)


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def url_locale(url: str) -> str | None:
    parts = [p for p in urlparse(url).path.split("/") if p]
    if len(parts) >= 1 and parts[0] in LOCALES:
        return parts[0]
    return None


def locale_slug(url: str) -> str:
    parts = [p for p in urlparse(url).path.split("/") if p]
    if len(parts) < 2:
        return ""
    slug = "/".join(parts[1:])
    if slug.endswith(".html"):
        slug = slug[:-5]
    return slug.lower()


def is_allowed_domain(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.netloc == "www.italkbb.ca"


def fetch_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh-TW;q=0.8",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            content_type = resp.headers.get("Content-Type", "")
            charset = "utf-8"
            m = re.search(r"charset=([\\w-]+)", content_type, flags=re.I)
            if m:
                charset = m.group(1)
            text = body.decode(charset, errors="replace")
            return {
                "ok": True,
                "status": getattr(resp, "status", 200),
                "url": resp.geturl(),
                "headers": dict(resp.headers.items()),
                "html": text,
                "error": None,
            }
    except HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return {
            "ok": False,
            "status": e.code,
            "url": url,
            "headers": dict(e.headers.items()) if e.headers else {},
            "html": body,
            "error": f"HTTPError {e.code}",
        }
    except URLError as e:
        return {
            "ok": False,
            "status": None,
            "url": url,
            "headers": {},
            "html": "",
            "error": f"URLError {e.reason}",
        }


def extract_title(html: str) -> str | None:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
    if not m:
        return None
    title = re.sub(r"\\s+", " ", m.group(1)).strip()
    return html_unescape(title)


def html_unescape(text: str) -> str:
    # Minimal unescape for common entities in metadata fields.
    return (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )


def html_to_text_excerpt(html: str, max_chars: int = 1200) -> str:
    text = re.sub(r"<script\\b[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<style\\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_unescape(text)
    text = re.sub(r"\\s+", " ", text).strip()
    return text[:max_chars]


def extract_urls_from_html(source_url: str, html: str) -> set[str]:
    candidates: set[str] = set()
    patterns = [
        r'href=["\\\']([^"\\\']+)["\\\']',
        r"https://www\\.italkbb\\.ca/(?:chs|cht|en)/[^\"'\\s<>]+",
    ]
    for pattern in patterns:
        for raw in re.findall(pattern, html, flags=re.I):
            if isinstance(raw, tuple):
                raw = raw[0]
            raw = raw.strip()
            if not raw:
                continue
            if raw.startswith(("mailto:", "tel:", "javascript:")):
                continue
            url = normalize_url(urljoin(source_url, raw))
            if is_allowed_domain(url):
                candidates.add(url)
    return candidates


def pick_locale_candidate(
    source_url: str, target_locale: str, candidates: set[str]
) -> str | None:
    expected_slug = locale_slug(source_url)
    locale_candidates = [u for u in candidates if url_locale(u) == target_locale]
    if not locale_candidates:
        return None

    def score(url: str) -> tuple[int, int]:
        slug = locale_slug(url)
        exact = 1 if slug == expected_slug else 0
        prefix = 1 if expected_slug and slug.startswith(expected_slug) else 0
        shorter = -len(url)
        return (exact * 10 + prefix, shorter)

    locale_candidates.sort(key=score, reverse=True)
    top = locale_candidates[0]
    top_slug = locale_slug(top)
    if expected_slug and expected_slug not in top_slug and top_slug not in expected_slug:
        return None
    return top


def derive_locale_fallbacks(source_chs_url: str, target_locale: str) -> list[str]:
    parsed = urlparse(source_chs_url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2 or parts[0] != "chs":
        return []
    rest = "/".join(parts[1:])
    base_path = f"/{target_locale}/{rest}"
    variants = [base_path]
    if target_locale == "en" and not base_path.endswith(".html"):
        variants.append(base_path + ".html")
    if target_locale != "en" and base_path.endswith(".html"):
        variants.append(base_path[:-5])
    out: list[str] = []
    for path in variants:
        out.append(normalize_url(urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))))
    # Preserve order, remove duplicates.
    dedup: list[str] = []
    for url in out:
        if url not in dedup:
            dedup.append(url)
    return dedup


def probe_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> bool:
    result = fetch_url(url, timeout=timeout)
    return bool(result["ok"] and result["status"] and 200 <= int(result["status"]) < 400)


def discover_locale_urls_from_chs(
    entry: dict[str, Any], timeout: int = DEFAULT_TIMEOUT
) -> tuple[dict[str, str | None], dict[str, Any] | None]:
    urls = entry.get("urls", {})
    chs_url = urls.get("chs")
    if not chs_url:
        return urls, None
    result = fetch_url(chs_url, timeout=timeout)
    if not result["ok"]:
        return urls, {"chs_fetch_error": result["error"], "status": result["status"]}
    candidates = extract_urls_from_html(chs_url, result["html"])
    updated = dict(urls)
    for locale in ("cht", "en"):
        if updated.get(locale):
            continue
        candidate = pick_locale_candidate(chs_url, locale, candidates)
        if not candidate:
            for fallback in derive_locale_fallbacks(chs_url, locale):
                if probe_url(fallback, timeout=timeout):
                    candidate = fallback
                    break
        if candidate:
            updated[locale] = candidate
    summary = {
        "source_url": chs_url,
        "status": result["status"],
        "title": extract_title(result["html"]),
        "discovered_urls": {k: updated.get(k) for k in LOCALES},
    }
    return updated, summary


def detect_project_root(start: Path) -> Path:
    for candidate in [start] + list(start.parents):
        if (candidate / ".git").exists() and (
            candidate / "skills/public/italkbb-ads-writer"
        ).exists():
            return candidate
    return start


def default_cache_root_from_cwd() -> Path:
    cwd = Path.cwd().resolve()
    project_root = detect_project_root(cwd)
    return project_root / "business_info"


def cache_paths(cache_root: Path, business_id: str, locale: str) -> dict[str, Path]:
    base = cache_root / business_id / locale
    return {
        "base": base,
        "meta": base / "meta.json",
        "raw": base / "raw.html",
        "snapshot": base / "snapshot.json",
    }


def load_registry(registry_path: Path) -> dict[str, Any]:
    data = read_json(registry_path)
    if not isinstance(data, dict) or "businesses" not in data:
        raise ValueError(f"Invalid registry file: {registry_path}")
    return data


def save_registry(registry_path: Path, data: dict[str, Any]) -> None:
    write_json(registry_path, data)


def registry_index(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["business_id"]: item for item in registry.get("businesses", [])}


def ensure_locale_url(
    registry_path: Path,
    registry: dict[str, Any],
    business_id: str,
    locale: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple[str, dict[str, Any] | None]:
    if locale not in LOCALES:
        raise ValueError(f"Unsupported locale: {locale}")
    index = registry_index(registry)
    if business_id not in index:
        raise KeyError(f"Unknown business_id: {business_id}")
    entry = index[business_id]
    urls = entry.get("urls", {})
    url = urls.get(locale)
    if url:
        return url, None
    updated_urls, summary = discover_locale_urls_from_chs(entry, timeout=timeout)
    if updated_urls != urls:
        entry["urls"] = updated_urls
        save_registry(registry_path, registry)
        url = updated_urls.get(locale)
    if not url:
        raise RuntimeError(
            f"Locale URL not found for business_id={business_id}, locale={locale}"
        )
    return url, summary


def read_meta_if_exists(meta_path: Path) -> dict[str, Any] | None:
    if not meta_path.exists():
        return None
    try:
        return read_json(meta_path)
    except Exception:
        return None


def cache_age_days(meta: dict[str, Any], now: datetime) -> float | None:
    fetched_at = meta.get("fetched_at")
    if not fetched_at:
        return None
    try:
        fetched_dt = parse_iso(fetched_at)
        return max(0.0, (now - fetched_dt).total_seconds() / 86400.0)
    except Exception:
        return None


def is_fresh(meta: dict[str, Any], ttl_days: int, now: datetime) -> bool:
    age = cache_age_days(meta, now)
    if age is None:
        return False
    return age <= ttl_days


def make_snapshot(source_url: str, html: str) -> dict[str, Any]:
    links = sorted(extract_urls_from_html(source_url, html))
    lang_links: dict[str, list[str]] = {locale: [] for locale in LOCALES}
    for link in links:
        locale = url_locale(link)
        if locale in lang_links:
            lang_links[locale].append(link)
    return {
        "source_url": source_url,
        "title": extract_title(html),
        "text_excerpt": html_to_text_excerpt(html),
        "language_links": lang_links,
    }


def cache_business_page(
    registry_path: Path,
    cache_root: Path,
    business_id: str,
    locale: str,
    ttl_days: int | None,
    timeout: int,
    force_refresh: bool,
) -> dict[str, Any]:
    registry = load_registry(registry_path)
    index = registry_index(registry)
    if business_id not in index:
        raise KeyError(f"Unknown business_id: {business_id}")
    entry = index[business_id]
    ttl = int(ttl_days if ttl_days is not None else entry.get("cache_ttl_days") or registry.get("default_ttl_days") or 7)
    source_url, discovery_summary = ensure_locale_url(
        registry_path=registry_path,
        registry=registry,
        business_id=business_id,
        locale=locale,
        timeout=timeout,
    )
    if not is_allowed_domain(source_url):
        raise RuntimeError(f"URL outside allowed domain: {source_url}")

    paths = cache_paths(cache_root, business_id, locale)
    now = utc_now()
    meta = read_meta_if_exists(paths["meta"])

    cache_status = "force_refresh" if force_refresh else "miss"
    if not force_refresh and meta and paths["raw"].exists() and paths["snapshot"].exists():
        if is_fresh(meta, ttl, now):
            cache_status = "hit"
            age = cache_age_days(meta, now)
            meta_out = dict(meta)
            meta_out["cache_status"] = "hit"
            if age is not None:
                meta_out["cache_age_days"] = round(age, 4)
            write_json(paths["meta"], meta_out)
            return {
                "business_id": business_id,
                "locale": locale,
                "source_url": source_url,
                "cache_status": cache_status,
                "ttl_days": ttl,
                "cache_age_days": round(age, 4) if age is not None else None,
                "meta_path": str(paths["meta"]),
                "raw_path": str(paths["raw"]),
                "snapshot_path": str(paths["snapshot"]),
                "discovery_summary": discovery_summary,
                "used_cache": True,
            }
        cache_status = "stale_refresh"

    result = fetch_url(source_url, timeout=timeout)
    if not result["ok"]:
        raise RuntimeError(
            f"Fetch failed for {source_url}: status={result['status']} error={result['error']}"
        )
    html = result["html"]
    fetched_at = iso_utc(now)
    snapshot = make_snapshot(source_url, html)

    write_text(paths["raw"], html)
    write_json(
        paths["snapshot"],
        {
            **snapshot,
            "business_id": business_id,
            "locale": locale,
            "fetched_at": fetched_at,
        },
    )
    expires_at = iso_utc(now + timedelta(days=ttl))
    meta_out = {
        "business_id": business_id,
        "locale": locale,
        "source_url": source_url,
        "fetched_at": fetched_at,
        "ttl_days": ttl,
        "expires_at": expires_at,
        "cache_age_days": 0.0,
        "cache_status": cache_status,
        "http_status": int(result["status"]),
        "content_sha256": sha256_text(html),
        "content_length_chars": len(html),
        "allowed_domain_check": "pass",
    }
    write_json(paths["meta"], meta_out)
    return {
        "business_id": business_id,
        "locale": locale,
        "source_url": source_url,
        "cache_status": cache_status,
        "ttl_days": ttl,
        "cache_age_days": 0.0,
        "meta_path": str(paths["meta"]),
        "raw_path": str(paths["raw"]),
        "snapshot_path": str(paths["snapshot"]),
        "discovery_summary": discovery_summary,
        "used_cache": False,
    }


def backfill_locales(
    registry_path: Path, timeout: int, business_id: str | None = None
) -> dict[str, Any]:
    registry = load_registry(registry_path)
    changed = False
    results: list[dict[str, Any]] = []
    for entry in registry.get("businesses", []):
        if business_id and entry.get("business_id") != business_id:
            continue
        before = dict(entry.get("urls", {}))
        updated_urls, summary = discover_locale_urls_from_chs(entry, timeout=timeout)
        if updated_urls != before:
            entry["urls"] = updated_urls
            changed = True
        results.append(
            {
                "business_id": entry.get("business_id"),
                "before": before,
                "after": dict(entry.get("urls", {})),
                "summary": summary,
            }
        )
    if changed:
        save_registry(registry_path, registry)
    return {
        "registry_path": str(registry_path),
        "changed": changed,
        "results": results,
    }


def list_businesses(registry_path: Path) -> dict[str, Any]:
    registry = load_registry(registry_path)
    return {
        "registry_path": str(registry_path),
        "default_ttl_days": registry.get("default_ttl_days", 7),
        "businesses": [
            {
                "business_id": b.get("business_id"),
                "category": b.get("category"),
                "cache_ttl_days": b.get("cache_ttl_days"),
                "urls": b.get("urls", {}),
            }
            for b in registry.get("businesses", [])
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Locked business page cache helper")
    parser.add_argument("--registry", type=Path, default=None, help="Path to business URL registry JSON")
    parser.add_argument("--cache-root", type=Path, default=None, help="Project cache root (default: <project>/business_info)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="HTTP timeout seconds")
    parser.add_argument("--list", action="store_true", help="List registry businesses")
    parser.add_argument("--backfill-locales", action="store_true", help="Backfill cht/en URLs from locked chs pages and persist registry")
    parser.add_argument("--business-id", help="Business id from registry")
    parser.add_argument("--locale", choices=LOCALES, help="Locale to fetch/cache")
    parser.add_argument("--ttl-days", type=int, default=None, help="Override cache TTL days")
    parser.add_argument("--force-refresh", action="store_true", help="Ignore fresh cache and fetch website again")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    registry_path = (
        args.registry.resolve()
        if args.registry
        else (script_dir.parent / "references" / "business-url-registry.json").resolve()
    )
    cache_root = (
        args.cache_root.resolve() if args.cache_root else default_cache_root_from_cwd().resolve()
    )

    try:
        if args.list:
            print(json.dumps(list_businesses(registry_path), ensure_ascii=False, indent=2))
            return 0

        if args.backfill_locales:
            print(
                json.dumps(
                    backfill_locales(registry_path, timeout=args.timeout, business_id=args.business_id),
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        if not args.business_id or not args.locale:
            raise ValueError("--business-id and --locale are required unless --list/--backfill-locales is used")

        result = cache_business_page(
            registry_path=registry_path,
            cache_root=cache_root,
            business_id=args.business_id,
            locale=args.locale,
            ttl_days=args.ttl_days,
            timeout=args.timeout,
            force_refresh=args.force_refresh,
        )
        print(json.dumps({**result, "cache_root": str(cache_root)}, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        err = {
            "ok": False,
            "error": str(e),
            "registry_path": str(registry_path),
            "cache_root": str(cache_root),
        }
        print(json.dumps(err, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
