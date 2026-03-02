import requests
import json
import os
import re
from urllib.parse import urlparse
from collections import defaultdict
from datetime import datetime
import pytz
import concurrent.futures
import threading
import logging
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class M3UCollector:
    def __init__(self, country="Bollywood", base_dir="Movies"):
        self.channels = defaultdict(list)
        self.default_logo = "https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/BugsfreeLogo/default-logo.png"
        self.seen_urls = set()
        self.output_dir = os.path.join(base_dir, country)
        self.lock = threading.Lock()
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_content(self, url):
        """Fetch content (M3U or HTML) with streaming."""
        try:
            with requests.get(url, stream=True, timeout=10) as response:
                response.raise_for_status()
                content = response.text  # For HTML parsing
                lines = list(response.iter_lines(decode_unicode=True))  # For M3U parsing
                logging.info(f"Fetched {len(lines)} lines from {url}")
                return content, lines
        except requests.RequestException as e:
            logging.error(f"Error fetching {url}: {e}")
            return None, []

    def extract_stream_urls_from_html(self, html_content, base_url):
        """Extract streaming URLs from HTML, filtering out non-stream links."""
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        stream_urls = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            parsed_base = urlparse(base_url)
            parsed_href = urlparse(href)
            if not parsed_href.scheme:
                href = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
            
            if (href.endswith(('.m3u', '.m3u8')) or 
                re.match(r'^https?://.*\.(ts|mp4|avi|mkv|flv|wmv)$', href) or 
                'playlist' in href.lower() or 'stream' in href.lower()):
                if not any(exclude in href.lower() for exclude in ['telegram', '.html', '.php', 'github.com', 'login', 'signup']):
                    stream_urls.add(href)
        
        logging.info(f"Extracted {len(stream_urls)} streaming URLs from {base_url}")
        return list(stream_urls)

    def check_link_active(self, url, timeout=5):
        """Quickly check if a link is active with a short timeout."""
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            is_active = response.status_code < 400
            logging.info(f"Checked {url}: {'Active' if is_active else 'Inactive'} (HEAD)")
            return is_active
        except requests.RequestException:
            try:
                with requests.get(url, stream=True, timeout=timeout) as r:
                    is_active = r.status_code < 400
                    logging.info(f"Checked {url}: {'Active' if is_active else 'Inactive'} (GET)")
                    return is_active
            except requests.RequestException as e:
                logging.warning(f"Link check failed for {url}: {e}")
                return False

    def parse_and_store(self, lines, source_url):
        """Parse M3U lines and store channels; duplicates checked via seen_urls."""
        current_channel = {}
        channel_count = 0
        for line in lines:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                match = re.search(r'tvg-logo="([^"]*)"', line)
                logo = match.group(1) if match and match.group(1) else self.default_logo
                
                match = re.search(r'group-title="([^"]*)"', line)
                group = match.group(1) if match else "Uncategorized"
                
                match = re.search(r',(.+)$', line)
                name = match.group(1).strip() if match else "Unnamed Channel"
                
                current_channel = {
                    'name': name,
                    'logo': logo,
                    'group': group,
                    'source': source_url
                }
            elif line.startswith('http') and current_channel:
                with self.lock:
                    if line not in self.seen_urls:
                        self.seen_urls.add(line)
                        current_channel['url'] = line
                        self.channels[current_channel['group']].append(current_channel)
                        channel_count += 1
                current_channel = {}
        logging.info(f"Parsed {channel_count} channels from {source_url}")

    def filter_active_channels(self):
        """Filter out inactive channels and ensure no duplicates."""
        active_channels = defaultdict(list)
        all_channels = [(group, ch) for group, chans in self.channels.items() for ch in chans]
        url_set = set()
        
        logging.info(f"Total channels to check: {len(all_channels)}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            future_to_channel = {
                executor.submit(self.check_link_active, ch['url']): (group, ch)
                for group, ch in all_channels if ch['url'] not in url_set and not url_set.add(ch['url'])
            }
            for future in concurrent.futures.as_completed(future_to_channel):
                group, channel = future_to_channel[future]
                try:
                    if future.result():
                        active_channels[group].append(channel)
                except Exception as e:
                    logging.error(f"Error checking {channel['url']}: {e}")

        self.channels = active_channels
        logging.info(f"Active channels after filtering: {sum(len(ch) for ch in active_channels.values())}")

    def process_sources(self, source_urls):
        """Process all sources, including HTML, remove duplicates, and filter active links."""
        self.channels.clear()
        self.seen_urls.clear()
        
        all_m3u_urls = set()
        for url in source_urls:
            html_content, lines = self.fetch_content(url)
            if url.endswith('.html'):
                m3u_urls = self.extract_stream_urls_from_html(html_content, url)
                all_m3u_urls.update(m3u_urls)
            else:
                self.parse_and_store(lines, url)
        
        for m3u_url in all_m3u_urls:
            _, lines = self.fetch_content(m3u_url)
            self.parse_and_store(lines, m3u_url)
        
        if self.channels:
            self.filter_active_channels()
        else:
            logging.warning("No channels parsed from sources")

    def export_m3u(self, filename="Movies.m3u"):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for group, channels in self.channels.items():
                for channel in channels:
                    f.write(f'#EXTINF:-1 tvg-logo="{channel["logo"]}" group-title="{group}",{channel["name"]}\n')
                    f.write(f'{channel["url"]}\n')
        logging.info(f"Exported M3U to {filepath}")
        return filepath

    def export_txt(self, filename="Movies.txt"):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            for group, channels in sorted(self.channels.items()):
                f.write(f"Group: {group}\n")
                for channel in channels:
                    f.write(f"Name: {channel['name']}\n")
                    f.write(f"URL: {channel['url']}\n")
                    f.write(f"Logo: {channel['logo']}\n")
                    f.write(f"Source: {channel['source']}\n")
                    f.write("-" * 50 + "\n")
                f.write("\n")
        logging.info(f"Exported TXT to {filepath}")
        return filepath

    def export_json(self, filename="Movies.json"):
        filepath = os.path.join(self.output_dir, filename)
        mumbai_tz = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(mumbai_tz).strftime('%Y-%m-%d %H:%M:%S')
        
        json_data = {
            "date": current_time,
            "channels": dict(self.channels)
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        logging.info(f"Exported JSON to {filepath}")
        return filepath

    def export_custom(self, filename="Movies"):
        """Export to custom format without extension."""
        filepath = os.path.join(self.output_dir, filename)
        custom_data = []
        
        for group, channels in self.channels.items():
            for channel in channels:
                custom_data.append({
                    "name": channel['name'],
                    "type": group,  # Using group as type
                    "url": channel['url'],
                    "img": channel['logo']
                })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(custom_data, f, ensure_ascii=False, indent=2)
        logging.info(f"Exported custom format to {filepath}")
        return filepath

def main():
    # Specific M3U sources
    source_urls = [
        "https://raw.githubusercontent.com/Mahabubulalammim/New/refs/heads/main/Mim%20New%20Movie%20Collection",
        "https://raw.githubusercontent.com/Mahabubulalammim/New/refs/heads/main/Mim-Movies.mim",        
    ]

    collector = M3UCollector(country="Bollywood")
    collector.process_sources(source_urls)
    
    # Export files
    collector.export_m3u("Movies.m3u")
    collector.export_txt("Movies.txt")
    collector.export_json("Movies.json")
    collector.export_custom("Movies")
    
    total_channels = sum(len(ch) for ch in collector.channels.values())
    mumbai_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    logging.info(f"[{mumbai_time}] Collected {total_channels} active, unique channels for Bollywood")
    logging.info(f"Groups found: {len(collector.channels)}")

if __name__ == "__main__":
    main()
