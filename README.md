# Restaurant Invigilation System

A comprehensive computer vision-based surveillance and analytics system for restaurants using 4-camera setup.

## System Overview

This system monitors restaurant operations through 4 strategically placed cameras:

1. **Parking Camera**: Monitors car arrivals and departures
2. **Gate Camera**: Tracks customer entry/exit patterns
3. **Queue Camera**: Analyzes order queue length and waiting times
4. **Kitchen Camera**: Monitors staff attendance and hygiene compliance

## Key Performance Indicators (KPIs)

### Customer Analytics
- Hourly/daily customer foot traffic
- Peak hours identification
- Customer dwell time analysis
- Queue wait times and length

### Vehicle Analytics
- Parking space utilization
- Vehicle arrival/departure patterns
- Peak parking hours

### Staff Analytics
- Staff attendance tracking
- Hygiene compliance monitoring (hand washing)
- Kitchen activity levels

### Operational Analytics
- Service efficiency metrics
- Queue management insights
- Staff productivity indicators

## Technical Stack

- **Computer Vision**: OpenCV, YOLO, MediaPipe
- **Deep Learning**: TensorFlow/PyTorch
- **Database**: SQLite/PostgreSQL
- **Dashboard**: Streamlit/Flask
- **Real-time Processing**: Threading/AsyncIO

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Camera Setup Requirements

- 4 IP cameras or USB cameras
- Stable network connection
- Adequate lighting conditions
- Strategic camera positioning