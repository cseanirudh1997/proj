#!/usr/bin/env python3
"""
Demo Script for Restaurant Invigilation System
Run this to see the dashboard with sample data
"""

import streamlit as st
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Run demo dashboard"""
    print("Starting Restaurant Invigilation System Demo...")
    print("This will launch a web dashboard with sample data")
    print("=" * 50)
    
    # Import and run dashboard
    from dashboard.dashboard_app import run_dashboard
    run_dashboard()

if __name__ == "__main__":
    main()