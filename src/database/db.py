"""
Database Connection and Schema Management for EduHyperRAG.
Uses SQLite for zero-dependency, local file-based data persistence.
"""

import sqlite3
from pathlib import Path
from typing import Optional
from src.config import config
from src.utils.logger import get_logger

logger = get_logger("database")


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Creates and returns a SQLite database connection with Row factory enabled.
    """
    target_path = db_path or config.db_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    """
    Initializes database tables if they do not already exist.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        # 1. Users Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('teacher', 'student')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Courses Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            teacher_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)

        # 3. Documents Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            uploaded_by INTEGER NOT NULL,
            status TEXT DEFAULT 'PROCESSING' CHECK(status IN ('PROCESSING', 'READY', 'ERROR')),
            num_chunks INTEGER DEFAULT 0,
            num_concepts INTEGER DEFAULT 0,
            num_hyperedges INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE
        );
        """)

        # 4. Course Enrollments Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(course_id, student_id),
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)

        # 5. Question Answering History Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            doc_id TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            user_query TEXT NOT NULL,
            generated_answer TEXT NOT NULL,
            confidence_level TEXT DEFAULT 'Medium',
            support_score REAL DEFAULT 0.0,
            verification_decision TEXT DEFAULT 'ACCEPT',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        );
        """)

        conn.commit()
        logger.info("Successfully initialized database tables.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    finally:
        conn.close()
