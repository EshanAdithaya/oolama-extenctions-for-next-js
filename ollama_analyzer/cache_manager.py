import sqlite3
import hashlib
import zlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
import pickle
import json

class CacheManager:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "cache.db"
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_cache (
                    path TEXT PRIMARY KEY,
                    content_hash TEXT,
                    last_modified REAL,
                    size INTEGER,
                    file_type TEXT,
                    compressed_content BLOB,
                    metadata TEXT,
                    last_analyzed TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    file_path TEXT,
                    question_hash TEXT,
                    response TEXT,
                    timestamp TIMESTAMP,
                    model_name TEXT,
                    PRIMARY KEY (file_path, question_hash, model_name)
                )
            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_content_hash ON file_cache(content_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_lookup ON analysis_cache(file_path, question_hash)")

    def compress_content(self, content: str) -> bytes:
        return zlib.compress(content.encode())

    def decompress_content(self, compressed: bytes) -> str:
        return zlib.decompress(compressed).decode()

    def cache_file(self, file_path: str, content: str, metadata: Dict):
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        compressed = self.compress_content(content)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO file_cache 
                (path, content_hash, last_modified, size, file_type, 
                 compressed_content, metadata, last_analyzed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_path,
                content_hash,
                metadata['last_modified'],
                len(content),
                metadata['file_type'],
                compressed,
                json.dumps(metadata),
                datetime.now().isoformat()
            ))

    def get_cached_file(self, file_path: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM file_cache WHERE path = ?",
                (file_path,)
            )
            row = cursor.fetchone()

            if row:
                return {
                    'content': self.decompress_content(row[5]),
                    'metadata': json.loads(row[6])
                }
        return None

    def cache_analysis(self, file_path: str, question: str, response: str, model_name: str):
        question_hash = hashlib.sha256(question.encode()).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO analysis_cache 
                (file_path, question_hash, response, timestamp, model_name)
                VALUES (?, ?, ?, ?, ?)
            """, (
                file_path,
                question_hash,
                response,
                datetime.now().isoformat(),
                model_name
            ))

    def get_cached_analysis(self, file_path: str, question: str, model_name: str) -> Optional[str]:
        question_hash = hashlib.sha256(question.encode()).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT response, timestamp 
                FROM analysis_cache 
                WHERE file_path = ? AND question_hash = ? AND model_name = ?
            """, (file_path, question_hash, model_name))

            result = cursor.fetchone()
            if result:
                return result[0]
        return None