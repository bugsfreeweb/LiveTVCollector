AJN Professional Player — Enterprise Media Console
A high-performance, single-screen broadcast control deck for live IPTV playback and archive streaming.

AJN Professional Player is a modern, React 18-powered media application designed for seamless live TV streaming and on-demand content management. It features an intelligent M3U playlist parser, resilient HLS streaming, archive scheduling, and multiple export formats for custom web applications.
# 📊 Project Stats
[![GitHub forks](https://img.shields.io/github/forks/bugsfreeweb/LiveTVCollector?logo=forks&style=plastic)](https://github.com/bugsfreeweb/LiveTVCollector/network) [![GitHub stars](https://img.shields.io/github/stars/bugsfreeweb/LiveTVCollector)](https://github.com/bugsfreeweb/LiveTVCollector/stargazers) [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)  [![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)
![GitHub issues](https://img.shields.io/github/issues/bugsfreeweb/LiveTVCollector)
![GitHub pull requests](https://img.shields.io/github/issues-pr/bugsfreeweb/LiveTVCollector)

## Online Useable Tools:

<a href="https://buddytv.vercel.app" target="_blank"><img src="https://buddytv.vercel.app/img/logo.png" style="width:auto; height:60px" alt="BuddyTv"></a>
<a href="https://m3ulinkchecker.vercel.app" target="_blank"><img src="https://m3ulinkchecker.vercel.app/img/logo.png" style="width:auto; height:60px" alt="M3U Checker"></a>
<a href="https://circletv.vercel.app" target="_blank"><img src="https://circletv.vercel.app/img/logo.png" style="width:auto; height:60px" alt="CircleTV player"></a>
<a href="https://bugsfreeweb.github.io/iptv" target="_blank"><img src="https://bugsfreeweb.github.io/iptv/img/logo.png" style="width:auto; height:60px" alt="IPTV player"></a>
<a href="https://m3ulinkeditor.vercel.app" target="_blank"><img src="https://m3ulinkeditor.vercel.app/img/logo.png" style="width:auto; height:60px" alt="M3U Editor"></a>
<a href="https://bugsfreeweb.github.io/WebIPTV" target="_blank"><img src="https://bugsfreeweb.github.io/iptv/img/logo.png" style="width:auto; height:60px" alt="Web IPTV"></a>
<a href="https://bugsfreetv.vercel.app" target="_blank"><img src="https://bugsfreetv.vercel.app/img/logo.png" style="width:auto; height:60px" alt="Web IPTV Player"></a>
🎯 Key Features
Core Playback & Streaming
Unified Stream Console: Load and manage M3U playlists with real-time search, fuzzy matching, category organization, and persistent favorites
Live IPTV Support: Native HLS streaming with automatic buffer optimization and keyframe recovery
Archive Scheduling: Parse broadcast manifests, organize segments by hour, and navigate with color-coded status indicators
Resilient Playback Engine: Automatic memory management, garbage collection, and browser leak prevention with hls.js pipelines
Advanced Playback Features
Sirius Audio Console: Integrated premium audio deck with 120-frequency spectrum visualizer, EQ controls, loop selectors, and timeline scrubbing
Smart Adaptive Themes: Seamlessly toggle between Dark (default) and Light modes with intuitive UI controls
Diagnostic Debug Terminal: Real-time buffer latency reports, segment tracking, and proxy thread monitoring
Cinephile Intelligence Suite (v4.0)
Nine integrated modules for content discovery and viewing analytics:

Mood Journaling: Pre-watch environment tracking and detailed ratings
Episode Analysis: Narrative structure and continuity tracking synced with playback
Playlist Versioning: Version control with SHA-256 hashes and branch checkout
Timeline Composition: Chronological workbench for dynamic channels and streams
Mood Discovery Matrix: Contextual filtering by lighting, duration, and cognitive load
Side-by-Side Comparison: Frame-accurate stream alignment with offset buffers
Clipping Hub: Segment splicing with custom frame taxonomy and transcripts
Viewing DNA Heatmap: Affinity graphs and preferred viewing range analytics
Calendar Scheduler: Automated event pairing with backup harvesting
Dynamic Export Suite
Transform playlists into custom, self-contained web applications:

TV Explorer Dashboard — Modern black grid interface with lazy-loading cards and fullscreen players
VidGrid Monitor Wall — 9-channel parallel grid for multi-monitor sports/news viewing
Retro TV Cabinet — Analog wood-grain home entertainment interface with animated channel transitions
EPG Loop Display — Lightweight TV schedule with synchronized clocks and slide crossfades
Multi-Language M3U Serializer — Automatic categorization by language (EN, ES, RU, etc.)
Liberty Express Return Vector — Self-contained HTML apps with return anchor to host platform
Smart HUD & Deep Linking
Query Parameter Auto-Loading: Launch streams directly via ?stream=url&title=title
Glassmorphic Floating HUD: Active countdowns, dynamic tags, clipboard sharing, and Theater Mode toggle
🏗️ Architecture Overview


External Sources (HLS M3U8, IPTV M3U, XML)
                ↓
         Node.js Express Proxy
         (CORS bypass, backpressure handling)
                ↓
         Refined Client Deck
         (HLS.js buffering, M3U parsing, UI rendering)
Technical Highlights
Category Preservation: Extracts group-title attributes from M3U metadata to maintain playlist structure
Memory Optimization: Formal stream destructuring when switching channels; pending requests terminated cleanly
Decoupled Rendering: Isolated clock and playhead components reduce root application redraw overhead
50MB HLS Buffer: Dynamic segment caching with automatic keyframe recovery
📦 Installation & Setup
Prerequisites
Node.js 16+ and npm
A modern web browser (Chrome, Firefox, Safari, Edge)
Installation Steps
bash


# Install dependencies
npm install

# Build React bundle & Express backend
npm run build

# Start the application
npm run start
The application will launch on http://localhost:3000

⚙️ Configuration
Create a .env file in your project root with the following variables:

env


# .env
PORT=3000
NODE_ENV=production
Variable	Default	Description
PORT	3000	Express server port for hosting and routing
NODE_ENV	production	Build output mode (compressed CJS server bundle to /dist/server.cjs)
🎬 Usage Guide
Loading a Playlist
Navigate to the Playlist tab
Import an M3U file or paste a direct M3U URL
Streams automatically categorize by group-title
Use the search bar for real-time filtering
Creating Custom Exports
Select streams from your loaded playlist
Choose an export format (Dashboard, Grid, Cabinet, etc.)
Download the generated HTML file
Open in any modern browser for instant playback
Using the Audio Console
Access via the Sirius Audio button
Adjust EQ, enable spectrum visualization, loop segments
Works in both Light and Dark themes
Deep Linking
Launch a stream directly with query parameters:



http://localhost:3000?stream=https://example.com/stream.m3u8&title=Stream%20Name
⚠️ Limitations & Best Practices
Limitation	Solution
Playback stuttering or choppy video	Open the dashboard in a dedicated browser tab for full frame authority
CORS-restricted streams fail to load	Ensure the Express Proxy option is enabled on custom servers
High memory usage with large playlists	Monitor via Diagnostic Debug Terminal; reduce buffer size if needed
Export compatibility	Test exported HTML files in target browsers before deployment
Performance Tips
Use the Diagnostic Debug Terminal to monitor buffer latency in real time
Limit simultaneous streams in VidGrid to 9 for optimal performance
Clear browser cache if export files don't update
Enable Dark mode for reduced eye strain during extended use
🔗 Project Structure


ajn-professional-player/
├── src/
│   ├── components/        # React UI components
│   ├── hooks/             # Custom React hooks
│   ├── utils/             # M3U parsers, HLS logic
│   ├── styles/            # Theme & CSS modules
│   └── App.jsx            # Main application container
├── server/
│   └── proxy.js           # Express CORS proxy
├── dist/
│   ├── client/            # Built React bundle
│   └── server.cjs         # Compiled Node server
├── .env.example           # Environment variable template
└── package.json
🚀 Tech Stack
Frontend: React 18, Vite, hls.js
Backend: Node.js, Express.js
Media: HLS streaming, M3U playlists, EPG scheduling
UI/UX: Glassmorphic design, responsive theming, spectrum visualization
📝 License & Attribution
This project integrates with Liberty Express (www.liberty-express.org) for hosted exports. All generated applications include a return anchor to the host platform.

🤝 Contributing
Contributions are welcome. Please ensure:

Code follows the existing component structure
M3U parsing logic preserves category metadata
Memory cleanup includes proper .detachMedia() calls
Exports are tested in multiple browsers
❓ FAQ
Q: Can I use this with custom IPTV sources?
A: Yes. Import any M3U playlist (local file or URL) and the parser will automatically categorize by group-title.

Q: Does this work offline?
A: The player requires an internet connection to stream live IPTV content. Exported HTML files can work offline if streams are pre-cached.

Q: How do I export for multiple languages?
A: Use the Multi-Language M3U Serializer export option. The parser detects EN, ES, RU, and other language tags and splits accordingly.

Q: What browsers are supported?
A: Modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+). Older browsers may experience compatibility issues.





