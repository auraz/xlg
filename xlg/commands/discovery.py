"""Discovery source commands."""

import httpx
from collections.abc import Generator
from urllib.parse import quote


def cmd_reddit(subreddit: str, query: str = "") -> Generator[dict, None, None]:
    """Fetch posts from Reddit."""
    sub = subreddit.lstrip("r/")
    url = f"https://www.reddit.com/r/{sub}/search.json?q={query}&restrict_sr=1&limit=10" if query else f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
    response = httpx.get(url, headers={"User-Agent": "xlg/0.1"})
    response.raise_for_status()
    for child in response.json()["data"]["children"]:
        post = child["data"]
        yield {"title": post["title"], "url": f"https://reddit.com{post['permalink']}", "source": "reddit"}


def cmd_hn(query: str) -> Generator[dict, None, None]:
    """Fetch posts from Hacker News via Algolia API."""
    url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&hitsPerPage=10"
    response = httpx.get(url)
    response.raise_for_status()
    for hit in response.json()["hits"]:
        item_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
        yield {"title": hit["title"], "url": item_url, "source": "hn"}


def cmd_museum(museum: str, query: str) -> Generator[dict, None, None]:
    """Fetch artworks from museum API."""
    if museum != "met":
        raise ValueError(f"museum: unsupported museum '{museum}', use 'met'")
    headers = {"User-Agent": "xlg/0.1"}
    search_url = f"https://collectionapi.metmuseum.org/public/collection/v1/search?q={query}&hasImages=true"
    response = httpx.get(search_url, headers=headers)
    response.raise_for_status()
    object_ids = response.json().get("objectIDs") or []
    for oid in object_ids[:10]:
        obj_response = httpx.get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}", headers=headers)
        obj_response.raise_for_status()
        obj = obj_response.json()
        if obj.get("primaryImage"):
            yield {"title": obj["title"], "url": f"https://www.metmuseum.org/art/collection/search/{oid}", "source": "museum"}


def cmd_github(query: str) -> Generator[dict, None, None]:
    """Fetch repositories from GitHub."""
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=10"
    response = httpx.get(url, headers={"User-Agent": "xlg/0.1"})
    response.raise_for_status()
    for repo in response.json()["items"]:
        yield {"title": f"{repo['full_name']}: {repo['description'] or ''}", "url": repo["html_url"], "source": "github"}


def cmd_wiki(query: str = "") -> Generator[dict, None, None]:
    """Fetch articles from Wikipedia."""
    headers = {"User-Agent": "xlg/0.1 (https://github.com/auraz/xlg)"}
    if query:
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote(query)}&format=json&srlimit=10"
        response = httpx.get(url, headers=headers, follow_redirects=True)
        response.raise_for_status()
        for item in response.json()["query"]["search"]:
            yield {"title": item["title"], "url": f"https://en.wikipedia.org/wiki/{item['title'].replace(' ', '_')}", "source": "wikipedia"}
    else:
        for _ in range(5):
            response = httpx.get("https://en.wikipedia.org/api/rest_v1/page/random/summary", headers=headers, follow_redirects=True)
            response.raise_for_status()
            data = response.json()
            yield {"title": data["title"], "url": data["content_urls"]["desktop"]["page"], "source": "wikipedia"}
