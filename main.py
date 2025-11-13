#!/usr/bin/env python3
"""
Restaurant Invigilation System - Main Application
Comprehensive computer vision-based surveillance and analytics system
"""

import os
import sys
import streamlit.web.cli as stcli

def main():
    """
    Main entry point for the application.
    This script launches the Streamlit dashboard, which now contains all the application logic.
    """
    # Construct the absolute path to the dashboard application script
    project_root = os.path.dirname(__file__)
    # The dashboard app is the true entry point now
    streamlit_app_path = os.path.join(project_root, 'src', 'dashboard', 'dashboard_app.py')

    # Check if the app file exists before trying to run it
    if not os.path.exists(streamlit_app_path):
        print(f"Error: The application file was not found at {streamlit_app_path}", file=sys.stderr)
        print("Please ensure the file exists and the path is correct.", file=sys.stderr)
        sys.exit(1)

    print("="*50)
    print("Launching Restaurant Invigilation Dashboard...")
    print(f"App path: {streamlit_app_path}")
    print("="*50)

    # Use Streamlit's internal CLI runner to start the app.
    # This is programmatically equivalent to running this command in the terminal:
    # `streamlit run "c:\path\to\your\project\src\dashboard\dashboard_app.py"`
    sys.argv = [
        "streamlit",
        "run",
        streamlit_app_path,
        "--server.runOnSave", "true",
        "--server.fileWatcherType", "poll" # Use polling for robustness in some environments
    ]
    stcli.main()

if __name__ == "__main__":
    main()