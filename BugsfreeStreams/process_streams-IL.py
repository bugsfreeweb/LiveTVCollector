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

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_server_geolocation():
    try:
        ip_response = requests.get('https://api.ipify.org?format=json', timeout=10)
        server_ip = ip_response.json()['ip']
        geo_response = requests.get(f'https://ipapi.co/{server_ip}/json/', timeout=10)
        geo_data = geo_response.json()
        location_info = {
            'ip': server_ip,
            'country': geo_data.get('country_name', 'Unknown'),
            'country_code': geo_data.get('country_code', 'Unknown'),
            'region': geo_data.get('region', 'Unknown'),
            'city': geo_data.get('city', 'Unknown'),
            'org': geo_data.get('org', 'Unknown'),
            'timezone': geo_data.get('timezone', 'Unknown')
        }
        logging.info(f"SERVER GEOLOCATION: {location_info['city']}, {location_info['region']}, {location_info['country']} ({location_info['country_code']}) | IP: {location_info['ip']} | Org: {location_info['org']} | TZ: {location_info['timezone']}")
        return location_info
    except Exception as e:
        logging.warning(f"Failed to get server geolocation: {e}")
        return None

class M3UCollector:
    def __init__(self, country="Mikhoul", base_dir="LiveTV", check_links=False, excluded_groups=None):
        self.channels = defaultdict(list)
        self.default_logo = "https://buddytv.netlify.app/img/no-logo.png"
        self.seen_urls = set()
        self.output_dir = os.path.join(base_dir, country)
        self.check_links = check_links
        self.excluded_groups = excluded_groups or []
        self.skipped_non_http_count = 0
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_content(self, url):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        try:
            with requests.get(url, stream=True, headers=headers, timeout=10) as response:
                response.raise_for_status()
                lines = [line.decode('utf-8', errors='replace') if isinstance(line, bytes) else line for line in response.iter_lines()]
                return lines
        except requests.RequestException as e:
            logging.warning(f"Failed to fetch {url}: {str(e)}")
            return []

    def test_cuisine_detection(self, lines):
        cuisine_lines = sum(1 for line in lines if 'cuisine' in line.lower())
        zeste_lines = sum(1 for line in lines if 'zeste' in line.lower())
        logging.info(f"CUISINE lines found: {cuisine_lines} | ZESTE lines found: {zeste_lines}")

    def parse_and_store(self, lines, source_url):
        current_channel = {}
        channel_count = 0
        group_occurrences = defaultdict(int)

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            if line.startswith('#EXTINF:'):
                if current_channel:
                    logging.warning(f"Orphaned #EXTINF at line {line_num}. Previous channel data was discarded.")
                
                group = "Uncategorized"
                try:
                    # **CRITICAL FIX: Robust and simple group extraction**
                    match = re.search(r'group-title="([^"]*)"', line)
                    if match:
                        extracted_group = match.group(1).strip()
                        if extracted_group:
                            group = extracted_group
                            if group.lower() == 'cuisine':
                                group = 'Cuisine' # Normalize case
                                logging.info(f"★★★ CUISINE GROUP CONFIRMED at line {line_num}")
                    
                    group_occurrences[group] += 1
                    
                    if any(excl.lower() == group.lower() for excl in self.excluded_groups):
                        current_channel = {}
                        continue

                    logo_match = re.search(r'tvg-logo="([^"]*)"', line)
                    logo = logo_match.group(1) if logo_match and logo_match.group(1) else self.default_logo

                    name_match = re.search(r',(.+)$', line)
                    name = name_match.group(1).strip() if name_match else "Unnamed Channel"

                    current_channel = {
                        'name': name,
                        'logo': logo,
                        'group': group,
                        'source': source_url,
                        'line_num': line_num
                    }

                except Exception as e:
                    logging.error(f"Error parsing #EXTINF at line {line_num}: {e}")
                    current_channel = {}

            elif current_channel and line and not line.startswith('#'):
                # This is the URL line for the previously parsed #EXTINF
                if line.startswith(('http://', 'https://')):
                    if line not in self.seen_urls:
                        self.seen_urls.add(line)
                        current_channel['url'] = line
                        self.channels[current_channel['group']].append(current_channel)
                        channel_count += 1
                        if current_channel['group'].lower() == 'cuisine':
                            logging.info(f"★★★ CUISINE CHANNEL STORED: '{current_channel['name']}' | URL: {line}")
                else:
                    self.skipped_non_http_count += 1
                    if current_channel.get('group', '').lower() == 'cuisine':
                        logging.info(f"★★★ CUISINE CHANNEL REJECTED (non-HTTP): '{current_channel.get('name')}' | URL: {line}")
                
                current_channel = {} # Reset for the next entry

        logging.info("GROUP OCCURRENCES SUMMARY:")
        for group, count in sorted(group_occurrences.items()):
            logging.info(f"  - {group}: {count} channels")
        
        logging.info(f"Parsing complete: {channel_count} channels added from {source_url}")
        logging.info(f"Skipped {self.skipped_non_http_count} non-HTTP/HTTPS URLs.")

    def process_sources(self, source_urls):
        for url in source_urls:
            lines = self.fetch_content(url)
            if lines:
                self.test_cuisine_detection(lines)
                self.parse_and_store(lines, url)

    def export_m3u(self, filename="LiveTV.m3u"):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for group, channels in sorted(self.channels.items()):
                for channel in sorted(channels, key=lambda x: x['name']):
                    f.write(f'#EXTINF:-1 tvg-logo="{channel["logo"]}" group-title="{group}",{channel["name"]}\n')
                    f.write(f'{channel["url"]}\n')
        logging.info(f"Exported M3U to {filepath}")

    # ... (Other export functions: export_txt, export_json, export_custom) ...
    def get_excluded_groups_info(self):
        return {'excluded_count': len(self.excluded_groups)}

def main():
    server_location = get_server_geolocation()
    excluded_groups = [
        "Argentina", "Austria", "Brazil", "Chile", "Denmark", "Germany", "India", "Italy", 
        "Mexico", "Norway", "South Korea", "Spain", "Sweden", "Switzerland", "United Kingdom", 
        "United States", "Offline", "Test", "Demo", "Shopping", "Teleshopping"
    ]
    source_urls = ["https://github.com/Sphinxroot/QC-TV/raw/16afc34391cf7a1dbc0b6a8273476a7d3f9ca33b/Quebec.m3u"]
    
    collector = M3UCollector(country="Mikhoul", excluded_groups=excluded_groups)
    
    excluded_info = collector.get_excluded_groups_info()
    logging.info(f"Groupes exclus: {excluded_info['excluded_count']} | {', '.join(excluded_groups)}")
    
    collector.process_sources(source_urls)
    
    total_channels = sum(len(ch) for ch in collector.channels.values())
    logging.info(f"PHASE 1 COMPLETE: {total_channels} channels parsed, groups: {', '.join(sorted(collector.channels.keys()))}")
    
    cuisine_channels_count = len(collector.channels.get('Cuisine', []))
    logging.info(f"CUISINE channels after parsing: {cuisine_channels_count}")

    collector.export_m3u()
    # collector.export_txt()
    # collector.export_json()
    # collector.export_custom()
    
    logging.info(f"Collected {total_channels} unique channels for Mikhoul")

if __name__ == "__main__":
    main()

