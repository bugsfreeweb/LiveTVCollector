import requests
import json
import os
import re
from collections import defaultdict
from datetime import datetime
import pytz
import logging

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
    def __init__(self, country="Mikhoul", base_dir="LiveTV", excluded_groups=None):
        self.country = country
        self.base_dir = base_dir
        self.excluded_groups = [group.lower() for group in (excluded_groups or [])]
        self.output_dir = os.path.join(self.base_dir, self.country)
        self.channels = defaultdict(list)
        self.seen_urls = set()
        self.default_logo = "https://buddytv.netlify.app/img/no-logo.png"
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
        total_extinf_lines = 0
        group_occurrences = defaultdict(int)
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Debug logging for critical lines
            if line_num in (537, 539, 541) and "group-title" in line:
                logging.info(f"RAW GROUP DETECTED Line {line_num}: '{line}'")
            
            if line_num % 100 == 0 or line_num in (1, 537, 538, 539, 540, 541, 542):
                logging.info(f"Parsing line {line_num}/{len(lines)}: {line[:60]}")
            
            # **CRITICAL FIX: Check for both '#EXTINF:' and 'EXTINF:' (missing #)**
            if line.startswith('#EXTINF:') or line.startswith('EXTINF:'):
                total_extinf_lines += 1
                
                # Extract logo
                try:
                    match = re.search(r'tvg-logo="([^"]*)"', line)
                    logo = match.group(1) if match and match.group(1) else self.default_logo
                except Exception:
                    logo = self.default_logo
                
                # Direct group extraction
                group = "Uncategorized"
                try:
                    match = re.search(r'group-title="([^"]*)"', line)
                    if match:
                        extracted_group = match.group(1).strip()
                        if extracted_group and not extracted_group.isspace():
                            group = extracted_group
                            # Enhanced logging for lines 537, 539, 541
                            if line_num in (537, 539, 541):
                                logging.info(f"★★★ LINE {line_num} EXTRACTED GROUP: '{group}'")
                            
                            # Normalize case for Cuisine
                            if group.lower() == 'cuisine':
                                group = 'Cuisine'
                                logging.info(f"★★★ CUISINE GROUP CONFIRMED: '{group}' at line {line_num}")
                except Exception as e:
                    logging.error(f"Line {line_num}: GROUP EXTRACTION ERROR: {e}")
                    group = "Uncategorized"
                
                group_occurrences[group] += 1
                
                # Check if group is excluded
                excluded = any(
                    group.lower() == excl.lower() for excl in self.excluded_groups
                )
                if excluded:
                    current_channel = {}
                    continue
                
                # Extract channel name
                try:
                    match = re.search(r',(.+)$', line)
                    name = match.group(1).strip() if match else "Unnamed Channel"
                except Exception:
                    name = "Unnamed Channel"
                
                current_channel = {
                    'name': name,
                    'logo': logo,
                    'group': group,
                    'source': source_url,
                    'line_num': line_num
                }
                
            elif line and not line.startswith('#') and current_channel:
                if line.startswith(('http://', 'https://')):
                    if line not in self.seen_urls:
                        self.seen_urls.add(line)
                        current_channel['url'] = line
                        self.channels[current_channel['group']].append(current_channel)
                        channel_count += 1
                        
                        # Special logging for Cuisine channels
                        if current_channel['group'].lower() == 'cuisine':
                            logging.info(f"★★★ CUISINE CHANNEL STORED: '{current_channel['name']}' in group '{current_channel['group']}' | URL: {line}")
                else:
                    self.skipped_non_http_count += 1
                    if current_channel.get('group', '').lower() == 'cuisine':
                        logging.info(f"★★★ CUISINE CHANNEL REJECTED (non-HTTP): '{current_channel.get('name', 'Unknown')}' | URL: {line}")
                
                current_channel = {}
        
        # Summary logging
        logging.info(f"GROUP OCCURRENCES SUMMARY:")
        for group, count in group_occurrences.items():
            logging.info(f"  - {group}: {count} channels")
        
        logging.info(f"Parsing complete: {channel_count} channels added from {source_url}")
        logging.info(f"Skipped non-HTTP/HTTPS URLs: {self.skipped_non_http_count}")

    def process_sources(self, source_urls):
        self.channels.clear()
        self.seen_urls.clear()
        
        for url in source_urls:
            lines = self.fetch_content(url)
            if lines:
                self.test_cuisine_detection(lines)
                self.parse_and_store(lines, url)
        
        total_parsed = sum(len(ch) for ch in self.channels.values())
        logging.info(f"PHASE 1 COMPLETE: {total_parsed} channels parsed, groups: {', '.join(sorted(self.channels.keys()))}")
        
        # Special check for Cuisine channels
        cuisine_channels = [ch for ch_list in self.channels.values() for ch in ch_list if ch['group'].lower() == 'cuisine']
        logging.info(f"CUISINE channels after parsing: {len(cuisine_channels)}")
        
        if cuisine_channels:
            logging.info(f"★★★ CUISINE CHANNELS FOUND:")
            for ch in cuisine_channels:
                logging.info(f"★★★   - {ch['name']} -> {ch['url']}")

    def get_excluded_groups_info(self):
        return {
            'excluded_groups': self.excluded_groups,
            'excluded_count': len(self.excluded_groups)
        }

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
            "channels": dict(self.channels),
            "excluded_groups": list(self.excluded_groups)
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        logging.info(f"Exported JSON to {filepath}")
        return filepath

    def export_custom(self, filename="LiveTV"):
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
    server_location = get_server_geolocation()
    excluded_groups = [
        "Argentina", "Austria", "Brazil", "Chile", "Denmark", "Germany", 
        "India", "Italy", "Mexico", "Norway", "South Korea", "Spain", 
        "Sweden", "Switzerland", "United Kingdom", "United States",
        "Offline", "Test", "Demo", "Shopping", "Teleshopping"
    ]
    
    source_urls = [
        "https://github.com/Sphinxroot/QC-TV/raw/16afc34391cf7a1dbc0b6a8273476a7d3f9ca33b/Quebec.m3u",
    ]
    
    collector = M3UCollector(
        country="Mikhoul", 
        excluded_groups=excluded_groups
    )
    
    excluded_info = collector.get_excluded_groups_info()
    logging.info(f"Groupes exclus: {excluded_info['excluded_count']} | {', '.join(excluded_groups)}")
    
    collector.process_sources(source_urls)
    collector.export_m3u("LiveTV.m3u")
    collector.export_txt("LiveTV.txt")
    collector.export_json("LiveTV.json")
    collector.export_custom("LiveTV")
    
    total_channels = sum(len(ch) for ch in collector.channels.values())
    mumbai_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    logging.info(f"[{mumbai_time}] Collected {total_channels} unique channels for Mikhoul")
    logging.info(f"Groups found: {len(collector.channels)}")
    final_groups = list(collector.channels.keys())
    logging.info(f"Final groups after exclusion: {', '.join(sorted(final_groups))}")
    
    if server_location:
        logging.info(f"All tests performed from: {server_location['country']} ({server_location['country_code']})")

if __name__ == "__main__":
    main()
