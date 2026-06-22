#!/usr/bin/env python3
"""Scan PubMed topic directions for review-topic scouting.

Example:
  python pubmed_topic_scan.py --direction "gut microbiome|Alzheimer disease" \
    --direction "tau|gut microbiome|Alzheimer disease"
"""

import argparse
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date


BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def get_json(endpoint, params):
    url = f"{BASE}/{endpoint}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "medical-review-topic-scout/1.0 (topic selection; contact: local-user)"
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def quote_term(term, field="Title/Abstract"):
    term = term.strip()
    if "[" in term:
        return term
    if " " in term or "'" in term or "-" in term:
        return f'"{term}"[{field}]'
    return f"{term}[{field}]"


def parse_block(block_text, field="Title/Abstract", include_mesh=True):
    """Parse one concept block: synonyms separated by /; MeSH by mesh:term."""
    out = []
    for raw in block_text.split("/"):
        term = raw.strip()
        if not term:
            continue
        if term.lower().startswith("mesh:"):
            if not include_mesh:
                continue
            mesh = term.split(":", 1)[1].strip()
            if " " in mesh:
                out.append(f'"{mesh}"[MeSH Terms]')
            else:
                out.append(f"{mesh}[MeSH Terms]")
        else:
            out.append(quote_term(term, field=field))
    return out


def build_query(blocks, years=None, review=False, title_only=False):
    parts = []
    for block in blocks:
        terms = parse_block(
            block,
            field="Title" if title_only else "Title/Abstract",
            include_mesh=not title_only,
        )
        if terms:
            parts.append("(" + " OR ".join(terms) + ")")
    q = " AND ".join(parts)
    if review:
        q = f"({q}) AND (review[Publication Type] OR systematic review[Publication Type] OR meta-analysis[Publication Type] OR review[Title] OR meta-analysis[Title] OR systematic[Title])"
    if years:
        start, end = years
        q = f"({q}) AND ({start}:{end}[Date - Publication])"
    return q


def esearch(query, retmax=5, sort="pub+date"):
    data = get_json(
        "esearch.fcgi",
        {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": retmax,
            "sort": sort,
        },
    )
    result = data.get("esearchresult", {})
    return int(result.get("count", 0)), result.get("idlist", []), result.get("querytranslation", "")


def esummary(pmids):
    if not pmids:
        return []
    data = get_json(
        "esummary.fcgi",
        {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "json",
        },
    )
    out = []
    for pmid in data.get("result", {}).get("uids", []):
        rec = data["result"][pmid]
        out.append(
            {
                "pmid": pmid,
                "title": rec.get("title", ""),
                "journal": rec.get("fulljournalname", rec.get("source", "")),
                "pubdate": rec.get("pubdate", ""),
            }
        )
    return out


def label(total5, direct_reviews_recent, direct_reviews_all, title_reviews_recent=0):
    if title_reviews_recent >= 2:
        return "严重饱和"
    if direct_reviews_recent >= 5 and total5 >= 100:
        return "饱和"
    if direct_reviews_recent >= 2:
        return "近期有综述"
    if direct_reviews_recent == 1:
        return "刚被占/需差异化"
    if direct_reviews_all == 0 and total5 >= 30:
        return "空白/有空间"
    if total5 < 20:
        return "略窄"
    return "有空间"


def score_direction(total5, reviews_recent, title_reviews_recent, reviews_all):
    """Score 0-100 for review topic viability, not scientific merit."""
    if total5 < 10:
        volume = 5
    elif total5 < 30:
        volume = 15
    elif total5 <= 180:
        volume = 30
    elif total5 <= 350:
        volume = 22
    else:
        volume = 12

    if title_reviews_recent >= 2:
        competition = 2
    elif title_reviews_recent == 1:
        competition = 10
    elif reviews_recent >= 5:
        competition = 6
    elif reviews_recent >= 2:
        competition = 14
    elif reviews_all == 0:
        competition = 25
    else:
        competition = 20

    timeliness = 20 if total5 >= 30 else max(5, int(total5 / 30 * 20))
    tractability = 15 if 30 <= total5 <= 250 else 10 if total5 > 250 else 7
    differentiation = 10 if title_reviews_recent == 0 and reviews_recent <= 1 else 5
    return min(100, volume + competition + timeliness + tractability + differentiation)


def scan_direction(direction, current_year):
    blocks = [x.strip() for x in direction.split("|") if x.strip()]
    five_years = (current_year - 4, current_year)
    three_years = (current_year - 2, current_year)
    all_query = build_query(blocks)
    five_query = build_query(blocks, five_years)
    review_query = build_query(blocks, review=True)
    review_recent_query = build_query(blocks, three_years, review=True)
    title_review_recent_query = build_query(blocks, three_years, review=True, title_only=True)
    total_all, latest_ids, all_translation = esearch(all_query, retmax=5)
    time.sleep(0.34)
    total5, _, five_translation = esearch(five_query, retmax=0)
    time.sleep(0.34)
    reviews_all, review_ids, review_translation = esearch(review_query, retmax=5)
    time.sleep(0.34)
    reviews_recent, recent_review_ids, recent_review_translation = esearch(review_recent_query, retmax=5)
    time.sleep(0.34)
    title_reviews_recent, title_recent_review_ids, title_review_translation = esearch(title_review_recent_query, retmax=5)
    time.sleep(0.34)
    viability = score_direction(total5, reviews_recent, title_reviews_recent, reviews_all)
    return {
        "direction": " x ".join(blocks),
        "blocks": blocks,
        "query_all": all_query,
        "query_5y": five_query,
        "query_review": review_query,
        "query_recent_review": review_recent_query,
        "query_title_recent_review": title_review_recent_query,
        "query_translation_all": all_translation,
        "query_translation_5y": five_translation,
        "query_translation_review": review_translation,
        "query_translation_recent_review": recent_review_translation,
        "query_translation_title_recent_review": title_review_translation,
        "total_all": total_all,
        "total_5y": total5,
        "reviews_all": reviews_all,
        "reviews_recent_3y": reviews_recent,
        "title_reviews_recent_3y": title_reviews_recent,
        "label": label(total5, reviews_recent, reviews_all, title_reviews_recent),
        "viability_score": viability,
        "latest_papers": esummary(latest_ids),
        "recent_reviews": esummary(title_recent_review_ids or recent_review_ids or review_ids),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--direction", action="append", required=True, help='Terms separated by "|", e.g. "tau|gut microbiome|Alzheimer disease"')
    ap.add_argument("--year", type=int, default=date.today().year)
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown")
    ap.add_argument("--csv", help="Write a CSV summary to this path")
    args = ap.parse_args()

    results = []
    for d in args.direction:
        results.append(scan_direction(d, args.year))

    if args.json:
        print(json.dumps({"search_date": date.today().isoformat(), "results": results}, ensure_ascii=False, indent=2))
        return

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "direction",
                    "total_5y",
                    "reviews_all",
                    "reviews_recent_3y",
                    "title_reviews_recent_3y",
                    "label",
                    "viability_score",
                    "query_5y",
                    "query_recent_review",
                ],
            )
            writer.writeheader()
            for r in results:
                writer.writerow({k: r.get(k, "") for k in writer.fieldnames})

    print(f"Search date: {date.today().isoformat()}")
    print()
    print("| Direction | 5-year count | Reviews all | Reviews recent 3y | Title-review recent 3y | Score | Label |")
    print("|---|---:|---:|---:|---:|---:|---|")
    for r in results:
        print(f"| {r['direction']} | {r['total_5y']} | {r['reviews_all']} | {r['reviews_recent_3y']} | {r['title_reviews_recent_3y']} | {r['viability_score']} | {r['label']} |")
    print()
    for r in results:
        print(f"## {r['direction']}")
        print(f"- 5-year query: `{r['query_5y']}`")
        print(f"- Review query: `{r['query_review']}`")
        print(f"- PubMed query translation: `{r['query_translation_5y']}`")
        if r["recent_reviews"]:
            print("- Recent/direct review samples:")
            for rec in r["recent_reviews"]:
                print(f"  - PMID {rec['pmid']}: {rec['title']} ({rec['journal']}, {rec['pubdate']})")
        if r["latest_papers"]:
            print("- Latest paper samples:")
            for rec in r["latest_papers"][:3]:
                print(f"  - PMID {rec['pmid']}: {rec['title']} ({rec['journal']}, {rec['pubdate']})")
        print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
