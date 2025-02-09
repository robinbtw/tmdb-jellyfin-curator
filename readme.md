# Movie Collection Automation Tool

This tool helps automate the process of creating themed movie collections by searching for movies by keyword, caching them via Real-Debrid, organizing them in Jellyfin collections, and optionally creating Tunarr channels.

## Disclaimer

This tool is provided for educational and personal use only. The author does not endorse or encourage illegal downloading or distribution of copyrighted content. While streaming content may exist in a legal grey area in some jurisdictions, users are responsible for complying with their local laws and regulations regarding media consumption and copyright.

This script is provided "as is" without warranty of any kind. 


## Prerequisites

- [Jellyfin](https://jellyfin.org/) server running
- [Zurg](https://github.com/debridmediamanager/zurg) with Real-Debrid configuration
- [Rclone](https://rclone.org/) setup with your cloud storage/zurg
- [Tunarr](https://github.com/tunarr/tunarr) (optional, for channel creation)

## Configuration

Before running, update the following configuration values in the files:

### utils/jellyfin.py
```python
JELLYFIN_SERVER = "http://localhost:8096"  # Your Jellyfin server address
JELLYFIN_API_KEY = "your-api-key"          # Your Jellyfin API key
MOVIE_LIBRARY_ID = "your-library-id"       # Your Movie Library ID
```

### utils/torrent.py
```python
REAL_DEBRID_API_KEY = "your-api-key"       # Your Real-Debrid API key
```

## Usage

### Basic Command
```bash
python main.py
```
This will prompt you for a keyword interactively.

### Command Line Arguments
```bash
# Search with a specific keyword
python main.py --keyword "science fiction"
python main.py -k "science fiction"

# Limit the number of results
python main.py --keyword horror --max-results 25
python main.py -k horror -m 25
```

### Interactive Options

After running the command, you'll be prompted with several options:

1. Select a specific keyword from search results
2. Create a Tunarr channel (y/n)
3. Create a Jellyfin collection (y/n)
4. Add movies to Real-Debrid (y/n)
5. Add movies to the collection (y/n)

## Example Keywords

### Generic Keywords
- horror
- action
- comedy
- drama
- thriller
- romance
- animation

### Specific Keywords
- antihero
- superhero
- mcu
- live action
- animated
- video game

## Notes

- The tool will automatically search for high-quality (1080p/BluRay) releases
- Movies are sorted by vote average from TMDB
- Library scans are automated with appropriate wait times
- Torrents require minimum 5 seeders for reliability

## Error Handling

- If a keyword isn't found, the tool will suggest random keywords
- Failed torrent searches will be logged but won't stop the process
- Invalid selections will prompt for correct input

## Contributing

Feel free to submit issues and pull requests for additional features or improvements.
