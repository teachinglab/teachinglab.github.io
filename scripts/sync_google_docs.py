#!/usr/bin/env python3
"""Turn Google Docs into native Data Hub pages.

Each doc in DOCS is exported as HTML through the Drive API, cleaned of Google's
inline styling, comments and redirect links, and written to a .qmd. Each
heading becomes a real Quarto heading, so the page gets a table of contents,
search and site styling, and the content between headings is kept as cleaned
HTML so tables with merged cells survive intact.

The Azure deploy workflow runs this before `quarto render`, with a Drive
access token minted from the GOOGLE_DOCS_SA_KEY service account (the doc must
be shared with that account as a Viewer). Without a token it does nothing, so
local renders use the committed snapshot.

Usage:
  GOOGLE_DRIVE_TOKEN=... python3 scripts/sync_google_docs.py
  python3 scripts/sync_google_docs.py --from-file export.html   # test a local export
"""

import argparse
import base64
import datetime
import hashlib
import html
import os
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DOCS = [
    {
        "id": "1yvo1cW5i3OXtzN3Lf1lCRgw06Efbt0CH7n6PM53kELI",
        "output": "data_collection_overview.qmd",
        "image_dir": "Images/data_collection_overview",
        "title": "Data Collection Overview",
        "description": (
            "What we collect for each scope of work, survey and instrument "
            "links, tracking progress, ANAs, student data, and Stepback prep."
        ),
        "image": "Images/Surveys/guskey_framework.png",
    },
]

# Links that point at old homes of pages that now live elsewhere
LINK_REWRITES = [
    (r"^https://tl-data\.teachinglab\.org/shiny/", "https://tl-data.teachinglab.org/"),
    (r"^https://datahub\.teachinglab\.org/", "/"),
]

KEEP_TAGS = {
    "p", "ul", "ol", "li", "table", "tbody", "thead", "tr", "td", "th",
    "a", "img", "br", "strong", "em", "sup", "sub",
}
HEADING_TAGS = {"h1", "h2", "h3", "h4"}
VOID_TAGS = {"br", "img", "hr", "meta", "link", "col"}


def export_html(doc_id, token):
    url = (
        f"https://www.googleapis.com/drive/v3/files/{doc_id}/export"
        f"?mimeType=text/html"
    )
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def style_classes(raw_html):
    """Classes Google uses for bold and italic text (it never uses <b>/<i>)."""
    bold, italic = set(), set()
    style_block = " ".join(re.findall(r"<style[^>]*>(.*?)</style>", raw_html, re.S))
    for selector, body in re.findall(r"\.([\w-]+)\{([^}]*)\}", style_block):
        if re.search(r"font-weight:\s*(700|bold)", body):
            bold.add(selector)
        if re.search(r"font-style:\s*italic", body):
            italic.add(selector)
    return bold, italic


def clean_href(href):
    if href.startswith("https://www.google.com/url?"):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
        href = query.get("q", [href])[0]
    for pattern, replacement in LINK_REWRITES:
        href = re.sub(pattern, replacement, href)
    return href


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


class DocCleaner(HTMLParser):
    """Rebuilds the doc body as a list of ("heading", level, text, id) and
    ("html", fragment) blocks."""

    def __init__(self, bold, italic, image_writer):
        super().__init__(convert_charrefs=True)
        self.bold, self.italic = bold, italic
        self.image_writer = image_writer
        self.blocks = []
        self.buffer = []
        self.stack = []  # (tag, closing_markup) for every open tag
        self.in_body = False
        self.skip_depth = 0  # inside a comment thread or <style>
        self.heading = None
        self.seen_heading = False

    def handle_starttag(self, tag, attrs_list):
        attrs = dict(attrs_list)
        if tag == "body":
            self.in_body = True
            return
        if not self.in_body:
            return
        if self.skip_depth:
            if tag not in VOID_TAGS:
                self.skip_depth += 1
            return
        if tag == "style":
            self.skip_depth = 1
            return
        if tag in HEADING_TAGS:
            self.flush()
            self.heading = {"level": int(tag[1]), "text": [], "anchors": []}
            self.stack.append((tag, ""))
            return
        if self.heading is not None:
            if tag == "a" and attrs.get("id"):
                self.heading["anchors"].append(attrs["id"])
            if tag not in VOID_TAGS:
                self.stack.append((tag, ""))
            return

        classes = set(attrs.get("class", "").split())
        open_markup, close_markup = "", ""
        if tag == "span":
            # The Drive API export styles inline; the Docs UI export uses classes
            inline_style = attrs.get("style", "")
            if classes & self.bold or re.search(r"font-weight:\s*(700|bold)", inline_style):
                open_markup += "<strong>"
                close_markup = "</strong>" + close_markup
            if classes & self.italic or re.search(r"font-style:\s*italic", inline_style):
                open_markup += "<em>"
                close_markup = "</em>" + close_markup
        elif tag == "a":
            if attrs.get("href"):
                href = clean_href(attrs["href"])
                external = href.startswith("http") and "datahub.teachinglab.org" not in href
                target = ' target="_blank" rel="noopener"' if external else ""
                open_markup = f'<a href="{html.escape(href)}"{target}>'
                close_markup = "</a>"
            elif attrs.get("id"):
                # Bookmark targets used by the doc's own table of contents
                open_markup = f'<a id="{html.escape(attrs["id"])}">'
                close_markup = "</a>"
        elif tag == "img":
            if not self.seen_heading:
                return  # the letterhead logo above the first heading
            src = self.image_writer(attrs.get("src", ""))
            if src:
                alt = html.escape(attrs.get("alt", "") or attrs.get("title", ""))
                self.buffer.append(f'<img src="{src}" alt="{alt}" class="img-fluid doc-image">')
            return
        elif tag == "table":
            self.buffer.append('<div class="table-responsive"><table class="table table-sm doc-table">')
            self.stack.append((tag, "</table></div>"))
            return
        elif tag in ("td", "th"):
            span = "".join(
                f' {name}="{int(attrs[name])}"'
                for name in ("colspan", "rowspan")
                if attrs.get(name, "1").isdigit() and attrs.get(name, "1") != "1"
            )
            open_markup, close_markup = f"<{tag}{span}>", f"</{tag}>"
        elif tag in KEEP_TAGS:
            if tag in VOID_TAGS:
                self.buffer.append(f"<{tag}>")
                return
            open_markup, close_markup = f"<{tag}>", f"</{tag}>"

        if tag in VOID_TAGS:
            return
        self.buffer.append(open_markup)
        self.stack.append((tag, close_markup))

    def handle_endtag(self, tag):
        if not self.in_body:
            return
        if self.skip_depth:
            self.skip_depth -= 1
            return
        if tag == "body":
            self.flush()
            self.in_body = False
            return
        if tag in VOID_TAGS:
            return
        # Pop back to the matching open tag
        while self.stack:
            open_tag, close_markup = self.stack.pop()
            if self.heading is None or open_tag in HEADING_TAGS:
                self.buffer.append(close_markup)
            if open_tag == tag:
                break
        if tag in HEADING_TAGS and self.heading is not None:
            text = re.sub(r"\s+", " ", "".join(self.heading["text"])).strip()
            if text:
                self.blocks.append(("heading", self.heading["level"], text, self.heading["anchors"]))
                self.seen_heading = True
            self.heading = None

    def handle_data(self, data):
        if not self.in_body or self.skip_depth:
            return
        if self.heading is not None:
            self.heading["text"].append(data)
        else:
            self.buffer.append(html.escape(data, quote=False))

    def flush(self):
        fragment = "".join(self.buffer)
        self.buffer = []
        if fragment.strip():
            self.blocks.append(("html", fragment))


def preprocess(raw_html):
    """Remove comment markers and threads before parsing, which is simpler than
    tracking them inside the parser."""
    body = raw_html
    body = re.sub(r'<sup><a href="#cmnt\d+"[^>]*>.*?</a></sup>', "", body, flags=re.S)
    # Each comment thread is a <div> that starts with <p><a href="#cmnt_refN">
    body = re.sub(r'<div[^>]*><p[^>]*><a href="#cmnt_ref\d+".*?</div>', "", body, flags=re.S)
    return body


def tidy_fragment(fragment):
    # Collapse the empty wrappers Google leaves behind
    previous = None
    while previous != fragment:
        previous = fragment
        fragment = re.sub(r"<(strong|em)>(\s*)</\1>", r"\2", fragment)
        fragment = re.sub(r"</strong>(\s*)<strong>", r"\1", fragment)
        fragment = re.sub(r"</em>(\s*)<em>", r"\1", fragment)
        fragment = re.sub(r"<p>(\s|&nbsp;| )*</p>", "", fragment)
        fragment = re.sub(r"<li>(\s| )*</li>", "", fragment)
    # Google repeats every list as one <ul> per item; merge adjacent lists
    fragment = re.sub(r"</ul>\s*<ul>", "", fragment)
    fragment = re.sub(r"</ol>\s*<ol>", "", fragment)
    # Markdown-ish text typed into table cells, e.g. **Bold**
    fragment = re.sub(r"\*\*([^*<]+?)\*\*", r"<strong>\1</strong>", fragment)
    return fragment.strip()


def make_image_writer(image_dir):
    out_dir = ROOT / image_dir
    written = []

    def write(src):
        match = re.match(r"data:image/(png|jpe?g|gif);base64,(.*)", src, re.S)
        if not match:
            return src if src.startswith("http") else None
        ext = "jpg" if match.group(1).startswith("jp") else match.group(1)
        data = base64.b64decode(match.group(2))
        # Name by content so an unchanged image keeps its file between syncs
        name = f"{hashlib.sha1(data).hexdigest()[:12]}.{ext}"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / name).write_bytes(data)
        written.append(name)
        return f"{image_dir}/{name}"

    return write, written, out_dir


def render_qmd(doc, blocks):
    synced = datetime.date.today().isoformat()
    doc_url = f"https://docs.google.com/document/d/{doc['id']}/edit"
    lines = [
        "---",
        f'title: "{doc["title"]}"',
        f'description: "{doc["description"]}"',
        f'image: "{doc["image"]}"',
        "format:",
        "  html:",
        "    toc: true",
        "    toc-depth: 2",
        "---",
        "",
        "<!-- Generated by scripts/sync_google_docs.py. Edit the Google Doc, not this file. -->",
        "",
        '::: {.callout-note appearance="simple"}',
        f"This page is copied from the [{doc['title']} Google Doc]({doc_url}) "
        f"every day (last synced {synced}). To change it, edit the doc.",
        ":::",
        "",
    ]
    used_ids = set()
    first_html = True
    for block in blocks:
        if block[0] == "heading":
            _, level, text, anchors = block
            slug = slugify(text)
            while slug in used_ids:
                slug += "-1"
            used_ids.add(slug)
            # Keep the doc's bookmark ids so its internal links still land here
            anchor_html = "".join(f'<a id="{a}"></a>' for a in anchors if not a.startswith("h."))
            lines += [f"{'#' * max(level, 2)} {text} {{#{slug}}}", ""]
            if anchor_html:
                lines += ["```{=html}", anchor_html, "```", ""]
        else:
            fragment = tidy_fragment(block[1])
            if not fragment:
                continue
            if first_html:
                # Drop the doc's own title line; the page title replaces it
                fragment = re.sub(r"^<p>\s*<strong>[^<]*Overview Guide[^<]*</strong>\s*</p>", "", fragment)
                first_html = False
            lines += ["```{=html}", fragment, "```", ""]
    return "\n".join(lines)


def sync(doc, raw_html):
    bold, italic = style_classes(raw_html)
    write_image, written, image_dir = make_image_writer(doc["image_dir"])
    cleaner = DocCleaner(bold, italic, write_image)
    cleaner.feed(preprocess(raw_html))
    cleaner.flush()
    # Images no longer in the doc
    if image_dir.exists():
        for stale in image_dir.iterdir():
            if stale.name not in written:
                stale.unlink()
    headings = sum(1 for b in cleaner.blocks if b[0] == "heading")
    if headings == 0:
        raise SystemExit(f"{doc['id']}: no headings found, refusing to overwrite {doc['output']}")
    (ROOT / doc["output"]).write_text(render_qmd(doc, cleaner.blocks), encoding="utf-8")
    print(f"Wrote {doc['output']}: {headings} sections, {len(written)} images")


def token_from_service_account():
    """Mint a Drive token straight from the GOOGLE_SA_KEY JSON key. This signs
    locally, so it doesn't need the IAM Credentials API that
    google-github-actions/auth uses (it's disabled in the facilitatorsheets
    project)."""
    key_json = os.environ.get("GOOGLE_SA_KEY", "").strip()
    if not key_json:
        return None
    import json
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    credentials = service_account.Credentials.from_service_account_info(
        json.loads(key_json),
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    credentials.refresh(Request())
    return credentials.token


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-file", help="Use a local HTML export instead of the Drive API (first doc only)")
    args = parser.parse_args()

    if args.from_file:
        sync(DOCS[0], Path(args.from_file).read_text(encoding="utf-8"))
        return

    token = os.environ.get("GOOGLE_DRIVE_TOKEN") or token_from_service_account()
    if not token:
        print("No Google credentials; keeping the committed Google Doc snapshots")
        return
    for doc in DOCS:
        try:
            sync(doc, export_html(doc["id"], token))
        except Exception as error:  # one bad doc shouldn't block the deploy
            print(f"::warning::Could not sync {doc['output']}: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
