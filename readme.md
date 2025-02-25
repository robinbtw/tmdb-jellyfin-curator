# TMDB Jellyfin Curator

A powerful automation tool that helps you curate and manage your movie collection by integrating TMDB, Real-Debrid, and Jellyfin. Perfect for movie enthusiasts who want to automate their media library management.

## ⚠️ Important Disclaimer

This script is **NOT** a movie downloader or a tool for piracy. It is designed to:
- Bridge the gap between Real-Debrid's cloud streaming service and your Jellyfin media server
- Automate the organization and curation of your legal media collection
- Manage metadata and collections through TMDB's API

The script does not handle any direct downloads or host any content. It simply helps manage and organize content between Real-Debrid's cloud streaming service and your personal Jellyfin server. Users are responsible for ensuring they comply with their local laws and regulations regarding media consumption and streaming services.

## 🚀 Features

- **Smart Movie Search**
  - Find movies by keywords, genres, or themes
  - Search by cast or crew members
  - Automatic popularity-based sorting
  - Smart duplicate detection

- **Service Integration**
  - TMDB for accurate movie metadata
  - Real-Debrid for content management
  - Jellyfin for media organization
  - Tunarr for custom channel creation

- **Zurg & Real-Debrid Integration**
  - Zurg mounts Real-Debrid as a virtual drive on your system
  - This allows streaming content directly from Real-Debrid's servers
  - Nothing is downloaded locally.


## 📋 Prerequisites

- Python 3.x
- [TMDB API key](https://www.themoviedb.org/settings/api)
- Real-Debrid account (for torrent scraping)
- [Jellyfin](https://github.com/jellyfin/jellyfin) server
- [Tunarr](https://github.com/chrisbenincasa/tunarr) server (optional)
- [Zurg](https://github.com/debridmediamanager/zurg-testing) (highly recommended, this script is solely built around this)


## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/robinbtw/tmdb-jellyfin-curator.git
cd tmdb-jellyfin-curator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```env
# Movie quality. Select one: 720p, 1080p, or 2160p
MOVIE_QUALITY=1080p 

# Jellyfin Configuration
JELLYFIN_SERVER=http://localhost:8096
JELLYFIN_API_KEY=your-jellyfin-api-key

# TMDb Configuration
TMDB_API_KEY=your-tmdb-api-key
TMDB_API_URL=https://api.themoviedb.org/3

# Real-Debrid Configuration
REAL_DEBRID_API_URL=https://api.real-debrid.com/rest/1.0
REAL_DEBRID_API_KEY=your-real-debrid-api-key

# Tunarr Configuration
TUNARR_SERVER=http://localhost:8000
TUNARR_TRANSCODE_CONFIG_ID=your-tunarr-transocde-id
```

## 📖 Usage Examples

### 1. Movie Collection by Actor

Create a Tom Hanks collection:
```bash
python main.py -p "Tom Hanks" -l 30
```
This will:
- Find Tom Hanks' most popular movies
- Add them to Real-Debrid
- Create a "Tom Hanks" collection in Jellyfin
- Create a "Tom Hanks Filmography" channel in Tunarr

### 2. Genre-based Collection

Create a horror movie collection:
```bash
python main.py -k "horror" -l 20 -b
```
This automatically:
- Finds top horror movies
- Processes them through Real-Debrid
- Creates a "Horror" collection
- Sets up a themed channel

### 3. Theme-based Collections

```bash
# Superhero movies
python main.py -k "superhero" -l 25

# Time travel films
python main.py -k "time travel" -l 25

# Movies based on books
python main.py -k "based on novel" -l 25
```

### 4. Smart Library Management

Clean up your library (beta):
```bash
python main.py -c
```
This will:
- Remove duplicate movies from Jellyfin
- Clean up duplicate torrents in Real-Debrid
- Optimize your media storage

### 5. Advanced Usage

Process multiple genres with custom worker count:
```bash
# Process psychological thriller movies with 15 parallel workers
python main.py -k "psychological thriller" -w 15 -l 50

# Process based on video game movies and bypass all prompts
python main.py -k "based on video game" -b -l 40
```

## 🎯 Available Search Keywords

### Popular Genres
```
✦ horror      ✦ comedy     ✦ drama
✦ adventure   ✦ fantasy    ✦ mystery
✦ crime       ✦ thriller   ✦ romance
✦ animation   ✦ family     ✦ western
✦ documentary ✦ biography  ✦ sport and more...
```

### Interesting Themes
```
✦ antihero            ✦ female protagonist
✦ superhero           ✦ disaster
✦ based on novel      ✦ based on true story
✦ time travel         ✦ space
✦ alien invasion      ✦ zombie apocalypse
✦ vampire             ✦ werewolf
✦ dystopia            ✦ post-apocalyptic
✦ heist               ✦ spy thriller and more...
✦ mafia              
```

## 🔧 Configuration Tips

### Optimizing Performance

1. Adjust worker count based on your system:
```bash
python main.py -k "suspenseful" -w 20 # for huge batches
python main.py -k "suspenseful" -w 5 # for light work
```

2. Batch processing with bypass flag:
```bash
# Process multiple themes quickly
python main.py -k "superhero" -b -l 40
python main.py -k "time travel" -b -l 40
python main.py -k "post-apocalyptic future" -b -l 40
```

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Submit bug reports
- Suggest new features
- Create pull requests

## 🔍 Troubleshooting

If you encounter issues:
1. Check your API keys in `.env`
2. Verify your service URLs are correct
3. Test proxy connections: `python main.py -t`
4. Check service status pages
5. Review logs for detailed errors
