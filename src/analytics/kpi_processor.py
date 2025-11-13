"""
KPI Processor - Analyzes detection data and generates Key Performance Indicators
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
import numpy as np

class KPIProcessor:
    def __init__(self, analytics_config, db_manager, camera_manager):
        """Initialize KPI Processor"""
        self.config = analytics_config
        self.db_manager = db_manager
        self.camera_manager = camera_manager
        self.logger = logging.getLogger('KPIProcessor')
        
        self.running = False
        self.update_interval = self.config.get('update_interval', 5)
        self.save_interval = self.config.get('save_interval', 60)
        
        # KPI data storage
        self.kpis = {
            'customer_flow': {
                'total_entries': 0,
                'total_exits': 0,
                'current_occupancy': 0,
                'hourly_entries': defaultdict(int),
                'peak_hour': None,
                'average_dwell_time': 0
            },
            'vehicle_metrics': {
                'total_vehicles': 0,
                'current_vehicles': 0,
                'hourly_arrivals': defaultdict(int),
                'peak_parking_hour': None,
                'parking_utilization': 0
            },
            'queue_analytics': {
                'current_queue_length': 0,
                'max_queue_length': 0,
                'average_queue_length': 0,
                'average_wait_time': 0,
                'total_customers_served': 0,
                'queue_history': deque(maxlen=100)
            },
            'staff_metrics': {
                'current_staff_count': 0,
                'total_staff_hours': 0,
                'hygiene_compliance_rate': 0,
                'hand_washing_events': 0,
                'attendance_log': []
            },
            'operational_kpis': {
                'service_efficiency': 0,
                'customer_satisfaction_score': 0,
                'peak_hours': [],
                'busy_periods': [],
                'alerts': []
            }
        }
        
        # Historical data for trend analysis
        self.historical_data = {
            'entries_per_hour': deque(maxlen=24),
            'queue_lengths': deque(maxlen=1440),  # 24 hours of minute data
            'staff_counts': deque(maxlen=1440),
            'vehicle_counts': deque(maxlen=1440)
        }
        
        # Tracking variables
        self.last_detection_data = {}
        self.person_tracker = {}  # Track individuals for entry/exit
        self.queue_timer = {}     # Track queue wait times
        self.staff_attendance = {}  # Track staff attendance
        
    def start_processing(self):
        """Start KPI processing loop"""
        self.running = True
        self.logger.info("Starting KPI processing...")
        
        last_save_time = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # Process KPIs
                self.process_kpis()
                
                # Save to database periodically
                if current_time - last_save_time >= self.save_interval:
                    self.save_kpis_to_database()
                    last_save_time = current_time
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in KPI processing: {e}")
                time.sleep(5)
    
    def process_kpis(self):
        """Process all KPIs from detection data"""
        detection_data = self.camera_manager.get_detection_data()
        if not detection_data:
            return

        current_time = datetime.now()
        
        # Update customer flow metrics
        self.update_customer_flow_kpis(detection_data.get('gate'), current_time)
        
        # Update vehicle metrics
        self.update_vehicle_kpis(detection_data.get('parking'), current_time)
        
        # Update queue analytics
        self.update_queue_kpis(detection_data.get('queue'), current_time)
        
        # Update staff metrics
        self.update_staff_kpis(detection_data.get('kitchen'), current_time)
        
        # Update operational KPIs
        self.update_operational_kpis(current_time)
        
        # Generate alerts if necessary
        self.check_and_generate_alerts(current_time)
    
    def update_customer_flow_kpis(self, gate_data, current_time):
        """Update customer flow related KPIs"""
        if not gate_data:
            return
        try:
            # This would process gate camera data
            # Placeholder for actual implementation
            
            hour = current_time.hour
            
            # Update hourly entries (placeholder)
            # In real implementation, this would analyze person tracking data
            # self.kpis['customer_flow']['hourly_entries'][hour] += new_entries
            
            # Calculate peak hour
            if self.kpis['customer_flow']['hourly_entries']:
                peak_hour = max(
                    self.kpis['customer_flow']['hourly_entries'],
                    key=self.kpis['customer_flow']['hourly_entries'].get
                )
                self.kpis['customer_flow']['peak_hour'] = peak_hour
            
            # Store historical data
            entries_this_hour = self.kpis['customer_flow']['hourly_entries'][hour]
            self.historical_data['entries_per_hour'].append({
                'hour': hour,
                'entries': entries_this_hour,
                'timestamp': current_time
            })
            
        except Exception as e:
            self.logger.error(f"Error updating customer flow KPIs: {e}")
    
    def update_vehicle_kpis(self, parking_data, current_time):
        """Update vehicle related KPIs"""
        if not parking_data:
            return
        try:
            self.kpis['vehicle_metrics']['current_vehicles'] = parking_data.get('vehicle_count', 0)
            hour = current_time.hour
            
            # Update hourly arrivals (placeholder)
            # self.kpis['vehicle_metrics']['hourly_arrivals'][hour] += new_arrivals
            
            # Calculate peak parking hour
            if self.kpis['vehicle_metrics']['hourly_arrivals']:
                peak_hour = max(
                    self.kpis['vehicle_metrics']['hourly_arrivals'],
                    key=self.kpis['vehicle_metrics']['hourly_arrivals'].get
                )
                self.kpis['vehicle_metrics']['peak_parking_hour'] = peak_hour
            
            # Store historical data
            current_vehicles = self.kpis['vehicle_metrics']['current_vehicles']
            self.historical_data['vehicle_counts'].append({
                'count': current_vehicles,
                'timestamp': current_time
            })
            
        except Exception as e:
            self.logger.error(f"Error updating vehicle KPIs: {e}")
    
    def update_queue_kpis(self, queue_data, current_time):
        """Update queue related KPIs"""
        if not queue_data:
            return
        try:
            current_queue_length = queue_data.get('queue_length', 0)
            self.kpis['queue_analytics']['current_queue_length'] = current_queue_length
            
            # Update queue history
            self.kpis['queue_analytics']['queue_history'].append({
                'length': current_queue_length,
                'timestamp': current_time
            })
            
            # Update max queue length
            if current_queue_length > self.kpis['queue_analytics']['max_queue_length']:
                self.kpis['queue_analytics']['max_queue_length'] = current_queue_length
            
            # Calculate average queue length
            if self.kpis['queue_analytics']['queue_history']:
                avg_length = np.mean([
                    entry['length'] for entry in self.kpis['queue_analytics']['queue_history']
                ])
                self.kpis['queue_analytics']['average_queue_length'] = round(avg_length, 2)
            
            # Store historical data
            self.historical_data['queue_lengths'].append({
                'length': current_queue_length,
                'timestamp': current_time
            })
            
        except Exception as e:
            self.logger.error(f"Error updating queue KPIs: {e}")
    
    def update_staff_kpis(self, kitchen_data, current_time):
        """Update staff related KPIs"""
        if not kitchen_data:
            return
        try:
            current_staff = kitchen_data.get('staff_count', 0)
            self.kpis['staff_metrics']['current_staff_count'] = current_staff
            
            # Store historical data
            self.historical_data['staff_counts'].append({
                'count': current_staff,
                'timestamp': current_time
            })
            
            # Update attendance log
            # In real implementation, this would track individual staff members
            
        except Exception as e:
            self.logger.error(f"Error updating staff KPIs: {e}")
    
    def update_operational_kpis(self, current_time):
        """Update operational KPIs"""
        try:
            # Calculate service efficiency
            queue_length = self.kpis['queue_analytics']['average_queue_length']
            staff_count = self.kpis['staff_metrics']['current_staff_count']
            
            if staff_count > 0 and queue_length > 0:
                # Simple efficiency metric: lower is better
                efficiency = queue_length / staff_count
                self.kpis['operational_kpis']['service_efficiency'] = round(efficiency, 2)
            
            # Identify peak hours
            hourly_entries = self.kpis['customer_flow']['hourly_entries']
            if hourly_entries:
                avg_entries = np.mean(list(hourly_entries.values()))
                peak_hours = [
                    hour for hour, entries in hourly_entries.items()
                    if entries > avg_entries * 1.5
                ]
                self.kpis['operational_kpis']['peak_hours'] = peak_hours
            
        except Exception as e:
            self.logger.error(f"Error updating operational KPIs: {e}")
    
    def check_and_generate_alerts(self, current_time):
        """Check conditions and generate alerts"""
        try:
            alerts = []
            
            # Check queue length alert
            max_queue = self.config.get('alert_thresholds', {}).get('max_queue_length', 10)
            current_queue = self.kpis['queue_analytics']['current_queue_length']
            
            if current_queue > max_queue:
                alerts.append({
                    'type': 'queue_alert',
                    'message': f'Queue length ({current_queue}) exceeds threshold ({max_queue})',
                    'severity': 'high',
                    'timestamp': current_time
                })
            
            # Check staff count alert
            min_staff = self.config.get('alert_thresholds', {}).get('min_staff_count', 2)
            current_staff = self.kpis['staff_metrics']['current_staff_count']
            
            if current_staff < min_staff:
                alerts.append({
                    'type': 'staff_alert',
                    'message': f'Staff count ({current_staff}) below minimum ({min_staff})',
                    'severity': 'medium',
                    'timestamp': current_time
                })
            
            # Store alerts
            self.kpis['operational_kpis']['alerts'].extend(alerts)
            
            # Keep only recent alerts (last 100)
            if len(self.kpis['operational_kpis']['alerts']) > 100:
                self.kpis['operational_kpis']['alerts'] = \
                    self.kpis['operational_kpis']['alerts'][-100:]
            
        except Exception as e:
            self.logger.error(f"Error generating alerts: {e}")
    
    def get_current_kpis(self):
        """Get current KPI values"""
        return self.kpis.copy()
    
    def get_historical_data(self, metric_type, hours=24):
        """Get historical data for a specific metric"""
        try:
            if metric_type not in self.historical_data:
                return []
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            historical = list(self.historical_data[metric_type])
            
            # Filter by time range
            filtered_data = [
                entry for entry in historical
                if entry.get('timestamp', datetime.now()) >= cutoff_time
            ]
            
            return filtered_data
            
        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            return []
    
    def save_kpis_to_database(self):
        """Save current KPIs to database"""
        try:
            current_time = datetime.now()
            
            # Prepare KPI data for database
            kpi_record = {
                'timestamp': current_time,
                'customer_entries': self.kpis['customer_flow']['total_entries'],
                'customer_exits': self.kpis['customer_flow']['total_exits'],
                'current_occupancy': self.kpis['customer_flow']['current_occupancy'],
                'vehicle_count': self.kpis['vehicle_metrics']['current_vehicles'],
                'queue_length': self.kpis['queue_analytics']['current_queue_length'],
                'staff_count': self.kpis['staff_metrics']['current_staff_count'],
                'service_efficiency': self.kpis['operational_kpis']['service_efficiency']
            }
            
            # Save to database (placeholder - would implement actual database saving)
            self.db_manager.save_kpi_record(kpi_record)
            
            self.logger.debug(f"KPIs saved to database at {current_time}")
            
        except Exception as e:
            self.logger.error(f"Error saving KPIs to database: {e}")
    
    def stop_processing(self):
        """Stop KPI processing"""
        self.logger.info("Stopping KPI processing...")
        self.running = False