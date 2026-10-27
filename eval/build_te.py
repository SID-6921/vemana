# Copyright 2026 Udgam Labs. Licensed under the Apache License, Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0).
"""Build a Telugu Wikipedia fresh-text set for bits-per-byte evaluation.

The crawl stage enumerates mainspace creation log events, rejects redirects, recreated pages, copied-content summaries,
list-like titles, bot-created pages, and non-Telugu or short extracts, then saves accepted articles and a candidate
reject log. The finalize stage re-checks pages for deletion, hidden revisions, and suspected AI-generated text before
writing the attributed parquet table. HTTP responses can be cached, and all sample ordering is seeded.

The October 2026 Telugu set defaults cover first revisions from 2026-09-01 through 2026-10-22 (inclusive), target
6,000,000 UTF-8 bytes, and use seed 20261023. Articles need at least 120 prose words, are capped at 1,200 words, and
must have at least 2,500 bytes of wikitext. Run `python build_te.py crawl` to collect candidates and
`python build_te.py finalize crawl.jsonl` to screen and publish the table.
"""
import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import random
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

UA = "udgam-evals-te/1.0 (https://github.com/udgamlabs/udgam-evals) python-urllib"
WIKI_API = "https://te.wikipedia.org/w/api.php"
SOURCE = "te.wikipedia"

# ----------------------------------------------------------------------------------------------------------
# HTTP with retry, pacing and an optional on-disk cache of raw responses
# ----------------------------------------------------------------------------------------------------------
_last_call = collections.defaultdict(float)
CACHE_DIR = None
STATS = collections.Counter()


def http_get(url, min_interval, host_key, tries=8):
    """GET url (bytes). Paces calls per host; retries on 429/5xx/network errors."""
    key = hashlib.sha1(url.encode()).hexdigest()
    cpath = os.path.join(CACHE_DIR, key[:2], key) if CACHE_DIR else None
    if cpath and os.path.exists(cpath):
        STATS["cache_hit"] += 1
        with open(cpath, "rb") as f:
            return f.read()
    delay = 2.0
    for attempt in range(tries):
        wait = _last_call[host_key] + min_interval - time.time()
        if wait > 0:
            time.sleep(wait)
        _last_call[host_key] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
            with urllib.request.urlopen(req, timeout=90) as r:
                body = r.read()
            STATS["http_" + host_key] += 1
            if cpath:
                os.makedirs(os.path.dirname(cpath), exist_ok=True)
                with open(cpath, "wb") as f:
                    f.write(body)
            return body
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ConnectionError) as e:
            code = getattr(e, "code", None)
            if code not in (None, 429, 500, 502, 503, 504) and attempt >= 1:
                raise
            retry_after = None
            if code == 429 and getattr(e, "headers", None) is not None:
                try:
                    retry_after = float(e.headers.get("Retry-After"))
                except (TypeError, ValueError):
                    retry_after = None
            sleep_s = max(delay, (retry_after or 0) + 2)
            print(f"  [retry {attempt + 1}/{tries}] {host_key} {code or type(e).__name__}; sleeping {sleep_s:.0f}s",
                  file=sys.stderr)
            time.sleep(sleep_s)
            delay = min(delay * 2, 60)
    raise RuntimeError("giving up on " + url)


def wiki_api(**params):
    params.update(format="json", formatversion=2, maxlag=5)
    url = WIKI_API + "?" + urllib.parse.urlencode(params)
    for _ in range(5):
        d = json.loads(http_get(url, 1.2, "wiki"))
        if "error" in d and d["error"].get("code") == "maxlag":
            time.sleep(5)
            continue
        if "error" in d:
            raise RuntimeError(f"wiki api error {d['error']} for {params}")
        return d
    raise RuntimeError("maxlag persisted")


# ----------------------------------------------------------------------------------------------------------
# Text helpers
# ----------------------------------------------------------------------------------------------------------
def norm_text(s):
    s = unicodedata.normalize("NFC", s)
    s = s.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    s = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def words(s):
    return len(s.split())


def telugu_letter_ratio(s):
    """Share of alphabetic/combining-mark characters that are in the Telugu Unicode block."""
    letters = [c for c in s if c.isalpha() or unicodedata.category(c) in ("Mn", "Mc")]
    return (sum("\u0c00" <= c <= "\u0c7f" for c in letters) / len(letters)) if letters else 0.0


def dedup_key(s):
    return hashlib.sha1(re.sub(r"\W+", " ", s.lower()).strip().encode()).hexdigest()


def utf8_len(s):
    return len(s.encode("utf-8"))


TELUGU_WORD = re.compile(r"[\u0c00-\u0c7f]+")


def template_skeleton(body, title):
    """First 300 body characters with digits and Telugu title words removed and whitespace normalized."""
    sample = re.sub(r"\d+", " ", body[:300])
    title_words = set(TELUGU_WORD.findall(title))
    for token in sorted(title_words, key=len, reverse=True):
        sample = re.sub(rf"(?<![\u0c00-\u0c7f]){re.escape(token)}(?![\u0c00-\u0c7f])", " ", sample)
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", sample)).strip().lower()


def skeleton_hash(body, title):
    return hashlib.sha1(template_skeleton(body, title).encode("utf-8")).hexdigest()


# ----------------------------------------------------------------------------------------------------------
# Wikipedia
# ----------------------------------------------------------------------------------------------------------
STOP_SECTIONS = {
    "references", "external links", "see also", "further reading", "notes", "sources", "bibliography", "footnotes",
    "citations", "works cited", "explanatory notes", "general references", "notes and references",
    "references and notes", "selected bibliography", "gallery", "external links and further reading",
    "notes and sources", "cited works", "footnotes and references",
    "మూలాలు", "మూలం", "వనరులు", "బయటి లింకులు", "బాహ్య లంకెలు", "బయటి లంకెలు", "ఇవి కూడా చూడండి",
    "ఇతర లింకులు", "గమనికలు", "ఉల్లేఖనలు", "ఆధారాలు", "గ్రంథసూచి", "చిత్రమాలిక", "చిత్రాలు", "మరింత చదవండి",
    "సూచికలు", "ఉపయుక్త గ్రంథాలు", "పాదపీఠికలు",
}
BAD_TITLE = re.compile(
    r"^(List|Lists|Index|Outline|Timeline|Glossary|Bibliography|Discography|Filmography) of |"
    r"\((disambiguation|surname|given name|name)\)$|^\d{4}.*(season|results|elections?)$|"
    r"జాబితా|\(అయోమయ నివృత్తి\)|^\d+$",
    re.I,
)
COPIED_COMMENT = re.compile(
    r"\b(split|spun|spin(?:ning)?[ -](?:off|out)|cop(?:y|ied|ying)|copy from|merged?|forked|"
    r"import(?:ed)?|restor\w+|undelet\w+|unredirect\w+|draft|moved|rv|revert\w*)\b",
    re.I,
)
MARKUP_LEFTOVER = re.compile(
    r"\{\{|\}\}|\[\[|\]\]|</?[a-zA-Z][^>]*>|\\displaystyle|&[a-z]{2,8};|\|\s*\w+\s*=|"
    r"\bwikitable\b|^\s*[*#:;]",
    re.M,
)
HEADING = re.compile(r"^(={2,6})\s*(.*?)\s*\1\s*$")
SENT_END = re.compile(r"[.!?।॥…][\"'”’»›)\]\}」』】〕》〉]*$")


def clean_wiki_extract(extract, max_words):
    """Return (paragraphs, prose_words, other_words) from a plain-text extract with == headings ==."""
    paras, prose_w, other_w = [], 0, 0
    skip_level = None
    for raw in extract.split("\n"):
        line = norm_text(raw)
        if not line:
            continue
        m = HEADING.match(line)
        if m:
            level, title = len(m.group(1)), norm_text(m.group(2)).lower()
            if skip_level is not None and level <= skip_level:
                skip_level = None
            if skip_level is None and title in STOP_SECTIONS:
                skip_level = level
            continue
        if skip_level is not None:
            continue
        w = words(line)
        if w >= 6 and SENT_END.search(line) and not MARKUP_LEFTOVER.search(line):
            paras.append(line)
            prose_w += w
        else:
            other_w += w
    return paras, prose_w, other_w


def truncate_paras(paras, max_words):
    out, n = [], 0
    for p in paras:
        w = words(p)
        if out and n + w > max_words:
            break
        out.append(p)
        n += w
    return out


def translation_source_language(comment):
    """Best-effort source language from a Content Translation log summary; otherwise None."""
    linked = re.search(r"\[\[?\s*:?[ \t]*([a-z]{2,3}(?:-[a-z0-9]+)?):", comment, re.I)
    if linked:
        return linked.group(1).lower()
    named = re.search(r"\bfrom\s+(?:the\s+)?([A-Za-z][A-Za-z-]*)\b", comment, re.I)
    return named.group(1).lower() if named else None


def wiki_enumerate_creates(day_start, day_end):
    """All mainspace create log events for UTC dates in [day_start, day_end), one day at a time."""
    events = []
    d = day_start
    while d < day_end:
        nxt = d + dt.timedelta(days=1)
        cont = {}
        n_day = 0
        while True:
            res = wiki_api(action="query", list="logevents", letype="create", lenamespace=0, lelimit=500,
                           lestart=nxt.strftime("%Y-%m-%dT00:00:00Z"), leend=d.strftime("%Y-%m-%dT00:00:00Z"),
                           ledir="older", leprop="ids|title|timestamp|comment|tags|type|user", **cont)
            for e in res["query"]["logevents"]:
                events.append({"logid": e["logid"], "pageid": e["pageid"], "revid": e["revid"],
                               "title": e["title"], "timestamp": e["timestamp"], "comment": e.get("comment", ""),
                               "tags": e.get("tags", []), "user": e.get("user")})
                n_day += 1
            if "continue" in res:
                cont = res["continue"]
            else:
                break
        print(f"  {d} creates: {n_day}", file=sys.stderr)
        d = nxt
    return events


def wiki_users_are_bots(usernames, cache):
    """Check unknown names in batches and retain each result for the rest of the crawl."""
    unknown = sorted({u for u in usernames if u and u not in cache})
    for c0 in range(0, len(unknown), 50):
        batch = unknown[c0:c0 + 50]
        res = wiki_api(action="query", list="users", ususers="|".join(batch), usprop="groups")
        returned = res["query"].get("users", [])
        for u in returned:
            cache[u.get("name", "")] = "bot" in u.get("groups", [])
        for name in batch:
            cache.setdefault(name, False)
    return {u: cache.get(u, False) for u in usernames if u}


def wiki_build(args, rng, rejects):
    start = dt.date.fromisoformat(args.wiki_start)
    end = dt.date.fromisoformat(args.wiki_end) + dt.timedelta(days=1)  # inclusive end date
    if args.dry_days > 0:
        end = min(end, start + dt.timedelta(days=args.dry_days))
    start_ts = start.strftime("%Y-%m-%dT00:00:00Z")
    shown_end = end - dt.timedelta(days=1)
    print(f"[wiki] enumerating mainspace page creations {start} .. {shown_end}", file=sys.stderr)
    events = wiki_enumerate_creates(start, end)
    counts = collections.Counter()
    pool = collections.defaultdict(list)
    for e in events:
        counts["events"] += 1
        tags = set(e["tags"])
        # Do not keyword-match the wikitext embedded in MediaWiki's automatic creation summary.
        cmt = re.sub(r"Created page with .*", "", e["comment"], flags=re.S)
        if "mw-new-redirect" in tags or re.search(r"redirect", cmt, re.I):
            counts["skip_redirect_event"] += 1
            continue
        if "mw-recreated" in tags:
            counts["skip_recreated"] += 1
            continue
        if COPIED_COMMENT.search(cmt):
            counts["skip_copied_comment"] += 1
            continue
        if BAD_TITLE.search(e["title"]):
            counts["skip_title_pattern"] += 1
            continue
        pool[e["timestamp"][:10]].append(e)
    for day in pool.values():
        rng.shuffle(day)
    days = sorted(pool)
    print(f"[wiki] {counts['events']} create events; candidates after event-level filters: "
          f"{sum(len(v) for v in pool.values())} over {len(days)} days", file=sys.stderr)
    # Round-robin across dates so a limited smoke run still spans the full requested window.
    order = []
    i = 0
    while any(i < len(pool[d]) for d in days):
        for d in days:
            if i < len(pool[d]):
                order.append(pool[d][i])
        i += 1
    if args.max_candidates > 0:
        order = order[:args.max_candidates]

    docs, seen, skeleton_counts, total_bytes = [], set(), collections.Counter(), 0
    bot_cache = {}
    chunk = 50
    for c0 in range(0, len(order), chunk):
        if total_bytes >= args.wiki_bytes:
            break
        batch = order[c0:c0 + chunk]
        bots = wiki_users_are_bots([e.get("user") for e in batch], bot_cache)
        # (a) page info for the batch
        info = wiki_api(action="query", pageids="|".join(str(e["pageid"]) for e in batch), prop="info|pageprops",
                        ppprop="disambiguation")
        pages = {p["pageid"]: p for p in info["query"]["pages"] if not p.get("missing") and not p.get("invalid")}
        # (b) first-revision check using each log event's creation revid
        rev = wiki_api(action="query", revids="|".join(str(e["revid"]) for e in batch), prop="revisions",
                       rvprop="ids|timestamp|size")
        revinfo = {}
        for p in rev["query"]["pages"]:
            for r in p.get("revisions", []):
                revinfo[r["revid"]] = (p.get("pageid"), r)
        for e in batch:
            if total_bytes >= args.wiki_bytes:
                break
            creator_is_bot = bots.get(e.get("user"), False)
            rec = dict(e, source=SOURCE, creator_is_bot=creator_is_bot)
            pg = pages.get(e["pageid"])
            if creator_is_bot:
                rec["status"] = "rejected:bot_created"
            elif pg is None:
                rec["status"] = "rejected:missing_or_deleted"
            elif pg.get("redirect"):
                rec["status"] = "rejected:redirect"
            elif pg.get("ns") != 0:
                rec["status"] = "rejected:not_mainspace"
            elif "disambiguation" in pg.get("pageprops", {}):
                rec["status"] = "rejected:disambiguation"
            elif pg.get("length", 0) < args.wiki_min_wikitext_bytes:
                rec["status"] = "rejected:too_short_wikitext"
            elif e["revid"] not in revinfo or revinfo[e["revid"]][1].get("parentid") != 0 \
                    or revinfo[e["revid"]][1]["timestamp"] < start_ts:
                rec["status"] = "rejected:not_first_revision_after_start"
            else:
                rec["first_rev_timestamp"] = revinfo[e["revid"]][1]["timestamp"]
                # (c) full plain-text extract, one page per request
                ex = wiki_api(action="query", pageids=str(e["pageid"]), prop="extracts|info", explaintext=1,
                              exsectionformat="wiki", exlimit=1)
                p = ex["query"]["pages"][0]
                extract = p.get("extract", "")
                paras, prose_w, other_w = clean_wiki_extract(extract, args.wiki_max_words)
                tags = set(e["tags"])
                cx = bool(tags & {"contenttranslation", "contenttranslation-v2"}) or bool(
                    re.search(r"\bcreated by translating the page\b", e.get("comment", ""), re.I))
                source_language = translation_source_language(e.get("comment", "")) if cx else None
                rec.update(current_title=p.get("title"), fetched_revid=p.get("lastrevid"),
                           prose_words=prose_w, other_words=other_w, cx=cx, source_language=source_language)
                if prose_w < args.wiki_min_words:
                    rec["status"] = "rejected:under_min_words"
                elif prose_w / max(1, prose_w + other_w) < 0.7:
                    rec["status"] = "rejected:list_like"
                else:
                    paras = truncate_paras(paras, args.wiki_max_words)
                    body = "\n\n".join(paras)
                    title = norm_text(p["title"])
                    text = f"{title}\n\n{body}"
                    if telugu_letter_ratio(text) < 0.85:
                        rec["status"] = "rejected:non_telugu_like"
                    else:
                        exact_body_key = dedup_key(body[:400])
                        exact_text_key = dedup_key(text)
                        skeleton = skeleton_hash(body, title)
                        if exact_body_key in seen or exact_text_key in seen:
                            rec["status"] = "rejected:duplicate"
                        elif skeleton_counts[skeleton] >= 5:
                            rec["status"] = "rejected:template_like"
                        else:
                            seen.add(exact_text_key)
                            seen.add(exact_body_key)
                            skeleton_counts[skeleton] += 1
                            nb = utf8_len(text)
                            total_bytes += nb
                            rec["status"] = "accepted"
                            rec["bytes"] = nb
                            docs.append({
                                "id": f"wiki:{e['pageid']}",
                                "source": SOURCE,
                                "title": title,
                                "created": rev_ts(revinfo[e["revid"]][1]["timestamp"]),
                                "url": f"https://te.wikipedia.org/w/index.php?title="
                                       f"{urllib.parse.quote(p['title'].replace(' ', '_'))}&oldid={p.get('lastrevid')}",
                                "licence": "CC-BY-SA-4.0",
                                "text": text,
                                "meta": {"page_id": e["pageid"], "creation_revid": e["revid"],
                                         "fetched_revid": p.get("lastrevid"), "log_title": e["title"],
                                         "creator": e.get("user"), "creator_is_bot": False, "cx": cx,
                                         "source_language": source_language, "prose_words": prose_w,
                                         "words_in_text": words(text)},
                            })
            rejects.append({k: v for k, v in rec.items() if k != "comment"})
        print(f"[wiki] processed {min(c0 + chunk, len(order))}/{len(order)} candidates; "
              f"{len(docs)} accepted, {total_bytes / 1e6:.2f} MB", file=sys.stderr)
    counts["bot_users_checked"] = len(bot_cache)
    return docs, counts


def rev_ts(ts):
    return ts  # ISO-8601 UTC, e.g. 2026-10-09T23:32:00Z


# Finalize: screen Wikipedia pages again, then write the published table
# ----------------------------------------------------------------------------------------------------------
AI_CATEGORY = re.compile(
    r"suspected AI-generated texts|AI-generated content proposed for deletion|"
    r"కృత్రిమ మేధస్సు.*(?:సృష్టి|రచన|రూపొందించ)|ఏఐ.*(?:సృష్టి|రచన|రూపొందించ)",
    re.I,
)


def wiki_screen(docs):
    """Return drop reasons for deleted pages, hidden revisions, and AI-text categories."""
    wiki = [d for d in docs if d["source"] == SOURCE]
    drop = {}
    for c0 in range(0, len(wiki), 50):
        batch = wiki[c0:c0 + 50]
        cont = {}
        while True:
            res = wiki_api(action="query", pageids="|".join(str(d["meta"]["page_id"]) for d in batch),
                           prop="categories", cllimit="max", **cont)
            for p in res["query"]["pages"]:
                if p.get("missing") or p.get("invalid"):
                    drop[p["pageid"]] = "deleted_since_crawl"
                elif any(AI_CATEGORY.search(c["title"]) for c in p.get("categories", [])):
                    drop.setdefault(p["pageid"], "tagged_suspected_ai_text")
            if "continue" in res:
                cont = res["continue"]
            else:
                break
        res = wiki_api(action="query", revids="|".join(str(d["meta"]["fetched_revid"]) for d in batch),
                       prop="revisions", rvprop="ids")
        bad = {int(k) for k in res["query"].get("badrevids", {})}
        for d in batch:
            if d["meta"]["fetched_revid"] in bad:
                drop.setdefault(d["meta"]["page_id"], "revision_hidden")
        print(f"[screen] {min(c0 + 50, len(wiki))}/{len(wiki)} pages checked, {len(drop)} to drop", file=sys.stderr)
    return drop


def to_row(d):
    m = d["meta"]
    page_id = m["page_id"]
    history = f"https://te.wikipedia.org/w/index.php?curid={page_id}&action=history"
    credit = (f'"{d["title"]}", తెలుగు వికీపీడియా, revision {m["fetched_revid"]} ({d["url"]}), '
              f"వికీపీడియా సహకారులచే (రచయితలు: {history}). CC BY-SA 4.0. "
              "మార్పులు: సాధారణ పాఠ్యంగా మార్చబడింది; సూచనలు, శీర్షికలు, జాబితాలు, చిన్న పంక్తులు తొలగించబడ్డాయి; "
              "పొడవైన వ్యాసాలు పేరాగ్రాఫ్ సరిహద్దు వద్ద కత్తిరించబడ్డాయి.")
    return {"id": d["id"], "source": SOURCE, "title": d["title"], "url": d["url"], "created": d["created"],
            "licence": "CC-BY-SA-4.0", "attribution": credit, "text": d["text"],
            "n_bytes": utf8_len(d["text"]), "wiki_page_id": page_id, "wiki_revision_id": m["fetched_revid"],
            "content_translation": bool(m.get("cx", False)), "creator_is_bot": False,
            "n_words": words(d["text"])}


def finalize(args):
    import pyarrow as pa
    import pyarrow.parquet as pq

    with open(args.crawl, encoding="utf-8") as f:
        docs = [json.loads(line) for line in f]
    drop = wiki_screen(docs)
    rows, excluded = [], []
    for d in docs:
        reason = drop.get(d["meta"].get("page_id"))
        if reason:
            excluded.append({"id": d["id"], "title": d["title"], "url": d["url"], "reason": reason})
        else:
            rows.append(to_row(d))
    schema = pa.schema([
        ("id", pa.string()), ("source", pa.string()), ("title", pa.string()), ("url", pa.string()),
        ("created", pa.string()), ("licence", pa.string()), ("attribution", pa.string()),
        ("text", pa.string()), ("n_bytes", pa.int64()), ("wiki_page_id", pa.int64()),
        ("wiki_revision_id", pa.int64()), ("content_translation", pa.bool_()),
        ("creator_is_bot", pa.bool_()), ("n_words", pa.int64()),
    ])
    os.makedirs(os.path.join(args.out_dir, "data"), exist_ok=True)
    out = os.path.join(args.out_dir, "data", "test.parquet")
    pq.write_table(pa.Table.from_pylist(rows, schema=schema), out)
    with open(os.path.join(args.out_dir, "excluded.jsonl"), "w", encoding="utf-8") as f:
        for e in excluded:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    with open(args.crawl, "rb") as f:
        crawl_hash = hashlib.sha256(f.read()).hexdigest()
    with open(out, "rb") as f:
        parquet_hash = hashlib.sha256(f.read()).hexdigest()
    summary = {"screened_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "crawl_sha256": crawl_hash,
               "excluded": dict(collections.Counter(e["reason"] for e in excluded)), "sources": {}}
    if rows:
        summary["sources"][SOURCE] = {"docs": len(rows), "bytes": sum(r["n_bytes"] for r in rows),
                                      "created_min": min(r["created"] for r in rows),
                                      "created_max": max(r["created"] for r in rows)}
    summary["docs"] = len(rows)
    summary["bytes"] = sum(r["n_bytes"] for r in rows)
    summary["parquet_sha256"] = parquet_hash
    with open(os.path.join(args.out_dir, "build_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


# ----------------------------------------------------------------------------------------------------------
def crawl(args):
    global CACHE_DIR
    CACHE_DIR = args.cache_dir
    os.makedirs(args.raw_dir, exist_ok=True)
    t0 = time.time()
    meta = {"script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
            "run_started_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "args": {k: v for k, v in vars(args).items() if k not in ("out", "raw_dir", "cache_dir")},
            "user_agent": UA}
    rejects = []
    docs, counts = wiki_build(args, random.Random(args.seed + 1), rejects)
    with open(os.path.join(args.raw_dir, "wiki_candidates.jsonl"), "w", encoding="utf-8") as f:
        for r in rejects:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    meta["wiki_event_counts"] = dict(counts)
    meta["wiki_status_counts"] = dict(collections.Counter(r["status"] for r in rejects))

    # Keep document order stable across runs, independent of API pagination order.
    final, seen = [], set()
    for d in sorted(docs, key=lambda d: (d["source"], d["created"], d["id"])):
        k = dedup_key(d["text"])
        if k in seen:
            continue
        seen.add(k)
        final.append(d)
    with open(args.out, "w", encoding="utf-8") as f:
        for d in final:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    summary = {}
    if final:
        summary[SOURCE] = {"docs": len(final), "bytes": sum(utf8_len(d["text"]) for d in final),
                           "words": sum(words(d["text"]) for d in final),
                           "created_min": min(d["created"] for d in final),
                           "created_max": max(d["created"] for d in final)}
    summary["total_bytes"] = sum(v["bytes"] for v in summary.values())
    with open(args.out, "rb") as f:
        output_hash = hashlib.sha256(f.read()).hexdigest()
    meta.update(summary=summary, http_stats=dict(STATS), elapsed_s=round(time.time() - t0, 1),
                output_sha256=output_hash)
    with open(args.out + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def selftest():
    assert telugu_letter_ratio("తెలుగు") == 1.0
    assert telugu_letter_ratio("Wikipedia") == 0.0
    assert telugu_letter_ratio("") == 0.0
    assert telugu_letter_ratio("కి English") < 0.85
    assert telugu_letter_ratio("అ\u0301") == 0.5  # the non-Telugu combining mark stays in the denominator

    valid = "ఇది తెలుగు వికీపీడియా కోసం ఒక సరళమైన వాక్యం మాత్రమే."
    paras, prose_w, _ = clean_wiki_extract(valid, 1200)
    assert paras == [valid] and prose_w >= 6
    assert clean_wiki_extract("ఇది తెలుగు వికీపీడియా కోసం ఒక సరళమైన వాక్యం మాత్రమే॥", 1200)[0]
    assert clean_wiki_extract("ఇది తెలుగు వాక్యం ముగియలేదు", 1200)[0] == []
    assert clean_wiki_extract("ఇది తెలుగు పదాలు [[లింకు]] కలిగిన వాక్యం.", 1200)[0] == []
    stopped = valid + "\n== మూలాలు ==\n" + valid
    assert clean_wiki_extract(stopped, 1200)[0] == [valid]
    assert clean_wiki_extract("This English sentence has six ordinary words.", 1200)[0]

    assert BAD_TITLE.search("List of Telugu films")
    assert BAD_TITLE.search("జాబితా తెలుగు సినిమాలు")
    assert BAD_TITLE.search("తెలుగు జాబితా సినిమాలు")
    assert BAD_TITLE.search("తెలుగు సినిమా (అయోమయ నివృత్తి)")
    assert BAD_TITLE.search("2026")
    assert not BAD_TITLE.search("2026 తెలుగు సినిమా")
    assert not BAD_TITLE.search("తెలుగు వికీపీడియా")

    cx_comment = "Created by translating the page [[en:Example]]"
    assert not COPIED_COMMENT.search(cx_comment)
    assert translation_source_language(cx_comment) == "en"
    for summary in ("Split from another article", "Merged into this page", "Copied from elsewhere",
                    "Moved page", "Restored old version", "Imported page", "Reverted edit", "Draft creation"):
        assert COPIED_COMMENT.search(summary), summary

    a = "గ్రామం 123లో వ్యవసాయం మరియు నీటి వనరులు ప్రధానమైనవి."
    b = "గ్రామం 999లో వ్యవసాయం మరియు నీటి వనరులు ప్రధానమైనవి."
    assert template_skeleton(a, "గ్రామం 2026") == template_skeleton(b, "గ్రామం 2025")
    assert skeleton_hash(a, "గ్రామం 2026") == skeleton_hash(b, "గ్రామం 2025")
    assert template_skeleton(a, "గ్రామం 2026") != template_skeleton(
        "గ్రామం 999లో జనాభా మరియు వాతావరణం పూర్తిగా భిన్నమైనవి.", "గ్రామం 2025")
    print("selftest passed")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("crawl", help="fetch candidates from Telugu Wikipedia")
    c.add_argument("--out", default="crawl.jsonl")
    c.add_argument("--raw-dir", default="raw")
    c.add_argument("--cache-dir", default=None, help="cache raw HTTP responses here (makes re-runs identical)")
    c.add_argument("--seed", type=int, default=20261023)
    c.add_argument("--wiki-start", default="2026-09-01")
    c.add_argument("--wiki-end", default="2026-10-22", help="last creation date (inclusive)")
    c.add_argument("--wiki-bytes", type=int, default=6_000_000)
    c.add_argument("--wiki-min-words", type=int, default=120)
    c.add_argument("--wiki-max-words", type=int, default=1200)
    c.add_argument("--wiki-min-wikitext-bytes", type=int, default=2500)
    c.add_argument("--max-candidates", type=int, default=0, help="limit page candidates after date round-robin; 0 is unlimited")
    c.add_argument("--dry-days", type=int, default=0, help="enumerate only the first N requested days; 0 is unlimited")
    f = sub.add_parser("finalize", help="screen Telugu Wikipedia pages again and write data/test.parquet")
    f.add_argument("crawl", help="crawl.jsonl from the crawl stage")
    f.add_argument("--out-dir", default=".")
    sub.add_parser("selftest", help="run offline checks for the Telugu text filters")
    args = ap.parse_args()
    if args.cmd == "crawl":
        crawl(args)
    elif args.cmd == "finalize":
        finalize(args)
    else:
        selftest()


if __name__ == "__main__":
    main()
