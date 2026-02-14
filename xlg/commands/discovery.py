"""Discovery source commands."""

import httpx
from collections.abc import Generator


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
    search_url = f"https://collectionapi.metmuseum.org/public/collection/v1/search?q={query}&hasImages=true"
    response = httpx.get(search_url)
    response.raise_for_status()
    object_ids = response.json().get("objectIDs") or []
    for oid in object_ids[:10]:
        obj_response = httpx.get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}")
        obj_response.raise_for_status()
        obj = obj_response.json()
        if obj.get("primaryImage"):
            yield {"title": obj["title"], "url": f"https://www.metmuseum.org/art/collection/search/{oid}", "source": "museum"}
