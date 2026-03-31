import sqlite3
import json
from datetime import datetime

DB_NAME = "resume_data.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database and creates the resumes table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_name TEXT,
            original_text TEXT,
            parsed_json TEXT,
            job_description TEXT,
            enhanced_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Safely try to add ATS score columns if they don't exist for backward compatibility
    try:
        cursor.execute("ALTER TABLE resumes ADD COLUMN original_ats_score INTEGER")
    except sqlite3.OperationalError:
        pass # Column already exists
    
    try:
        cursor.execute("ALTER TABLE resumes ADD COLUMN enhanced_ats_score INTEGER")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

def create_resume_record(candidate_name, original_text, parsed_json):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO resumes (candidate_name, original_text, parsed_json)
        VALUES (?, ?, ?)
    ''', (candidate_name, original_text, json.dumps(parsed_json)))
    
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id

def update_resume_record(record_id, job_description, enhanced_json):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE resumes
        SET job_description = ?, enhanced_json = ?
        WHERE id = ?
    ''', (job_description, json.dumps(enhanced_json), record_id))
    
    conn.commit()
    conn.close()

def update_original_ats(record_id, score):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE resumes SET original_ats_score = ? WHERE id = ?', (score, record_id))
    conn.commit()
    conn.close()

def update_enhanced_ats(record_id, score):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE resumes SET enhanced_ats_score = ? WHERE id = ?', (score, record_id))
    conn.commit()
    conn.close()

def get_all_resumes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, candidate_name, original_text, parsed_json, job_description, enhanced_json, created_at, original_ats_score, enhanced_ats_score
        FROM resumes
        ORDER BY created_at DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    resumes = []
    for row in rows:
        resume = dict(row)
        if resume['parsed_json']:
            resume['parsed_json'] = json.loads(resume['parsed_json'])
        if resume['enhanced_json']:
            resume['enhanced_json'] = json.loads(resume['enhanced_json'])
        resumes.append(resume)
        
    return resumes

def delete_resume_record(record_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM resumes WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()
