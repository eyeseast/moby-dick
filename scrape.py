#!/usr/bin/env python
import itertools
import pathlib
import re
import textwrap

import frontmatter
import httpx
from bs4 import BeautifulSoup

URL = "https://www.gutenberg.org/files/2701/2701-h/2701-h.htm"

CHAPTERS = pathlib.Path(__file__).parent / "chapters"
README = pathlib.Path(__file__).parent / "README.md"

WHITESPACE = re.compile(r"\s+")


def main():
    html = httpx.get(URL).content
    soup = BeautifulSoup(html, "lxml")

    if not CHAPTERS.exists():
        CHAPTERS.mkdir()

    toc = soup.find("blockquote")
    headings = toc.select("p.toc")

    for heading in headings:
        link = heading.find("a")
        if link:
            href = link["href"]
            marker = soup.select_one(href)
            if marker:
                extract_chapter(marker, soup)


def extract_chapter(marker, soup):
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

    content = [tag.string for tag in paragraphs if tag.name == "p" and tag.string]
    content = [collapse_whitespace(p) for p in content]
    text = "\n\n".join(p for p in content if p.strip())
    text = textwrap.dedent(text)

    # save it in a frontmatter file
    path = CHAPTERS / f"{slugify(name)}.md"
    post = frontmatter.Post(text, **metadata)
    frontmatter.dump(post, path)


def collapse_whitespace(text):
    text = WHITESPACE.sub(" ", text)
    text = text.replace("\n", "")
    return text.strip()


def slugify(s):
    return s.strip().lower().replace(" ", "-")


if __name__ == "__main__":
    main()