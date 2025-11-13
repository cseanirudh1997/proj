"""
Dashboard Application - Real-time web dashboard for monitoring KPIs
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import logging
import json
import os
import numpy as np
import sys
import threading

# Add src to path to allow sibling imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from cameras.camera_manager import CameraManager
from analytics.kpi_processor import KPIProcessor
from database.db_manager import DatabaseManager

class RestaurantInvigilationSystem:
    def __init__(self, config_path='config/config.json', input_source_type='rtsp', video_files=None):
        """Initialize the Restaurant Invigilation System"""
        self.config = self.load_config(config_path)
        self.setup_logging()
        
        # Initialize components
        self.db_manager = DatabaseManager(self.config['database'])
        self.camera_manager = CameraManager(self.config['cameras'], self.config['models'], input_source_type, video_files)
        self.kpi_processor = KPIProcessor(self.config['analytics'], self.db_manager, self.camera_manager)
        
        self.running = False
        self.threads = []
    
    def load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            project_root = os.path.join(os.path.dirname(__file__), '..', '..')
            abs_config_path = os.path.join(project_root, config_path)
            with open(abs_config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Configuration file {abs_config_path} not found!")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing configuration file: {e}")
            sys.exit(1)
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, f'restaurant_system_{datetime.now().strftime("%Y%m%d")}.log')),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('RestaurantSystem')
        self.logger.info("Restaurant Invigilation System initialized")
    
    def start_system(self):
        """Start all system components"""
        self.logger.info("Starting Restaurant Invigilation System...")
        self.running = True
        
        # Initialize database
        self.db_manager.initialize_database()
        
        # Start camera monitoring threads
        camera_thread = threading.Thread(target=self.camera_manager.start_monitoring, daemon=True)
        camera_thread.start()
        self.threads.append(camera_thread)
        
        # Start KPI processing thread
        kpi_thread = threading.Thread(target=self.kpi_processor.start_processing, daemon=True)
        kpi_thread.start()
        self.threads.append(kpi_thread)
        
        self.logger.info("All system components started successfully")
    
    def stop_system(self):
        """Stop all system components gracefully"""
        self.logger.info("Stopping Restaurant Invigilation System...")
        self.running = False
        
        # Stop all components
        self.camera_manager.stop_monitoring()
        self.kpi_processor.stop_processing()
        self.db_manager.close_connections()
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        self.logger.info("Restaurant Invigilation System stopped")

class DashboardApp:
    def __init__(self, dashboard_config):
        """Initialize Dashboard Application"""
        self.config = dashboard_config
        self.logger = logging.getLogger('DashboardApp')
        
        self.port = self.config.get('port', 8501)
        self.refresh_rate = self.config.get('refresh_rate', 5)

        if 'app_state' not in st.session_state:
            st.session_state['app_state'] = 'setup'
        if 'video_files' not in st.session_state:
            st.session_state['video_files'] = {}
        if 'input_source_type' not in st.session_state:
            st.session_state['input_source_type'] = 'rtsp'
        if 'system' not in st.session_state:
            st.session_state['system'] = None
        
    def run(self):
        """Run the Streamlit dashboard"""
        st.set_page_config(
            page_title="Restaurant Invigilation System",
            page_icon="🏪",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        if st.session_state['app_state'] == 'setup':
            self.create_setup_page()
        else:
            self.create_dashboard()

    def create_setup_page(self):
        """Create the initial setup page for selecting input source."""
        st.title("🏪 Restaurant Invigilation System Setup")
        st.header("Select Video Input Source")

        input_type = st.radio(
            "Choose the video source for the analysis:",
            ('RTSP Feed (Live)', 'Video Upload (Pre-recorded)')
        )

        if 'RTSP' in input_type:
            st.session_state['input_source_type'] = 'rtsp'
            st.info("The system will use the RTSP URLs defined in `config/config.json`.")
        else:
            st.session_state['input_source_type'] = 'video'
            st.subheader("Upload Video Files for Each Camera")
            
            video_files = {}
            camera_names = ['parking_camera', 'gate_camera', 'queue_camera', 'kitchen_camera']
            for cam_name in camera_names:
                uploaded_file = st.file_uploader(f"Upload video for {cam_name}", type=['mp4', 'avi', 'mov'])
                if uploaded_file is not None:
                    # Save the uploaded file to a temporary location
                    temp_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'temp_videos')
                    os.makedirs(temp_dir, exist_ok=True)
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    video_files[cam_name] = file_path
            
            st.session_state['video_files'] = video_files

        if st.button("Start Analysis", type="primary"):
            if st.session_state['input_source_type'] == 'video' and len(st.session_state.get('video_files', {})) < 4:
                st.warning("Please upload all four video files to start the analysis.")
            else:
                with st.spinner("Initializing system... This may take a moment."):
                    st.session_state['app_state'] = 'running'
                    # Start the backend system
                    if st.session_state.system is None:
                        system = RestaurantInvigilationSystem(
                            input_source_type=st.session_state.input_source_type,
                            video_files=st.session_state.video_files
                        )
                        st.session_state.system = system
                        system.start_system()
                st.rerun()
    
    def create_dashboard(self):
        """Create the main dashboard interface"""
        st.title("🏪 Restaurant Invigilation System")
        st.markdown("Real-time Analytics Dashboard")
        
        date_range = self.create_sidebar()
        
        # Auto-refresh
        if st.session_state.get('auto_refresh', True):
            time.sleep(self.refresh_rate)
            st.rerun()
        
        # Main dashboard sections
        self.create_overview_section()
        self.create_customer_analytics_section(date_range)
        self.create_operational_metrics_section(date_range)
        self.create_alerts_section(date_range)
        self.create_camera_feeds_section()
    
    def create_sidebar(self):
        """Create sidebar with controls and settings"""
        st.sidebar.header("Dashboard Controls")
        
        # Auto-refresh toggle
        auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
        st.session_state['auto_refresh'] = auto_refresh
        
        # Refresh rate
        refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 30, self.refresh_rate)
        self.refresh_rate = refresh_rate
        
        # Date range selector
        st.sidebar.subheader("Date Range")
        date_range = st.sidebar.selectbox(
            "Select Period",
            ["Last Hour", "Last 4 Hours", "Today", "Last 24 Hours", "Last Week"],
            key="date_range_selector"
        )
        
        # Manual refresh button
        if st.sidebar.button("Refresh Now"):
            st.rerun()
        
        # System status
        st.sidebar.subheader("System Status")
        if st.session_state.get('system') and st.session_state.system.running:
            st.sidebar.success("🟢 All Systems Online")
        else:
            st.sidebar.error("🔴 System Offline")
        st.sidebar.info(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")
        
        return date_range
    
    def get_db_manager(self):
        """Safely get the db_manager from the system object."""
        if st.session_state.get('system'):
            return st.session_state.system.db_manager
        return None

    def get_current_kpis(self):
        """Get current KPI values from the running system."""
        if st.session_state.get('system'):
            return st.session_state.system.kpi_processor.get_current_kpis()
        return {
            'customer_flow': {'current_occupancy': 0},
            'queue_analytics': {'current_queue_length': 0},
            'staff_metrics': {'current_staff_count': 0},
            'vehicle_metrics': {'current_vehicles': 0},
            'operational_kpis': {'service_efficiency': 0}
        }
    
    def create_overview_section(self):
        """Create overview metrics section"""
        st.header("📊 Real-time Overview")
        
        # Get current KPI data
        kpis = self.get_current_kpis()
        
        # Create metric columns
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="Current Occupancy",
                value=kpis['customer_flow'].get('current_occupancy', 0)
            )
        
        with col2:
            st.metric(
                label="Queue Length",
                value=kpis['queue_analytics'].get('current_queue_length', 0)
            )
        
        with col3:
            st.metric(
                label="Staff Count",
                value=kpis['staff_metrics'].get('current_staff_count', 0)
            )
        
        with col4:
            st.metric(
                label="Vehicles Parked",
                value=kpis['vehicle_metrics'].get('current_vehicles', 0)
            )
        
        with col5:
            st.metric(
                label="Service Efficiency",
                value=f"{kpis['operational_kpis'].get('service_efficiency', 0):.1f}"
            )
    
    def create_customer_analytics_section(self, date_range):
        """Create customer analytics section"""
        st.header("👥 Customer Analytics")
        db_manager = self.get_db_manager()
        if not db_manager:
            st.warning("Database connection not available.")
            return

        col1, col2 = st.columns(2)
        with col1:
            # Hourly customer flow chart
            st.subheader("Hourly Customer Flow")
            hourly_data = db_manager.get_hourly_customer_stats(self.get_hours_for_range(date_range))
            
            if hourly_data:
                df = pd.DataFrame(hourly_data)
                fig = px.line(df, x='hour', y=['entries', 'exits'], title="Customer Entries vs Exits")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No customer data for the selected period.")
        
        with col2:
            # Queue length over time
            st.subheader("Queue Length Trends")
            queue_data = db_manager.get_queue_trends(self.get_hours_for_range(date_range))
            
            if queue_data:
                df = pd.DataFrame(queue_data)
                fig = px.area(df, x='timestamp', y='queue_length', title="Queue Length Over Time")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No queue data for the selected period.")
    
    def create_operational_metrics_section(self, date_range):
        """Create operational metrics section"""
        st.header("⚙️ Operational Metrics")
        db_manager = self.get_db_manager()
        if not db_manager:
            st.warning("Database connection not available.")
            return

        col1, col2, col3 = st.columns(3)
        with col1:
            # Staff attendance chart
            st.subheader("Staff Attendance")
            staff_data = db_manager.get_staff_attendance(self.get_hours_for_range(date_range))
            
            if staff_data:
                df = pd.DataFrame(staff_data)
                fig = px.bar(df, x='hour', y='staff_count', title="Staff Count by Hour")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No staff data available.")
        
        with col2:
            # Vehicle utilization
            st.subheader("Parking Utilization")
            parking_data = db_manager.get_parking_utilization(self.get_hours_for_range(date_range))
            
            if parking_data:
                df = pd.DataFrame(parking_data)
                fig = px.line(df, x='timestamp', y='utilization_percent', title="Parking Utilization %")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No parking data available.")
        
        with col3:
            # Hygiene compliance
            st.subheader("Hygiene Compliance")
            hygiene_data = db_manager.get_hygiene_compliance(self.get_hours_for_range(date_range))
            
            compliance_rate = hygiene_data.get('compliance_rate', 0)
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=compliance_rate,
                title={'text': "Hand Washing Compliance %"},
                gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "darkblue"}}
            ))
            st.plotly_chart(fig, use_container_width=True)
    
    def create_alerts_section(self, date_range):
        """Create alerts section"""
        st.header("🚨 Alerts & Notifications")
        db_manager = self.get_db_manager()
        if not db_manager:
            st.warning("Database connection not available.")
            return
            
        alerts = db_manager.get_recent_alerts(self.get_hours_for_range(date_range))
        if alerts:
            for alert in alerts[:10]:
                severity = alert.get('severity', 'info').upper()
                message = alert.get('message', '')
                ts = alert.get('timestamp', '')
                if severity == 'HIGH':
                    st.error(f"🔴 **{severity}:** {message} - {ts}")
                elif severity == 'MEDIUM':
                    st.warning(f"🟡 **{severity}:** {message} - {ts}")
                else:
                    st.info(f"🔵 **{severity}:** {message} - {ts}")
        else:
            st.success("✅ No active alerts for the selected period.")
    
    def create_camera_feeds_section(self):
        """Create camera feeds section"""
        if self.config.get('show_live_feed', False) and st.session_state.get('system'):
            st.header("📹 Camera Feeds")
            
            camera_manager = st.session_state.system.camera_manager
            frames = camera_manager.get_latest_frames()

            cols = st.columns(2)
            cam_ids = list(frames.keys())
            
            for i in range(0, len(cam_ids), 2):
                with cols[0]:
                    cam_id_1 = cam_ids[i]
                    st.subheader(cam_id_1.replace('_', ' ').title())
                    if frames[cam_id_1] is not None:
                        st.image(frames[cam_id_1], channels="BGR", use_column_width=True)
                    else:
                        st.info(f"No feed from {cam_id_1}")

                if i + 1 < len(cam_ids):
                    with cols[1]:
                        cam_id_2 = cam_ids[i+1]
                        st.subheader(cam_id_2.replace('_', ' ').title())
                        if frames[cam_id_2] is not None:
                            st.image(frames[cam_id_2], channels="BGR", use_column_width=True)
                        else:
                            st.info(f"No feed from {cam_id_2}")

    def get_hours_for_range(self, date_range):
        """Convert date range string to hours"""
        mapping = {
            "Last Hour": 1, "Last 4 Hours": 4, "Today": datetime.now().hour,
            "Last 24 Hours": 24, "Last Week": 24 * 7
        }
        return mapping.get(date_range, 24)

def main():
    """Main entry point for the dashboard app"""
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Failed to load or parse config/config.json: {e}")
        st.stop()

    dashboard = DashboardApp(config.get('dashboard', {}))
    dashboard.run()

if __name__ == "__main__":
    main()