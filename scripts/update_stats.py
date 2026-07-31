import urllib.request
import re
import json
import os

PYPI_PACKAGES = [
    "hdrezka", "mspm", "notateit", "universalimg",
    "easyproxies", "ebomb", "spys", "fastdub",
    "pycocic", "proxytv", "minipy3", "visualpy",
    "tgphind", "pyfastdub"
]

def parse_badge_value(val):
    val = val.lower().replace(' ', '')
    multiplier = 1
    if val.endswith('k'):
        multiplier = 1000
        val = val[:-1]
    elif val.endswith('m'):
        multiplier = 1000000
        val = val[:-1]
    try:
        return int(float(val) * multiplier)
    except ValueError:
        return 0

def get_pypi_downloads():
    total_downloads = 0
    for pkg in PYPI_PACKAGES:
        url = f"https://static.pepy.tech/badge/{pkg}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                svg = response.read().decode()
                texts = re.findall(r'<text[^>]*>([^<]+)</text>', svg)
                if len(texts) >= 3:
                    downloads_str = texts[2]
                    downloads = parse_badge_value(downloads_str)
                    total_downloads += downloads
        except Exception as e:
            print(f"Error fetching {pkg}: {e}")
    return total_downloads

def get_github_downloads(username):
    url = f"https://api.github.com/users/{username}/repos?per_page=100"
    total_downloads = 0
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers['Authorization'] = f"token {token}"
        
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            repos = json.loads(response.read().decode())
            for repo in repos:
                releases_url = repo['releases_url'].replace('{/id}', '')
                try:
                    r_req = urllib.request.Request(releases_url, headers=headers)
                    with urllib.request.urlopen(r_req) as r_res:
                        releases = json.loads(r_res.read().decode())
                        for release in releases:
                            for asset in release.get('assets', []):
                                total_downloads += asset.get('download_count', 0)
                except Exception:
                    pass
    except Exception as e:
        print(f"Error fetching GitHub repos: {e}")
    return total_downloads

def main():
    pypi_downloads = get_pypi_downloads()
    github_downloads = get_github_downloads("ndenissov")
    
    stats = {
        "pypiDownloads": pypi_downloads,
        "githubDownloads": github_downloads,
        "schemaVersion": 1,
        "label": "PyPI Downloads",
        "message": f"{pypi_downloads:,}",
        "color": "blue",
        
        "github_label": "GitHub Downloads",
        "github_message": f"{github_downloads:,}",
        "github_color": "green"
    }
    
    with open("stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    print("Updated stats.json")

if __name__ == "__main__":
    main()
