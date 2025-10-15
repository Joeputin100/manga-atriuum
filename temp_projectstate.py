    class ProjectState:
        """Advanced project state management with SQLite database for performance"""
    
        def __init__(self, db_file="project_state.db"):
            self.db_file = db_file
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self._create_tables()
            self._ensure_metadata()
    
        def _create_tables(self):
            """Create database tables if they don't exist"""
            cursor = self.conn.cursor()
    
            # Metadata table for global stats
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
    
            # Cached responses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cached_responses (
                    id INTEGER PRIMARY KEY,
                    prompt_hash TEXT,
                    volume INTEGER,
                    response TEXT,
                    timestamp TEXT,
                    UNIQUE(prompt_hash, volume)
                )
            ''')
    
            # API calls table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY,
                    prompt TEXT,
                    response TEXT,
                    volume INTEGER,
                    success BOOLEAN,
                    timestamp TEXT
                )
            ''')
    
            # Searches table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS searches (
                    id INTEGER PRIMARY KEY,
                    query TEXT,
                    books_found INTEGER,
                    timestamp TEXT
                )
            ''')
    
            # Cached cover images
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cached_cover_images (
                    id INTEGER PRIMARY KEY,
                    isbn TEXT UNIQUE,
                    url TEXT,
                    timestamp TEXT
                )
            ''')
    
            self.conn.commit()
    
        def _ensure_metadata(self):
            """Ensure default metadata exists"""
            cursor = self.conn.cursor()
            defaults = {
                "interaction_count": "0",
                "total_books_found": "0",
                "start_time": datetime.now().isoformat()
            }
            for key, value in defaults.items():
                cursor.execute('INSERT OR IGNORE INTO metadata (key, value) VALUES (?, ?)', (key, value))
            self.conn.commit()
    
        def _get_metadata(self, key: str) -> str:
            cursor = self.conn.cursor()
            cursor.execute('SELECT value FROM metadata WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row[0] if row else "0"
    
        def _set_metadata(self, key: str, value: str):
            cursor = self.conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)', (key, value))
            self.conn.commit()
    
        def record_api_call(self, prompt: str, response: str, volume: int, success: bool = True):
            """Record API call with full details for caching"""
            cursor = self.conn.cursor()
            timestamp = datetime.now().isoformat()
    
            # Insert API call
            cursor.execute('''
                INSERT INTO api_calls (prompt, response, volume, success, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (prompt, response, volume, success, timestamp))
    
            # Cache successful responses
            if success:
                prompt_hash = f"{prompt[:100]}_{volume}"
                cursor.execute('''
                    INSERT OR REPLACE INTO cached_responses (prompt_hash, volume, response, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (prompt_hash, volume, response, timestamp))
    
            self.conn.commit()
    
        def get_cached_response(self, prompt: str, volume: int) -> Optional[str]:
            """Get cached response if available"""
            cursor = self.conn.cursor()
            prompt_hash = f"{prompt[:100]}_{volume}"
            cursor.execute('SELECT response FROM cached_responses WHERE prompt_hash = ? AND volume = ?', (prompt_hash, volume))
            row = cursor.fetchone()
            return row[0] if row else None
    
        def record_interaction(self, search_query: str, books_found: int):
            """Record a new user interaction"""
            cursor = self.conn.cursor()
            timestamp = datetime.now().isoformat()
    
            # Update metadata
            interaction_count = int(self._get_metadata("interaction_count")) + 1
            total_books = int(self._get_metadata("total_books_found")) + books_found
            self._set_metadata("interaction_count", str(interaction_count))
            self._set_metadata("total_books_found", str(total_books))
    
            # Insert search
            cursor.execute('INSERT INTO searches (query, books_found, timestamp) VALUES (?, ?, ?)',
                           (search_query, books_found, timestamp))
            self.conn.commit()
    
        # Compatibility properties for existing code
        @property
        def interaction_count(self):
            return int(self._get_metadata("interaction_count"))
    
        @property
        def total_books_found(self):
            return int(self._get_metadata("total_books_found"))
    
    def get_cached_cover_image(self, isbn_key: str) -> Optional[str]:
        """Get cached cover image URL by ISBN key"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT url FROM cached_cover_images WHERE isbn = ?", (isbn_key,))
        row = cursor.fetchone()
        return row[0] if row else None

    def cache_cover_image(self, isbn_key: str, url: str):
        """Cache a cover image URL"""
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute("INSERT OR REPLACE INTO cached_cover_images (isbn, url, timestamp) VALUES (?, ?, ?)",
                       (isbn_key, url, timestamp))
        self.conn.commit()


        def close(self):
            """Close database connection"""
            self.conn.close()
        """Handles DeepSeek API interactions with rate limiting and error handling"""
    
