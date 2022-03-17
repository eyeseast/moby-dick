#!/usr/bin/env python
import itertools
import pathlib
import re

import frontmatter
import httpx
from bs4 import BeautifulSoup

URL = "https://www.gutenberg.org/files/2701/2701-h/2701-h.htm"

CHAPTERS = pathlib.Path(__file__).parent / "chapters"
README = pathlib.Path(__file__).parent / "README.md"

WHITESPACE = re.compile(r"\s+")

CONTENT_TAGS = ["p", "table", "pre"]


def main():
    html = httpx.get(URL).content
    soup = BeautifulSoup(html, "lxml")

    if not CHAPTERS.exists():
        CHAPTERS.mkdir()

    toc = soup.find("blockquote")
    headings = toc.select("p.toc")

    for i, heading in enumerate(headings):
        link = heading.find("a")
        if link:
            href = link["href"]
            marker = soup.select_one(href)
            if marker:
                extract_chapter(marker, i, soup)


def extract_chapter(marker, index, soup):
    if marker.parent.name == "p":
        marker = marker.parent

    # the chapter starts after the marker
    heading = next(filter(lambda tag: tag.name == "h2", marker.next_siblings), None)
    if not heading:
        return

    # metadata
    metadata = {}
    title = metadata["title"] = heading.string.strip()
    name = title.split(".", 1)[0].strip()
    subhead = next(
        filter(
            lambda tag: tag.name == "h3", itertools.islice(heading.next_siblings, 5)
        ),
        None,
    )

    if subhead:
        metadata["subhead"] = subhead.string.strip()

    # content
    paragraphs = itertools.takewhile(
        lambda tag: tag.name != "h2", heading.next_siblings
    )

    content = [strings(tag) for tag in paragraphs if tag.name in CONTENT_TAGS]
    content = [collapse_whitespace(p) for p in content]
    text = "\n\n".join(p for p in content if p.strip())
    # text = textwrap.dedent(text)

    # save it in a frontmatter file
    path = CHAPTERS / f"{index:03}_{slugify(name)}.md"
    post = frontmatter.Post(text, **metadata)
    frontmatter.dump(post, path, sort_keys=False)


def strings(tag):
    if tag.name in ["table", "pre"]:
        return tag.prettify()

    return "".join(map(collapse_whitespace, tag.stripped_strings))


def collapse_whitespace(text):
    text = WHITESPACE.sub(" ", text)
    text = text.replace("\n", "")
    return text.strip()


def slugify(s):
    return collapse_whitespace(s).lower().replace(" ", "-")


if __name__ == "__main__":
    main()