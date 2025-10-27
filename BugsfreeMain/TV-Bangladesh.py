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
    def __init__(self, country="Bangladesh", base_dir="LiveTV", check_links=True):
        self.channels = defaultdict(list)
        self.default_logo = "https://buddytv.netlify.app/img/no-logo.png"
        self.seen_urls = set()
        self.url_status_cache = {}
        self.output_dir = os.path.join(base_dir, country)
        self.lock = threading.Lock()
        self.check_links = check_links  # Toggle link checking
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_content(self, url):
        """Fetch content (M3U or HTML) with streaming."""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        try:
            with requests.get(url, stream=True, headers=headers, timeout=10) as response:
                response.raise_for_status()
                lines = [line.decode('utf-8', errors='ignore') if isinstance(line, bytes) else line for line in response.iter_lines()]
                content = '\n'.join(lines)
                if not lines:
                    logging.warning(f"No content fetched from {url}")
                else:
                    logging.info(f"Fetched {len(lines)} lines from {url}")
                return content, lines
        except requests.RequestException as e:
            logging.error(f"Failed to fetch {url}: {str(e)}")
            return None, []

    def extract_stream_urls_from_html(self, html_content, base_url):
        """Extract streaming URLs from HTML."""
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

    def check_link_active(self, url, timeout=2):
        """Check if a link is active, optimized for speed."""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        with self.lock:
            if url in self.url_status_cache:
                return self.url_status_cache[url]
        
        # Try original URL
        try:
            response = requests.head(url, timeout=timeout, headers=headers, allow_redirects=True)
            if response.status_code < 400:
                logging.info(f"Checked {url}: Active (HEAD)")
                with self.lock:
                    self.url_status_cache[url] = (True, url)
                return True, url
        except requests.RequestException:
            # Only try GET if HEAD fails, skip alternate protocol for speed
            try:
                with requests.get(url, stream=True, timeout=timeout, headers=headers) as r:
                    if r.status_code < 400:
                        logging.info(f"Checked {url}: Active (GET)")
                        with self.lock:
                            self.url_status_cache[url] = (True, url)
                        return True, url
            except requests.RequestException as e:
                logging.warning(f"Link check failed for {url}: {e}")
                # Try alternate protocol only if not a timeout
                if not isinstance(e, requests.Timeout):
                    alt_url = url.replace('http://', 'https://') if url.startswith('http://') else url.replace('https://', 'http://')
                    try:
                        response = requests.head(alt_url, timeout=timeout, headers=headers, allow_redirects=True)
                        if response.status_code < 400:
                            logging.info(f"Checked {alt_url}: Active (HEAD, switched protocol)")
                            with self.lock:
                                self.url_status_cache[url] = (True, alt_url)
                            return True, alt_url
                    except requests.RequestException:
                        pass
                with self.lock:
                    self.url_status_cache[url] = (False, url)
                return False, url

    def parse_and_store(self, lines, source_url):
        """Parse M3U lines and store channels."""
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
        """Filter out inactive channels, skippable for speed."""
        if not self.check_links:
            logging.info("Skipping link activity check for speed")
            return
        
        active_channels = defaultdict(list)
        all_channels = [(group, ch) for group, chans in self.channels.items() for ch in chans]
        url_set = set()
        
        logging.info(f"Total channels to check: {len(all_channels)}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:  # Even fewer workers
            future_to_channel = {
                executor.submit(self.check_link_active, ch['url']): (group, ch)
                for group, ch in all_channels if ch['url'] not in url_set and not url_set.add(ch['url'])
            }
            for future in concurrent.futures.as_completed(future_to_channel):
                group, channel = future_to_channel[future]
                try:
                    is_active, updated_url = future.result()
                    if is_active:
                        channel['url'] = updated_url
                        active_channels[group].append(channel)
                except Exception as e:
                    logging.error(f"Error checking {channel['url']}: {e}")

        self.channels = active_channels
        logging.info(f"Active channels after filtering: {sum(len(ch) for ch in active_channels.values())}")

    def process_sources(self, source_urls):
        """Process sources sequentially for better control."""
        self.channels.clear()
        self.seen_urls.clear()
        self.url_status_cache.clear()
        
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

    def export_m3u(self, filename="LiveTV.m3u"):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for group, channels in self.channels.items():
                for channel in channels:
                    f.write(f'#EXTINF:-1 tvg-logo="{channel["logo"]}" group-title="{group}",{channel["name"]}\n')
                    f.write(f'{channel["url"]}\n')
        logging.info(f"Exported M3U to {filepath}")
        return filepath

    def export_txt(self, filename="LiveTV.txt"):
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

    def export_json(self, filename="LiveTV.json"):
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

    def export_custom(self, filename="LiveTV"):
        """Export to custom format without extension."""
        filepath = os.path.join(self.output_dir, filename)
        custom_data = []
        
        for group, channels in self.channels.items():
            for channel in channels:
                custom_data.append({
                    "name": channel['name'],
                    "type": group,
                    "url": channel['url'],
                    "img": channel['logo']
                })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(custom_data, f, ensure_ascii=False, indent=2)
        logging.info(f"Exported custom format to {filepath}")
        return filepath

def main():
    # Specific M3U sources (12 sources)
    source_urls = [
        "https://raw.githubusercontent.com/sydul104/main04/refs/heads/main/my",
        "https://raw.githubusercontent.com/abusaeeidx/Mrgify-Tv/refs/heads/main/playlist.m3u",
        "https://raw.githubusercontent.com/time2shine/IPTV/refs/heads/master/combined.m3u",
        "https://raw.githubusercontent.com/mhmimxl/filoox-bdix-selected/main/playlist.m3u",
        "https://raw.githubusercontent.com/Miraz6755/Bdixtv/refs/heads/main/Livetv.m3u8",
        "https://raw.githubusercontent.com/Yeadee/Toffee/refs/heads/main/toffee_ns_player.m3u",
        "https://raw.githubusercontent.com/MohammadJoyChy/BDIXTV/refs/heads/main/Aynaott",
        "https://raw.githubusercontent.com/skjahangirkabir/Bdix-549.m3u/refs/heads/main/BDIX-549.m3u8",
        "https://raw.githubusercontent.com/Arunjunan20/My-IPTV/refs/heads/main/index.html",
        "https://raw.githubusercontent.com/AHIL44444/GAZI-LIVE-TV-M3U8/refs/heads/main/index.html",
        "https://aynaxpranto.vercel.app/files/playlist.m3u",
        "https://raw.githubusercontent.com/tanvir907/bdix/refs/heads/main/bdix.m3u",
        "https://raw.githubusercontent.com/shuvo880/iptv/refs/heads/master/MiME%20(SHUVO)",
        "https://raw.githubusercontent.com/Shaharum1010/SmartFlix_Tv_Web/refs/heads/main/SmartFlixtv",
        "https://raw.githubusercontent.com/mr-masudrana/LiveTV/refs/heads/main/Bangla_Playlist.m3u",
        "https://raw.githubusercontent.com/mr-masudrana/Web_Player-IPTV/refs/heads/main/channels.json",
        "https://iptv-org.github.io/iptv/countries/bd.m3u",
    ]

    # Set check_links=False for super speed, True for accuracy
    collector = M3UCollector(country="Bangladesh", check_links=False)
    collector.process_sources(source_urls)
    
    # Export files
    collector.export_m3u("LiveTV.m3u")
    collector.export_txt("LiveTV.txt")
    collector.export_json("LiveTV.json")
    collector.export_custom("LiveTV")
    
    total_channels = sum(len(ch) for ch in collector.channels.values())
    mumbai_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    logging.info(f"[{mumbai_time}] Collected {total_channels} unique channels for Bangladesh")
    logging.info(f"Groups found: {len(collector.channels)}")

if __name__ == "__main__":
    main()
