# LiveTVCollector

A GitHub repository that automatically collects, filters, and exports live TV streaming links for Country/Category wise using GitHub Actions. This project fetches M3U playlists from multiple sources, removes duplicates, verifies active links, and exports them into various formats under the `LiveTV/Country Name/` directory.
# 📊 Project Stats
[![GitHub forks](https://img.shields.io/github/forks/bugsfreeweb/LiveTVCollector?logo=forks&style=plastic)](https://github.com/bugsfreeweb/LiveTVCollector/network) [![GitHub stars](https://img.shields.io/github/stars/bugsfreeweb/LiveTVCollector)](https://github.com/bugsfreeweb/LiveTVCollector/stargazers) [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)  [![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)
![GitHub issues](https://img.shields.io/github/issues/bugsfreeweb/LiveTVCollector)
![GitHub pull requests](https://img.shields.io/github/issues-pr/bugsfreeweb/LiveTVCollector)

## Online Useable Tools:
<a href="https://gmtv.netlify.app" target="_blank"><img src="https://gmtv.netlify.app/img/gmtv.png" style="width:auto; height:60px" alt="GM TV Player"></a>
<a href="https://lolstream.netlify.app" target="_blank"><img src="https://lolstream.netlify.app/img/logo.png" style="width:auto; height:60px" alt="Stream Player"></a>
<a href="https://pismarttv.netlify.app" target="_blank"><img src="https://pismarttv.netlify.app/img/logo.png" style="width:auto; height:60px" alt="IPTV Player"></a>
<a href="https://hodliptv.netlify.app" target="_blank"><img src="https://hodliptv.netlify.app/img/logo.png" style="width:auto; height:60px" alt="IPTV Player"></a>
<a href="https://pixstream.netlify.app" target="_blank"><img src="https://pixstream.netlify.app/img/logo.png" style="width:auto; height:60px" alt="IPTV Player"></a>
<a href="https://buddytv.netlify.app" target="_blank"><img src="https://buddytv.netlify.app/img/logo.png" style="width:auto; height:60px" alt="BuddyTv"></a>
<a href="https://m3uchecker.netlify.app" target="_blank"><img src="https://m3uchecker.netlify.app/img/logo.png" style="width:auto; height:60px" alt="M3U Checker"></a>
<a href="https://birdseyetv.netlify.app" target="_blank"><img src="https://birdseyetv.netlify.app/img/logo.png" style="width:auto; height:60px" alt="BirdseyeTV player"></a>
<a href="https://circletv.netlify.app" target="_blank"><img src="https://circletv.netlify.app/img/logo.png" style="width:auto; height:60px" alt="CircleTV player"></a>
<a href="https://bugsfreeweb.github.io/iptv" target="_blank"><img src="https://bugsfreeweb.github.io/iptv/img/logo.png" style="width:auto; height:60px" alt="IPTV player"></a>
<a href="https://m3ueditor.netlify.app" target="_blank"><img src="https://m3ueditor.netlify.app/img/logo.png" style="width:auto; height:60px" alt="M3U Editor"></a>
<a href="https://bugsfreeweb.github.io/WebIPTV" target="_blank"><img src="https://bugsfreeweb.github.io/iptv/img/logo.png" style="width:auto; height:60px" alt="Web IPTV"></a>


## Features

- **Automated Updates**: Runs every 8 hours (approximately 05:30, 13:30, 21:30 IST) via GitHub Actions.
- **Large Source Handling**: Processes large M3U files efficiently with streaming to minimize memory usage.
- **Active Link Verification**: Checks links for availability using concurrent requests (50 workers).
- **Duplicate Removal**: Ensures no duplicate streams (based on URL) are included.
- **HTML Source Parsing**: Extracts streaming URLs from HTML pages, filtering out non-stream links (e.g., Telegram, GitHub).
- **Multiple Export Formats**:
  - `LiveTV.m3u`: Standard M3U playlist.
  - `LiveTV.txt`: Human-readable text format with detailed channel info.
  - `LiveTV.json`: Structured JSON with channel metadata.
  - `LiveTV`: Custom JSON format without extension, designed for easy integration.

## Exported File Formats

### `LiveTV.m3u`
Standard M3U playlist format:
```
#EXTM3U
#EXTINF:-1 tvg-logo="https://i.imgur.com/VQVr4Nk.png" group-title="Entertainment",Adventure TV
http://109.233.89.170/Adventure_HD/index.m3u8
```

### `LiveTV.txt`
Readable text format:
```
Group: Entertainment
Name: Adventure TV
URL: http://109.233.89.170/Adventure_HD/index.m3u8
Logo: https://i.imgur.com/VQVr4Nk.png
Source: https://example.com/source.m3u
--------------------------------------------------
```

### `LiveTV.json`
Structured JSON with timestamp:
```json
{
  "date": "2025-03-25 13:30:00",
  "channels": {
    "Entertainment": [
      {
        "name": "Adventure TV",
        "logo": "https://i.imgur.com/VQVr4Nk.png",
        "group": "Entertainment",
        "source": "https://example.com/source.m3u",
        "url": "http://109.233.89.170/Adventure_HD/index.m3u8"
      }
    ]
  }
}
```

### `LiveTV` (Custom Format)
Custom JSON list without extension:
```json
[
  {
    "name": "Adventure TV",
    "type": "Entertainment",
    "url": "http://109.233.89.170/Adventure_HD/index.m3u8",
    "img": "https://i.imgur.com/VQVr4Nk.png"
  }
]
```

## Setup Instructions

### Prerequisites
- A GitHub account and repository (`bugsfreeweb/LiveTVCollector`).
- No local setup required; everything runs via GitHub Actions.

### Steps
1. **Clone or Fork**:
   ```bash
   git clone https://github.com/bugsfreeweb/LiveTVCollector.git
   cd LiveTVCollector
   ```

2. **Customize Sources** (Optional):
   - Edit `BugsfreeMain/Country Name.py` to update the `source_urls` list with additional CountryName-specific M3U sources.

3. **Push Changes**:
   ```bash
   git add .
   git commit -m "Initial setup or source update"
   git push origin main
   ```

4. **Verify Workflow**:
   - Go to the "Actions" tab in your GitHub repository.
   - The workflow "Country Name LiveTV Files" runs every 8 hours or can be triggered manually.

## How It Works

1. **Source Fetching**:
   - Streams M3U files and parses HTML for streaming URLs.
   - Uses `requests` with streaming to handle large files.

2. **Processing**:
   - Removes duplicates based on stream URLs.
   - Verifies link activity with concurrent HEAD/GET requests (5-second timeout).

3. **Exporting**:
   - Saves active, unique channels to four files in `LiveTV/Country Name/`.

4. **Automation**:
   - GitHub Actions runs `BugsfreeMain/Country Name.py` every 8 hours (UTC: 00:00, 08:00, 16:00 ≈ IST: 05:30, 13:30, 21:30).
   - Commits and pushes changes automatically using `GITHUB_TOKEN`.

## Dependencies

Managed by GitHub Actions:
- `requests`: For fetching M3U and HTML content.
- `pytz`: For Mumbai timezone timestamps.
- `beautifulsoup4`: For HTML parsing.

Installed in the workflow:
```bash
pip install requests pytz beautifulsoup4
```

## Troubleshooting

- **Empty Files**: Check the Actions logs for errors:
  - "Error fetching [url]": Source might be down or inaccessible.
  - "No channels parsed": Verify source format (`#EXTINF:` followed by URL).
  - "Active channels after filtering: 0": Links may be timing out; increase `timeout` in `check_link_active`.

- **Permissions Error**: Ensure `permissions: contents: write` is in `Country Name.yml`.

- **Logs**: View detailed logs in the "Actions" tab to diagnose issues.

## Contributing

Feel free to:
- Add more Country Name-specific sources to `BugsfreeMain/CountryName.py`.
- Suggest improvements via issues or pull requests.

## License

This project is open-source and available under the [MIT License](LICENSE) (add a `LICENSE` file if desired).

## Disclaimer

This project is intended solely for educational and research purposes. It aggregates publicly available streaming links from various sources on the internet for convenience and does not host, distribute, or provide any streaming content itself. The maintainers of this repository are not affiliated with the content providers or the streams listed in the exported files.

- **Usage Responsibility**: Users are responsible for ensuring their use of the streaming links complies with local laws and regulations, including copyright and intellectual property rights.
- **No Warranty**: The links provided are sourced from third-party repositories and may become unavailable or change without notice. This project offers no guarantee regarding the availability, quality, or legality of the streams.
- **Content Ownership**: All streaming content belongs to its respective owners, and this project does not claim ownership or endorse any specific content.

By using this repository or its generated files, you acknowledge and agree to these terms.

## Usage Policy
- Personal Use Only: These files are intended for personal, non-commercial use.
- No Redistribution for Profit: Do not redistribute or sell these files for commercial purposes.
- Respect Source Terms: Adhere to the terms of service of the original stream providers.
- Attribution: If you share or use this data, please credit bugsfreeweb/LiveTVCollector.
- Modification: Feel free to modify the files for personal use, but do not misrepresent them as official or endorsed content.

## Donate the project
- DOGE: <b>DEtH2yFUjjUEBUyd3scjs38X7S1Z7ee7zD</b>
- BTC Lightening: <b>bugsfree@speed.app</b>
- SOL: <b>bugsfree.sol</b>
- EVM: <b>bugsfree.bnb</b>
