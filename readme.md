# Movie Collection Manager
A Python-based tool that helps you manage movie collections by integrating with TMDB, Real-Debrid, Jellyfin, and Tunarr. Search for movies by keywords, automatically download them through Real-Debrid, organize them in Jellyfin collections, and create 24/7 streaming channels with Tunarr.

## Features

- Search movies by keywords using TMDB API
- Automatically find and cache torrents via Real-Debrid
- Create and manage Jellyfin collections
- Generate 24/7 streaming channels with Tunarr
- Smart movie selection based on ratings and quality
- Rate-limited API requests to prevent throttling

## Prerequisites

- Python 3.x
- [Jellyfin](https://jellyfin.org/) server
- Real-debrid account
- [Zurg](https://github.com/debridmediamanager/zurg-testing)/[Rclone](https://rclone.org/)
- Tmdb API key
- [Tunarr](https://github.com/chrisbensch/tunarr) server (optional)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/robinbtw/tmdb-automation.git
cd tmdb-automation
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with the following variables:
```
TMDB_API_KEY=your_tmdb_api_key
JELLYFIN_SERVER=your_jellyfin_server_url
JELLYFIN_API_KEY=your_jellyfin_api_key
MOVIE_LIBRARY_ID=your_jellyfin_movie_library_id
REAL_DEBRID_API_KEY=your_real_debrid_api_key
```

### Command Line Arguments

- `-k`: Keyword to search for (use quotes for multiple words)
- `-m`: Maximum number of movies to process (default: 50)

## Usage

Keyword can be used with or without quotes. Quotes required for keywords with spaces.
Run the main script with optional arguments:

```bash
python main.py -k mcu -m 35
python main.py -k "time travel" -m 25
```

## Features Breakdown

### TMDB Integration
- Search movies by keywords
- Fetch detailed movie information
- Get movie certifications and metadata

### Jellyfin Features
- Create and manage collections
- Add movies to collections
- Perform library scans

### Real-Debrid Integration
- Search for movie torrents (currently only 1337x)
- Add magnets to Real-Debrid
- Rate-limited requests to prevent API throttling

### Tunarr Features
- Create themed movie channels
- Add movies to channels
- Configure channel settings
- Manage programming schedules

## Disclaimer

This tool is provided for educational and personal use only. The author does not endorse or encourage illegal downloading or distribution of copyrighted content. While streaming content may exist in a legal grey area in some jurisdictions, users are responsible for complying with their local laws and regulations regarding media consumption and copyright.
