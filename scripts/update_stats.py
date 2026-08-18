import urllib.request
import re
import json
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
            with urllib.request.urlopen(req, timeout=10) as response:
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
        with urllib.request.urlopen(req, timeout=10) as response:
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

def update_github_stats_svg(username):
    urls = [
        f"https://github-readme-stats-fast.vercel.app/api?username={username}&show_icons=true&theme=tokyonight&hide_border=true&include_all_commits=true&count_private=true",
        f"https://github-stats-extended.vercel.app/api?username={username}&show_icons=true&theme=tokyonight&hide_border=true&include_all_commits=true&count_private=true",
    ]
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                svg_data = response.read().decode('utf-8')
                if "Something went wrong" not in svg_data and "Maximum retries exceeded" not in svg_data and len(svg_data) > 500:
                    with open(os.path.join(ROOT_DIR, "github-stats.svg"), "w", encoding="utf-8") as f:
                        f.write(svg_data)
                    print("Updated github-stats.svg")
                    return
        except Exception as e:
            print(f"Error fetching github stats from {url}: {e}")
    print("Failed to update github-stats.svg")

def update_top_langs_svg(username):
    urls = [
        f"https://github-readme-stats-fast.vercel.app/api/top-langs/?username={username}&theme=tokyonight&hide_border=true&layout=compact",
        f"https://github-stats-extended.vercel.app/api/top-langs/?username={username}&theme=tokyonight&hide_border=true&layout=compact",
    ]
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                svg_data = response.read().decode('utf-8')
                if "Something went wrong" not in svg_data and "Maximum retries exceeded" not in svg_data and len(svg_data) > 500:
                    with open(os.path.join(ROOT_DIR, "top-langs.svg"), "w", encoding="utf-8") as f:
                        f.write(svg_data)
                    print("Updated top-langs.svg")
                    return
        except Exception as e:
            print(f"Error fetching top languages from {url}: {e}")
    print("Failed to update top-langs.svg")

def update_streak_stats_svg():
    url = "https://streak-stats.vercel.app/?user=ndenissov&theme=tokyonight&hide_border=true"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            svg_data = response.read().decode('utf-8')
            if "Failed to retrieve contributions" not in svg_data and len(svg_data) > 500:
                with open(os.path.join(ROOT_DIR, "streak-stats.svg"), "w", encoding="utf-8") as f:
                    f.write(svg_data)
                print("Updated streak-stats.svg")
            else:
                print("Failed to retrieve streak stats SVG from Vercel")
    except Exception as e:
        print(f"Error fetching streak stats SVG: {e}")

def main():
    username = "ndenissov"
    pypi_downloads = get_pypi_downloads()
    github_downloads = get_github_downloads(username)
    update_streak_stats_svg()
    update_github_stats_svg(username)
    update_top_langs_svg(username)
    
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
    
    with open(os.path.join(ROOT_DIR, "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)
    print("Updated stats.json")

if __name__ == "__main__":
    main()

