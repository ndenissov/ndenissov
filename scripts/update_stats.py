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

from concurrent.futures import ThreadPoolExecutor

def get_github_token():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        try:
            import subprocess
            token = subprocess.check_output(["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            token = None
    return token

def get_repo_downloads(repo, headers):
    releases_url = repo['releases_url'].replace('{/id}', '')
    total = 0
    try:
        r_req = urllib.request.Request(releases_url, headers=headers)
        with urllib.request.urlopen(r_req, timeout=10) as r_res:
            releases = json.loads(r_res.read().decode())
            for release in releases:
                for asset in release.get('assets', []):
                    total += asset.get('download_count', 0)
    except Exception:
        pass
    return total

def get_github_downloads(username, fallback=0):
    token = get_github_token()
    headers = {'User-Agent': 'Mozilla/5.0'}
    if token:
        headers['Authorization'] = f"token {token}"
        
    page = 1
    all_repos = []
    total_downloads = 0
    success = False
    
    try:
        while True:
            url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                repos = json.loads(response.read().decode())
                if not repos:
                    break
                all_repos.extend(repos)
                if len(repos) < 100:
                    break
                page += 1
                
        with ThreadPoolExecutor(max_workers=10) as executor:
            counts = executor.map(lambda r: get_repo_downloads(r, headers), all_repos)
            total_downloads = sum(counts)
            
        success = True
    except Exception as e:
        print(f"Error fetching GitHub repos: {e}")
        
    if not success and fallback > 0:
        print(f"Using fallback GitHub downloads: {fallback}")
        return fallback
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
    existing_stats = {}
    stats_file = os.path.join(ROOT_DIR, "stats.json")
    if os.path.exists(stats_file):
        try:
            with open(stats_file, "r", encoding="utf-8") as f:
                existing_stats = json.load(f)
        except Exception:
            pass

    pypi_downloads = get_pypi_downloads()
    if pypi_downloads == 0 and "pypiDownloads" in existing_stats:
        pypi_downloads = existing_stats["pypiDownloads"]

    github_fallback = existing_stats.get("githubDownloads", 0)
    github_downloads = get_github_downloads(username, fallback=github_fallback)
    if github_downloads == 0 and github_fallback > 0:
        github_downloads = github_fallback

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
    
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print("Updated stats.json")

if __name__ == "__main__":
    main()

