"""
Database Manager - Handles data storage and retrieval
"""

import sqlite3
import logging
import os
import json
from datetime import datetime, timedelta
import threading

class DatabaseManager:
    def __init__(self, db_config):
        """Initialize Database Manager"""
        self.config = db_config
        self.logger = logging.getLogger('DatabaseManager')
        
        self.db_path = self.config.get('path', 'data/restaurant_analytics.db')
        self.db_lock = threading.Lock()
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
    def initialize_database(self):
        """Initialize database tables"""
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Create KPI records table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS kpi_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        customer_entries INTEGER DEFAULT 0,
                        customer_exits INTEGER DEFAULT 0,
                        current_occupancy INTEGER DEFAULT 0,
                        vehicle_count INTEGER DEFAULT 0,
                        queue_length INTEGER DEFAULT 0,
                        staff_count INTEGER DEFAULT 0,
                        service_efficiency REAL DEFAULT 0.0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create customer events table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS customer_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,  -- 'entry', 'exit'
                        timestamp DATETIME NOT NULL,
                        camera_id TEXT,
                        confidence REAL,
                        metadata TEXT,  -- JSON string for additional data
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create vehicle events table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vehicle_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,  -- 'arrival', 'departure'
                        vehicle_type TEXT,  -- 'car', 'motorcycle', 'truck', etc.
                        timestamp DATETIME NOT NULL,
                        camera_id TEXT,
                        confidence REAL,
                        metadata TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create queue events table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS queue_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        queue_length INTEGER NOT NULL,
                        estimated_wait_time INTEGER,  -- in seconds
                        timestamp DATETIME NOT NULL,
                        camera_id TEXT,
                        zone_name TEXT,
                        metadata TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create staff events table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS staff_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,  -- 'attendance', 'hand_washing', 'activity'
                        staff_count INTEGER,
                        timestamp DATETIME NOT NULL,
                        camera_id TEXT,
                        zone_name TEXT,
                        metadata TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create alerts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_type TEXT NOT NULL,
                        severity TEXT NOT NULL,  -- 'low', 'medium', 'high', 'critical'
                        message TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        resolved BOOLEAN DEFAULT FALSE,
                        resolved_at DATETIME,
                        metadata TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create system logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        log_level TEXT NOT NULL,
                        component TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        metadata TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_kpi_timestamp ON kpi_records(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_customer_timestamp ON customer_events(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_vehicle_timestamp ON vehicle_events(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_queue_timestamp ON queue_events(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_staff_timestamp ON staff_events(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)')
                
                conn.commit()
                conn.close()
                
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    def save_kpi_record(self, kpi_data):
        """Save KPI record to database"""
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO kpi_records (
                        timestamp, customer_entries, customer_exits, current_occupancy,
                        vehicle_count, queue_length, staff_count, service_efficiency
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    kpi_data['timestamp'],
                    kpi_data.get('customer_entries', 0),
                    kpi_data.get('customer_exits', 0),
                    kpi_data.get('current_occupancy', 0),
                    kpi_data.get('vehicle_count', 0),
                    kpi_data.get('queue_length', 0),
                    kpi_data.get('staff_count', 0),
                    kpi_data.get('service_efficiency', 0.0)
                ))
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Error saving KPI record: {e}")
    
    def save_customer_event(self, event_type, timestamp, camera_id=None, confidence=None, metadata=None):
        """Save customer event to database"""
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                metadata_json = json.dumps(metadata) if metadata else None
                
                cursor.execute('''
                    INSERT INTO customer_events (event_type, timestamp, camera_id, confidence, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (event_type, timestamp, camera_id, confidence, metadata_json))
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Error saving customer event: {e}")
    
    def save_vehicle_event(self, event_type, vehicle_type, timestamp, camera_id=None, confidence=None, metadata=None):
        """Save vehicle event to database"""
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                metadata_json = json.dumps(metadata) if metadata else None
                
                cursor.execute('''
                    INSERT INTO vehicle_events (event_type, vehicle_type, timestamp, camera_id, confidence, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (event_type, vehicle_type, timestamp, camera_id, confidence, metadata_json))
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Error saving vehicle event: {e}")
    
    def save_queue_event(self, queue_length, timestamp, estimated_wait_time=None, camera_id=None, zone_name=None, metadata=None):
        """Save queue event to database"""
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                metadata_json = json.dumps(metadata) if metadata else None
                
                cursor.execute('''
                    INSERT INTO queue_events (queue_length, estimated_wait_time, timestamp, camera_id, zone_name, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (queue_length, estimated_wait_time, timestamp, camera_id, zone_name, metadata_json))
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Error saving queue event: {e}")
    
    def save_staff_event(self, event_type, timestamp, staff_count=None, camera_id=None, zone_name=None, metadata=None):
        """Save staff event to database"""
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                metadata_json = json.dumps(metadata) if metadata else None
                
                cursor.execute('''
                    INSERT INTO staff_events (event_type, staff_count, timestamp, camera_id, zone_name, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (event_type, staff_count, timestamp, camera_id, zone_name, metadata_json))
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Error saving staff event: {e}")
    
    def save_alert(self, alert_type, severity, message, timestamp, metadata=None):
        """Save alert to database"""
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                metadata_json = json.dumps(metadata) if metadata else None
                
                cursor.execute('''
                    INSERT INTO alerts (alert_type, severity, message, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (alert_type, severity, message, timestamp, metadata_json))
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Error saving alert: {e}")
    
    def get_kpi_data(self, start_time=None, end_time=None, limit=None):
        """Get KPI data from database"""
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                query = "SELECT * FROM kpi_records"
                params = []
                
                if start_time or end_time:
                    query += " WHERE"
                    conditions = []
                    
                    if start_time:
                        conditions.append(" timestamp >= ?")
                        params.append(start_time)
                    
                    if end_time:
                        conditions.append(" timestamp <= ?")
                        params.append(end_time)
                    
                    query += " AND".join(conditions)
                
                query += " ORDER BY timestamp DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                conn.close()
                
                # Convert to list of dictionaries
                data = [dict(zip(columns, row)) for row in rows]
                return data
                
        except Exception as e:
            self.logger.error(f"Error getting KPI data: {e}")
            return []
    
    def get_hourly_customer_stats(self, date=None):
        """Get hourly customer statistics for a specific date"""
        try:
            if not date:
                date = datetime.now().date()
            
            start_time = datetime.combine(date, datetime.min.time())
            end_time = datetime.combine(date, datetime.max.time())
            
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        strftime('%H', timestamp) as hour,
                        COUNT(CASE WHEN event_type = 'entry' THEN 1 END) as entries,
                        COUNT(CASE WHEN event_type = 'exit' THEN 1 END) as exits
                    FROM customer_events 
                    WHERE timestamp BETWEEN ? AND ?
                    GROUP BY hour
                    ORDER BY hour
                ''', (start_time, end_time))
                
                rows = cursor.fetchall()
                conn.close()
                
                return [{'hour': int(row[0]), 'entries': row[1], 'exits': row[2]} for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error getting hourly customer stats: {e}")
            return []
    
    def get_recent_alerts(self, hours=24, unresolved_only=True):
        """Get recent alerts"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                query = '''
                    SELECT * FROM alerts 
                    WHERE timestamp >= ?
                '''
                params = [cutoff_time]
                
                if unresolved_only:
                    query += " AND resolved = FALSE"
                
                query += " ORDER BY timestamp DESC"
                
                cursor.execute(query, params)
                
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                conn.close()
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error getting recent alerts: {e}")
            return []
    
    def cleanup_old_data(self, retention_days=30):
        """Clean up old data based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Clean up old records from all tables
                tables = ['kpi_records', 'customer_events', 'vehicle_events', 
                         'queue_events', 'staff_events', 'system_logs']
                
                for table in tables:
                    cursor.execute(f'DELETE FROM {table} WHERE timestamp < ?', (cutoff_date,))
                
                # Keep alerts for longer (90 days)
                alert_cutoff = datetime.now() - timedelta(days=90)
                cursor.execute('DELETE FROM alerts WHERE timestamp < ?', (alert_cutoff,))
                
                conn.commit()
                conn.close()
                
                self.logger.info(f"Cleaned up data older than {retention_days} days")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                stats = {}
                
                tables = ['kpi_records', 'customer_events', 'vehicle_events', 
                         'queue_events', 'staff_events', 'alerts', 'system_logs']
                
                for table in tables:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    count = cursor.fetchone()[0]
                    stats[table] = count
                
                # Get database size
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                size = cursor.fetchone()[0]
                stats['database_size_bytes'] = size
                
                conn.close()
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}
    
    def close_connections(self):
        """Close database connections"""
        self.logger.info("Database connections closed")