"""Download public official guidance, respecting robots.txt and bounded concurrency.

Run: python src/app/crawl_knowledge.py --vus --chileatiende-limit 180
Requires requirements-knowledge.txt. Never visits citizen/authenticated pages.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import threading
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup
from ruta.knowledge import split_text

ROOT = Path(__file__).resolve().parent / "knowledge"
AGENT = "ChileAtiendeDemoKnowledge/1.0 (public guidance; bounded research crawl)"
VUS = "https://www.ventanillaunicasocial.gob.cl"
CA = "https://www.chileatiende.gob.cl"
SEEDS = [
    CA + "/momentos-de-vida",
    CA + "/temas",
    CA + "/ayuda",
    CA + "/ayuda/sucursales",
    CA + "/ayuda/atencion-telefonica",
    CA + "/fichas/102077-pension-garantizada-universal-pgu",
    CA + "/fichas/62932-seguro-de-cesantia",
    CA + "/fichas/9380-certificado-de-nacimiento",
    CA + "/fichas/54985-solicitud-de-ingreso-al-registro-social-de-hogares-rsh",
    CA + "/fichas/11331-obtener-la-claveunica",
    CA + "/fichas/3430",
    CA + "/fichas/3442",
    CA + "/fichas/3445",
    CA + "/fichas/29888",
    CA
    + "/fichas/19094-ds1-tramo-1-subsidio-habitacional-para-comprar-una-vivienda-de-hasta-1100-uf",
    "https://www.registrosocial.gob.cl/preguntas-frecuentes-web",
    "https://claveunica.gob.cl/",
    "https://portal.beneficiosestudiantiles.cl/",
    "https://www.afc.cl/afiliados/",
    "https://www.fonasa.cl/sites/fonasa/beneficiarios",
    "https://www.minvu.gob.cl/beneficios/",
    "https://www.sence.cl/",
]
ALLOWED_HOSTS = {
    "www.ventanillaunicasocial.gob.cl",
    "www.chileatiende.gob.cl",
    "www.registrosocial.gob.cl",
    "claveunica.gob.cl",
    "portal.beneficiosestudiantiles.cl",
    "www.afc.cl",
    "www.fonasa.cl",
    "www.minvu.gob.cl",
    "www.sence.cl",
    "sence.gob.cl",
}
BLOCKED_PATHS = re.compile(r"/(ciudadano|cu/|login|autenticar|oauth|api/|buscar|wp-admin)", re.I)


def replace_snapshot(temporary: Path, destination: Path):
    # Windows may briefly hold a file open while Streamlit rebuilds its index.
    for attempt in range(12):
        try:
            temporary.replace(destination)
            return
        except PermissionError:
            if attempt == 11:
                raise
            time.sleep(0.25 * (attempt + 1))


def deduplicate_documents(documents):
    """A service's numeric identifier is stable even when its title slug changes."""
    unique = {}
    for doc in documents:
        identity = re.sub(
            r"((?:/fichas/|/ficha/|/todos-los-beneficios/)\d+)(?:[-/].*)?$", r"\1", doc["url"]
        )
        if identity not in unique:
            unique[identity] = dict(doc)
            unique[identity]["alternate_urls"] = list(doc.get("alternate_urls", []))
        else:
            kept = unique[identity]
            kept["alternate_urls"] = sorted(
                set(kept["alternate_urls"] + [doc["url"]] + doc.get("alternate_urls", []))
                - {kept["url"]}
            )
    return list(unique.values())


def normalize_url(url: str) -> str | None:
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or parts.hostname not in ALLOWED_HOSTS:
        return None
    if parts.username or parts.password or BLOCKED_PATHS.search(parts.path):
        return None
    if re.search(r"\.(pdf|jpg|png|svg|zip|docx?|xlsx?)$", parts.path, re.I):
        return None
    # Search/pagination and login queries are not crawled.
    path = re.sub(r"(/fichas/\d+)/\d+/pdf$", r"\1", parts.path.rstrip("/"))
    return urlunsplit(("https", parts.netloc, quote(path, safe="/%:@!$&'()*+,;=-._~"), "", ""))


class Downloader:
    def __init__(self, delay: float = 0.5):
        self.delay = delay
        self.robots: dict[str, RobotFileParser] = {}
        self.locks: dict[str, threading.Lock] = {}
        self.last: dict[str, float] = {}
        self.guard = threading.Lock()

    def prepare(self, hosts):
        for host in sorted(hosts):
            robot = RobotFileParser()
            try:
                request = Request(f"https://{host}/robots.txt", headers={"User-Agent": AGENT})
                with urlopen(request, timeout=20) as response:
                    robot.parse(response.read(500_000).decode("utf-8", "replace").splitlines())
            except HTTPError as error:
                robot.parse(
                    ["User-agent: *", "Allow: /"]
                    if error.code == 404
                    else ["User-agent: *", "Disallow: /"]
                )
            except Exception:
                # Do not crawl a host whose policy could not be checked.
                robot.parse(["User-agent: *", "Disallow: /"])
            self.robots[host] = robot
            self.locks[host] = threading.Lock()

    def get(self, url: str) -> tuple[str, str]:
        host = urlsplit(url).hostname
        robot = self.robots[host]
        if not robot.can_fetch(AGENT, url):
            raise ValueError("robots_disallowed")
        with self.locks[host]:
            interval = max(self.delay, robot.crawl_delay(AGENT) or 0)
            time.sleep(max(0, interval - (time.monotonic() - self.last.get(host, 0))))
            self.last[host] = time.monotonic()
        for attempt in range(3):
            try:
                request = Request(
                    url, headers={"User-Agent": AGENT, "Accept": "text/html,application/xml"}
                )
                with build_opener(PublicRedirect(self.robots)).open(
                    request, timeout=35
                ) as response:
                    final = normalize_url(response.url)
                    if final is None or not self.robots[urlsplit(final).hostname].can_fetch(
                        AGENT, final
                    ):
                        raise ValueError("redirect_outside_public_scope")
                    content_type = response.headers.get("Content-Type", "")
                    if not any(kind in content_type for kind in ("html", "xml", "text/plain")):
                        raise ValueError("unsupported_content_type")
                    raw = response.read(5_000_001)
                    if len(raw) > 5_000_000:
                        raise ValueError("page_too_large")
                    return raw.decode(
                        response.headers.get_content_charset() or "utf-8", "replace"
                    ), final
            except HTTPError as error:
                if error.code not in {429, 500, 502, 503, 504} or attempt == 2:
                    raise
                time.sleep(min(20, int(error.headers.get("Retry-After", "3")) + attempt * 3))
        raise RuntimeError("download_failed")


class PublicRedirect(HTTPRedirectHandler):
    """Reject login, unknown hosts and disallowed routes before following redirects."""

    def __init__(self, robots):
        super().__init__()
        self.robots = robots

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        target = normalize_url(newurl)
        if target is None or not self.robots[urlsplit(target).hostname].can_fetch(AGENT, target):
            raise ValueError("redirect_outside_public_scope")
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def extract_document(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text(" ", strip=True)
    main = soup.find("main") or soup.find("article") or soup.body
    if main is None:
        raise ValueError("missing_content")
    first_heading = main.find(["h1", "h2"])
    page_title = first_heading.get_text(" ", strip=True) if first_heading else None
    if "/fichas/" in url and "chileatiende.gob.cl" in url:
        main = soup.select_one("#page-content") or main
    elif "/ficha/" in url and "/centro-de-ayuda/" not in url:
        main = soup.select_one("#contenido-ficha") or main
    for element in main.select(
        "script,style,svg,nav,footer,header,noscript,input,textarea,[role=dialog],.modal,.material-icons,.material-icons-outlined"
    ):
        element.decompose()
    for element in list(main.find_all(True)):
        if element.attrs is not None and any(str(key).startswith("wire:") for key in element.attrs):
            # Livewire state is not needed; retain its rendered public content.
            for key in list(element.attrs):
                if key.startswith("wire:"):
                    del element.attrs[key]
    first_heading = main.find(["h1", "h2"])
    title = page_title or (
        first_heading.get_text(" ", strip=True)
        if first_heading
        else (soup.title.get_text(" ", strip=True) if soup.title else url)
    )
    if title in {"Menú", "Ventanilla Única Social"}:
        heading = main.find("h2")
        if heading:
            title = heading.get_text(" ", strip=True)
    links = []
    for anchor in main.select("a[href]"):
        target = urljoin(url, anchor["href"])
        parts = urlsplit(target)
        if (
            parts.scheme == "https"
            and parts.hostname
            and not any(
                s in parts.hostname for s in ("facebook", "twitter", "instagram", "youtube")
            )
        ):
            label = anchor.get_text(" ", strip=True)
            if (
                label
                and len(target) < 1000
                and not parts.query
                and not BLOCKED_PATHS.search(parts.path)
            ):
                links.append({"label": label[:200], "url": target})
                anchor.replace_with(f"{label} ({target})")
    # VUS uses h5/h6 for entire FAQ answers, not just headings.
    for heading in main.find_all(re.compile(r"^h[1-4]$")):
        text = heading.get_text(" ", strip=True)
        if text:
            heading.replace_with(f"\n@@SECTION:{text}\n")
    sections = []
    current = "Resumen"
    lines = []
    seen = set()

    def flush():
        text = " ".join(lines).strip()
        if len(text) >= 35:
            sections.append({"heading": current, "text": text})

    for line in main.get_text("\n", strip=True).splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if line.startswith("@@SECTION:"):
            flush()
            current, lines, seen = line.removeprefix("@@SECTION:"), [], set()
        elif (
            line
            and line not in seen
            and line
            not in {
                "Mostrar más",
                "Mostrar menos",
                "Conocer más",
                "Volver",
                "Compartir",
                "add",
                "remove",
                "arrow_back",
                "business",
                "history",
            }
        ):
            seen.add(line)
            lines.append(line)
    flush()
    total = " ".join(section["text"] for section in sections)
    if len(total) < 120:
        raise ValueError("insufficient_public_text")
    if any(word in title.lower() for word in ("access denied", "just a moment", "error 404")):
        raise ValueError("error_page")
    date = re.search(
        r"[ÚUuú]ltima actualizaci[oó]n\s*:?\s*(\d{1,2}/\d{1,2}/\d{4}|"
        r"\d{1,2}(?:\s+de)?\s+[a-záéíóú]+,?(?:\s+de)?\s+\d{4})",
        page_text,
        re.I,
    )
    source = (
        "Ventanilla Única Social"
        if "ventanillaunicasocial" in url
        else ("ChileAtiende" if "chileatiende.gob.cl" in url else urlsplit(url).hostname)
    )
    return {
        "extractor_version": 2,
        "id": hashlib.sha256(url.encode()).hexdigest()[:16],
        "url": url,
        "title": title,
        "source": source,
        "fetched_at": datetime.now(UTC).isoformat(),
        "source_updated_text": date.group(1).strip() if date else None,
        "sha256": hashlib.sha256(total.encode()).hexdigest(),
        "sections": sections,
        "links": list({link["url"]: link for link in links}.values()),
    }


def run(args):
    ROOT.mkdir(exist_ok=True)
    if args.reparse:
        existing = ROOT / "documents.jsonl"
        old = (
            {
                doc["url"]: doc
                for doc in map(json.loads, existing.read_text(encoding="utf-8").splitlines())
            }
            if existing.exists()
            else {}
        )
        rebuilt, failures = {}, []
        for cache in sorted((ROOT / ".cache").glob("*.json.gz")):
            cached = json.loads(gzip.decompress(cache.read_bytes()))
            try:
                doc = extract_document(cached["html"], cached["url"])
                doc["fetched_at"] = (
                    old.get(doc["url"], {}).get("fetched_at")
                    or datetime.fromtimestamp(cache.stat().st_mtime, UTC).isoformat()
                )
                rebuilt[doc["url"]] = doc
            except ValueError as error:
                failures.append({"url": cached["url"], "error": str(error)})
        if not rebuilt:
            raise ValueError("No cached documents to reparse")
        # Keep documents not present in cache; avoid deleting a previous source.
        old.update(rebuilt)
        old = {doc["url"]: doc for doc in deduplicate_documents(old.values())}
        temporary = ROOT / "documents.jsonl.tmp"
        temporary.write_text(
            "".join(json.dumps(doc, ensure_ascii=False) + "\n" for _, doc in sorted(old.items())),
            encoding="utf-8",
        )
        replace_snapshot(temporary, existing)
        print(json.dumps({"reparsed": len(rebuilt), "errors": failures}), flush=True)
        return
    downloader = Downloader(args.delay)
    downloader.prepare(ALLOWED_HOSTS)
    urls = set()
    sitemap_urls = set()
    if args.vus:
        xml, _ = downloader.get(VUS + "/sitemap.xml")
        root = ET.fromstring(xml)
        urls.update(
            normalized
            for node in root.iter()
            if node.tag.endswith("}loc")
            if (normalized := normalize_url(node.text or ""))
            and "/terminos-y-condiciones" not in normalized
        )
        sitemap_urls = set(urls)
    urls.update(filter(None, (normalize_url(url) for url in SEEDS)))
    documents, errors = {}, []
    resolved_urls = set()
    existing = ROOT / "documents.jsonl"
    if existing.exists() and not args.refresh:
        documents = {
            doc["url"]: doc
            for doc in map(json.loads, existing.read_text(encoding="utf-8").splitlines())
        }
    discovered = set()
    requested = set()

    def crawl(batch):
        def fetch(url):
            if url in documents:
                return documents[url]
            cache = ROOT / ".cache" / (hashlib.sha256(url.encode()).hexdigest() + ".json.gz")
            if cache.exists() and not args.refresh:
                cached = json.loads(gzip.decompress(cache.read_bytes()))
                html, final = cached["html"], cached["url"]
            else:
                html, final = downloader.get(url)
                cache.parent.mkdir(exist_ok=True)
                cache.write_bytes(gzip.compress(json.dumps({"html": html, "url": final}).encode()))
            return extract_document(html, final)

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(fetch, url): url for url in sorted(batch)}
            for count, future in enumerate(as_completed(futures), 1):
                url = futures[future]
                requested.add(url)
                try:
                    doc = future.result()
                    documents[doc["url"]] = doc
                    resolved_urls.add(url)
                    for link in doc["links"]:
                        target = normalize_url(link["url"])
                        if (
                            target
                            and urlsplit(target).hostname == "www.chileatiende.gob.cl"
                            and re.match(
                                r"/(fichas/\d+|momentos-de-vida/|temas/)", urlsplit(target).path
                            )
                        ):
                            discovered.add(target)
                        if (
                            target
                            and urlsplit(target).hostname == "www.ventanillaunicasocial.gob.cl"
                            and re.match(
                                r"/(ficha/|micro-ficha/|todos-los-beneficios/|centro-de-ayuda/)",
                                urlsplit(target).path,
                            )
                        ):
                            discovered.add(target)
                except Exception as error:
                    errors.append({"url": url, "error": str(error)[:250]})
                if count % 25 == 0 or count == len(futures):
                    print(
                        f"Crawl {count}/{len(futures)}: "
                        f"{len(documents)} documents, {len(errors)} errors",
                        flush=True,
                    )
                    save()

    def save():
        snapshot = deduplicate_documents(documents.values())
        temporary = ROOT / "documents.jsonl.tmp"
        temporary.write_text(
            "".join(
                json.dumps(doc, ensure_ascii=False) + "\n"
                for doc in sorted(snapshot, key=lambda item: item["url"])
            ),
            encoding="utf-8",
        )
        replace_snapshot(temporary, existing)
        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "documents": len(snapshot),
            "requested": len(requested),
            "passages": sum(
                len(split_text(section["text"])) for doc in snapshot for section in doc["sections"]
            ),
            "sources": {
                source: sum(doc["source"] == source for doc in snapshot)
                for source in sorted({doc["source"] for doc in snapshot})
            },
            "vus_sitemap_urls": len(sitemap_urls),
            "vus_discovered_urls": sum("ventanillaunicasocial" in url for url in urls),
            "missing_urls": sorted(
                url for url in urls if url not in documents and url not in resolved_urls
            ),
            "coverage": {
                "vus_primary_records": sum(
                    "ventanillaunicasocial" in doc["url"]
                    and "/ficha/" in doc["url"]
                    and "/centro-de-ayuda/" not in doc["url"]
                    for doc in snapshot
                ),
                "vus_categories": sum(
                    "ventanillaunicasocial" in doc["url"] and "/todos-los-beneficios/" in doc["url"]
                    for doc in snapshot
                ),
                "vus_help_pages": sum(
                    "ventanillaunicasocial" in doc["url"] and "/centro-de-ayuda" in doc["url"]
                    for doc in snapshot
                ),
                "vus_missing_urls": sorted(
                    url
                    for url in urls
                    if "ventanillaunicasocial" in url
                    and url not in documents
                    and url not in resolved_urls
                ),
            },
            "errors": errors,
            "notice": (
                "Public snapshot, not eligibility rules or confirmation of an open "
                "application period. Missing and blocked sources are listed explicitly."
            ),
        }
        (ROOT / "manifest.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    crawl(urls)
    vus_extras = {url for url in discovered - requested if "ventanillaunicasocial.gob.cl" in url}
    urls.update(vus_extras)
    crawl(sorted(vus_extras)[: args.vus_extra_limit])
    # Discover life-event routes first, then their linked procedures.
    life_events = {url for url in discovered - requested if "/momentos-de-vida/" in url}
    crawl(sorted(life_events)[:50])
    topics = {url for url in discovered - requested if "/temas/" in url}
    crawl(sorted(topics)[:25])
    extras = sorted(
        (url for url in discovered - requested if "chileatiende.gob.cl" in url),
        key=lambda url: ("/fichas/" not in url, url),
    )[: args.chileatiende_limit]
    crawl(extras)
    save()
    print(
        json.dumps({"documents": len(documents), "errors": len(errors)}, ensure_ascii=False),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vus", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument(
        "--reparse",
        action="store_true",
        help="Re-extract cached HTML offline, preserving download dates",
    )
    parser.add_argument("--chileatiende-limit", type=int, default=180)
    parser.add_argument("--vus-extra-limit", type=int, default=1000)
    parser.add_argument("--delay", type=float, default=0.5)
    run(parser.parse_args())
