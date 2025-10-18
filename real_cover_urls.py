# Real manga cover image URLs for testing
REAL_COVER_URLS = {
    "One Piece": [
        "https://upload.wikimedia.org/wikipedia/en/9/90/One_Piece%2C_Volume_1.jpg",
        "https://upload.wikimedia.org/wikipedia/en/8/81/One_Piece_Volume_2.jpg",
        "https://upload.wikimedia.org/wikipedia/en/4/46/One_Piece_Volume_3.jpg",
        "https://upload.wikimedia.org/wikipedia/en/3/3b/One_Piece_Volume_4.jpg",
        "https://upload.wikimedia.org/wikipedia/en/5/5a/One_Piece_Volume_5.jpg",
    ],
    "Naruto": [
        "https://upload.wikimedia.org/wikipedia/en/9/9b/Naruto_Volume_1_manga_cover.jpg",
        "https://upload.wikimedia.org/wikipedia/en/7/7e/Naruto_Volume_2.jpg",
        "https://upload.wikimedia.org/wikipedia/en/4/4a/Naruto_Volume_3.jpg",
        "https://upload.wikimedia.org/wikipedia/en/3/39/Naruto_Volume_4.jpg",
        "https://upload.wikimedia.org/wikipedia/en/6/6a/Naruto_Volume_5.jpg",
    ],
    "Bleach": [
        "https://upload.wikimedia.org/wikipedia/en/7/7a/Bleach_manga_vol_1.jpg",
        "https://upload.wikimedia.org/wikipedia/en/9/9a/Bleach_manga_vol_2.jpg",
        "https://upload.wikimedia.org/wikipedia/en/7/7d/Bleach_manga_vol_3.jpg",
        "https://upload.wikimedia.org/wikipedia/en/8/8e/Bleach_manga_vol_4.jpg",
        "https://upload.wikimedia.org/wikipedia/en/2/2d/Bleach_manga_vol_5.jpg",
    ],
    "Dragon Ball": [
        "https://upload.wikimedia.org/wikipedia/en/0/0f/Dragon_Ball_Volume_1.png",
        "https://upload.wikimedia.org/wikipedia/en/1/1c/Dragon_Ball_Volume_2.png",
        "https://upload.wikimedia.org/wikipedia/en/2/2a/Dragon_Ball_Volume_3.png",
        "https://upload.wikimedia.org/wikipedia/en/3/3d/Dragon_Ball_Volume_4.png",
        "https://upload.wikimedia.org/wikipedia/en/4/4f/Dragon_Ball_Volume_5.png",
    ],
    "Death Note": [
        "https://upload.wikimedia.org/wikipedia/en/6/6f/Death_Note_Vol_1.jpg",
        "https://upload.wikimedia.org/wikipedia/en/7/7c/Death_Note_Vol_2.jpg",
        "https://upload.wikimedia.org/wikipedia/en/8/8d/Death_Note_Vol_3.jpg",
        "https://upload.wikimedia.org/wikipedia/en/9/9e/Death_Note_Vol_4.jpg",
        "https://upload.wikimedia.org/wikipedia/en/a/af/Death_Note_Vol_5.jpg",
    ],
}

def get_real_cover_url(series_name: str, volume: int) -> str:
    """Get a real cover URL for testing"""
    if series_name in REAL_COVER_URLS and 1 <= volume <= len(REAL_COVER_URLS[series_name]):
        return REAL_COVER_URLS[series_name][volume - 1]
    return None
