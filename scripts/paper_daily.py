#!/usr/bin/env python3
import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(REPO_ROOT, "paper_daily_config.json")
OUTPUT_PATH = os.path.join(REPO_ROOT, "daily-papers.md")
ARXIV_API = "http://export.arxiv.org/api/query"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    query = str(data.get("query", "")).strip()
    max_results = int(data.get("max_results", 5))
    if not query:
        raise ValueError("paper_daily_config.json must provide a non-empty 'query'")
    return query, max(1, min(max_results, 20))


def strip_html(text: str) -> str:
    no_tags = re.sub(r"<[^>]+>", "", text or "")
    return " ".join(no_tags.split())


def fetch_arxiv(query: str, max_results: int):
    params = urllib.parse.urlencode(
        {"search_query": query, "start": 0, "max_results": max_results, "sortBy": "submittedDate", "sortOrder": "descending"}
    )
    url = f"{ARXIV_API}?{params}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        xml_data = resp.read()
    root = ET.fromstring(xml_data)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    papers = []
    for entry in root.findall("atom:entry", ns):
        title = strip_html(entry.findtext("atom:title", default="", namespaces=ns))
        summary = strip_html(entry.findtext("atom:summary", default="", namespaces=ns))
        paper_id = entry.findtext("atom:id", default="", namespaces=ns)
        papers.append({"title": title, "summary_en": summary, "url": paper_id})
    return papers


def translate_to_zh(text: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return "未配置 OPENAI_API_KEY，无法自动翻译。"

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    payload = json.dumps(
        {
            "model": model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": "You are a precise academic translator."},
                {"role": "user", "content": f"Translate the following abstract into Chinese, keep terminology accurate and concise:\n\n{text}"},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        content = result["choices"][0]["message"]["content"].strip()
        return content
    except Exception as exc:
        return f"翻译失败: {exc}"


def write_markdown(query: str, papers, fetch_error: str = ""):
    today = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
    lines = [
        "# Daily Papers",
        "",
        f"- Date (UTC): {today}",
        f"- Query: `{query}`",
        f"- Count: {len(papers)}",
        "",
    ]
    if fetch_error:
        lines.extend([f"> 获取 arXiv 数据失败：{fetch_error}", ""])
    if not papers:
        lines.extend(["No papers found.", ""])
    for idx, paper in enumerate(papers, start=1):
        zh = translate_to_zh(paper["summary_en"])
        lines.extend(
            [
                f"## {idx}. {paper['title']}",
                "",
                f"- Link: {paper['url']}",
                "",
                "### Abstract (EN)",
                "",
                paper["summary_en"],
                "",
                "### 摘要 (ZH)",
                "",
                zh,
                "",
            ]
        )
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).strip() + "\n")


def main():
    query, max_results = load_config()
    fetch_error = ""
    try:
        papers = fetch_arxiv(query, max_results)
    except Exception as exc:
        papers = []
        fetch_error = str(exc)
    write_markdown(query, papers, fetch_error)
    print(f"Generated {OUTPUT_PATH} with {len(papers)} papers.")


if __name__ == "__main__":
    main()
