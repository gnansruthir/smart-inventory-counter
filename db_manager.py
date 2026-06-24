import sqlite3
import os
from datetime import datetime

class DBManager:
    def __init__(self, db_path="data/inventory.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_items INTEGER NOT NULL,
                    total_value REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scan_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    sku_name TEXT NOT NULL,
                    detected_class TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    FOREIGN KEY (scan_id) REFERENCES scans (id)
                )
            """)
            conn.commit()

    def log_scan(self, total_items, total_value, item_breakdown):
        """
        Logs a scan session.
        item_breakdown is a list of dicts:
        [{'sku_name': '...', 'detected_class': '...', 'count': 5, 'unit_price': 1.99}]
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO scans (timestamp, total_items, total_value) VALUES (?, ?, ?)",
                (timestamp, total_items, total_value)
            )
            scan_id = cursor.lastrowid
            
            for item in item_breakdown:
                cursor.execute("""
                    INSERT INTO scan_items (scan_id, sku_name, detected_class, count, unit_price)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    scan_id,
                    item['sku_name'],
                    item['detected_class'],
                    item['count'],
                    item['unit_price']
                ))
            conn.commit()
            return scan_id

    def get_all_scans(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, timestamp, total_items, total_value FROM scans ORDER BY id DESC")
            return cursor.fetchall()

    def get_scan_details(self, scan_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sku_name, detected_class, count, unit_price 
                FROM scan_items 
                WHERE scan_id = ?
            """, (scan_id,))
            return cursor.fetchall()

    def clear_all_scans(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM scan_items")
            cursor.execute("DELETE FROM scans")
            conn.commit()
