# Movie Collection Automation Suite

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Jellyfin](https://img.shields.io/badge/jellyfin-compatible-00A4DC)](https://jellyfin.org/)
[![Real-Debrid](https://img.shields.io/badge/Real--Debrid-API-red)](https://real-debrid.com/)
[![TMDB](https://img.shields.io/badge/TMDB-API-01B4E4)](https://www.themoviedb.org/)

A comprehensive automation tool for managing movie collections. Integrates TMDB for movie discovery, Real-Debrid for secure downloads, and Jellyfin for media organization. Features automated metadata management, smart collection creation, and 24/7 channel programming through Tunarr.

## 🌟 Key Features

### Movie Discovery & Management
- Search movies by keywords, cast members, or discover random suggestions
- Smart metadata verification and auto-updates
- Automated quality-based media selection (720p/1080p/2160p)
- Multi-threaded processing for efficient operations

### Collection Organization
- Automatic collection creation and management in Jellyfin
- Smart duplicate detection and cleanup
- Library integrity verification
- Automated metadata updates for incomplete entries

### Tunarr Integration
- Create 24/7 movie channels automatically
- Smart programming based on collections
- Automatic channel number normalization
- Support for filmography-based channels

### Real-Debrid Features
- Secure torrent handling through Real-Debrid
- Smart caching system to avoid duplicates
- Quality-based selection with seeder verification
- Multi-site search support (1337x, YTS)

## 📋 Prerequisites

- Python 3.9 or higher
- Jellyfin server (Plex/Emby not supported)
- Real-Debrid premium account
- TMDB API access
- [Zurg](https://github.com/debridmediamanager/zurg-testing) for Real-Debrid integration
- [Rclone](https://rclone.org) for cloud storage mounting
- [Tunarr](https://github.com/arabcoders/tunarr) for channel management

## 🚀 Quick Start

1. Clone the repository:
```bash
git clone https://github.com/robinbtw/tmdb-automation.git
cd tmdb-automation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your environment:
Create a `.env` file with your settings:
```env
# Media Quality
MOVIE_QUALITY=1080p 

# Jellyfin Settings
JELLYFIN_SERVER=http://localhost:8096
JELLYFIN_API_KEY=your-jellyfin-api-key

# TMDB Settings
TMDB_API_KEY=your-tmdb-api-key
TMDB_API_URL=https://api.themoviedb.org/3

# Real-Debrid Settings
REAL_DEBRID_API_URL=https://api.real-debrid.com/rest/1.0
REAL_DEBRID_API_KEY=your-real-debrid-api-key

# Tunarr Settings
TUNARR_SERVER=http://localhost:8000
TUNARR_TRANSCODE_CONFIG_ID=your-tunarr-config-id
```

## 💻 Usage

### Basic Commands
```bash
# Search by keyword
python main.py -k "dark fantasy" -l 20 -w 4

# Search by person
python main.py -p "tom cruise" -l 30 -w 6

# Get random suggestions
python main.py -r -l 15

# Verify media integrity
python main.py -v

# Clean up duplicates
python main.py -c

# Test connectivity
python main.py -t
```

### Command Arguments
- `-k, --keyword`: Search using keywords
- `-p, --person`: Search by actor/director/writer
- `-r, --random`: Get random movie suggestions
- `-l, --limit`: Set maximum results (default: 30)
- `-w, --workers`: Set parallel workers (default: 1)
- `-c, --cleanup`: Remove duplicates
- `-t, --test`: Test proxy connections
- `-b, --bypass`: Skip confirmation prompts

### Example Workflows

#### Create an Actor Collection
```bash
# Create Tom Cruise collection with 40 movies
python main.py -p "tom cruise" -l 40 -w 4 -b
```

#### Build a Genre Channel
```bash
# Create horror movie channel with 100 movies
python main.py -k "horror" -l 100 -w 6 -b
```

#### Maintain Library
```bash
# Remove duplicates
python main.py -c
```

## ⚙️ Best Practices

- Start with low worker counts (1-2) to avoid rate limits
- Run `-c` periodically to clean up duplicates
- Test connections with `-t` if experiencing issues
- Keep Jellyfin libraries updated for best matching
- When searching keywords, try to use more specific searches
- Use quotes for multi-word searches

## 🔍 Supported Search Categories

### Genres
- Horror, Comedy, Drama, Adventure
- Fantasy, Mystery, Crime, Thriller
- Romance, Animation, Documentary
- Family, Western, History, Sport

### Themes
- Superhero, Time Travel, Space
- Based on Books/Comics/Games
- Disaster, Post-Apocalyptic
- Heist, Spy, Crime, Mafia
- Zombie, Vampire, Robot
- Dystopian, Cyberpunk

## ⚠️ Rate Limiting

- TMDB: 30 requests/10 seconds
- Real-Debrid: 1 request/2 seconds
- Jellyfin: No strict limits
- Tunarr: Local API, no limits

## 🛡️ Disclaimer

This tool is for educational purposes only. Users are responsible for compliance with local laws and service terms. The developers do not endorse or encourage unauthorized content access.

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.