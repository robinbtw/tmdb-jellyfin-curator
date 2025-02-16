"""
Filename: constants.py
Date: 2023-10-05
Author: robinbtw

Description:
This module contains constants used throughout the movie recommendation system.
"""

# Generic movie keywords
GENERIC_KEYWORDS = [
    "horror", "comedy", 
    "drama", "adventure", "fantasy",
    "mystery", "crime", "thriller", "romance",
    "animation", "documentary", "family", "horror", "western", "war",
    "history", "biography", "sport", "reality"
]

# Specific movie keywords
SPECIFIC_KEYWORDS = [
    "antihero", "female protagonist", "superhero", 
    "mcu", "disaster", "live action", "based on young adult novel",
    "based on video game", "based on comic", "based on novel", "based on true story",
    "time travel", "space", "alien", "zombie", "vampire", "werewolf", "robot", "dystopia",
    "post-apocalyptic", "heist", "con artist", "spy", "mafia", "gangster", "interspecies romance",
]

# Movie discovery presets
MOVIE_PRESETS = {
    "nostalgia": {
        "primary_release_date.gte": "1980-01-01",
        "primary_release_date.lte": "1999-12-31",
        "vote_average.gte": 7.0,
        "with_genres": "10751|35",  # Family, Comedy
        "sort_by": "vote_average.desc"
    },
    "date night": {
        "with_genres": "10749",  # Romance
        "vote_average.gte": 7.0,
        "without_genres": "27",  # Exclude Horror
        "sort_by": "popularity.desc"
    },
    "mind bending": {
        "with_genres": "878|53",  # Sci-Fi, Thriller
        "vote_average.gte": 7.5,
        "with_keywords": "5391",  # plot-twist
        "sort_by": "vote_count.desc"
    },
    "hidden gems": {
        "vote_average.gte": 7.5,
        "vote_count.gte": 1000,
        "vote_count.lte": 5000,
        "sort_by": "vote_average.desc"
    },
    "critically acclaimed": {
        "vote_average.gte": 8.0,
        "vote_count.gte": 5000,
        "sort_by": "vote_average.desc"
    },
    "cult classics": {
        "vote_count.gte": 500,
        "vote_count.lte": 2000,
        "sort_by": "vote_average.desc",
        "with_keywords": "1701" # cult film
    },
    "80s action": {
        "primary_release_date.gte": "1980-01-01",
        "primary_release_date.lte": "1989-12-31",
        "with_genres": "28", # Action
        "vote_average.gte": 6.5,
        "sort_by": "popularity.desc"
    },
    "family fun": {
        "with_genres": "10751", # Family
        "vote_average.gte": 6.0,
        "sort_by": "popularity.desc"
    },
    "oscar_winners": {
      "with_collection": "10", # Oscar Collection (you'd need to find the correct collection ID)
      "sort_by": "vote_average.desc"
    },
    "indie films": {
        "vote_count.lte": 2000, # Lower vote count suggests indie
        "vote_average.gte": 7.0,
        "sort_by": "vote_average.desc"
    },
    "blockbusters": {
      "vote_count.gte": 10000,
      "sort_by": "revenue.desc" # Sort by revenue
    },
    "foreign films": {
        "with_original_language": "ja|fr|de|es",  # Example: Japanese, French, German, Spanish.  Add more as needed.
        "vote_average.gte": 6.5,
        "sort_by": "vote_average.desc"
    }
}