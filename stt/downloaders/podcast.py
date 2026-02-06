import os
import requests

from stt.utils import ensure_dir, read_json, write_json, safe_filename


def load_feeds_config(path):
    try:
        import yaml
    except ImportError:
        print("PyYAML not installed. Install with 'pip install pyyaml' to use feeds.")
        return []
    if not os.path.exists(path):
        print(f"Feeds config not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("feeds", [])


def fetch_feed_entries(url):
    try:
        import feedparser
    except ImportError:
        print("feedparser not installed. Install with 'pip install feedparser'.")
        return []
    feed = feedparser.parse(url)
    return feed.entries


def download_enclosure(entry, target_dir):
    enclosures = entry.get("enclosures", [])
    if not enclosures:
        return None
    enclosure_url = enclosures[0].get("href")
    if not enclosure_url:
        return None

    title = entry.get("title", "episode")
    safe_title = safe_filename(title)
    filename = f"{safe_title}.mp3"
    path = os.path.join(target_dir, filename)
    if os.path.exists(path):
        return path

    resp = requests.get(enclosure_url, stream=True, timeout=60)
    resp.raise_for_status()
    with open(path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
    return path


def process_feeds(feeds_path, output_dir):
    feeds = load_feeds_config(feeds_path)
    if not feeds:
        return []

    ensure_dir(output_dir)
    state_path = os.path.join(output_dir, "feeds_state.json")
    state = read_json(state_path, default={})
    new_files = []

    for feed in feeds:
        name = feed.get("name", "feed")
        url = feed.get("url")
        if not url:
            continue

        entries = fetch_feed_entries(url)
        seen_ids = set(state.get(name, []))
        for entry in entries:
            entry_id = entry.get("id") or entry.get("link")
            if entry_id in seen_ids:
                continue
            file_path = download_enclosure(entry, output_dir)
            if file_path:
                new_files.append(file_path)
            if entry_id:
                seen_ids.add(entry_id)

        state[name] = list(seen_ids)

    write_json(state_path, state)
    return new_files
