"""
Camera Manager - Handles multiple camera feeds and processing
"""

import cv2
import numpy as np
import threading
import time
import logging
from datetime import datetime
from ultralytics import YOLO
import mediapipe as mp

class CameraManager:
    def __init__(self, camera_config, model_config, input_source_type='rtsp', video_files=None):
        """Initialize Camera Manager with configuration"""
        self.camera_config = camera_config
        self.model_config = model_config
        self.input_source_type = input_source_type
        self.video_files = video_files or {}
        self.logger = logging.getLogger('CameraManager')
        
        # Camera objects
        self.cameras = {}
        self.camera_threads = {}
        self.running = False
        
        # Detection models
        self.yolo_model = None
        self.pose_model = None
        
        # Data storage for analytics
        self.detection_data = {
            'parking': [],
            'gate': [],
            'queue': [],
            'kitchen': []
        }
        
        self.initialize_models()
        self.initialize_cameras()
    
    def initialize_models(self):
        """Initialize detection models"""
        try:
            # Load YOLO model for object detection
            self.yolo_model = YOLO(self.model_config['vehicle_detection']['model_path'])
            self.logger.info("YOLO model loaded successfully")
            
            # Initialize MediaPipe for pose detection
            self.mp_pose = mp.solutions.pose
            self.pose_model = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                enable_segmentation=False,
                min_detection_confidence=0.7
            )
            self.logger.info("MediaPipe pose model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
    
    def initialize_cameras(self):
        """Initialize all camera connections"""
        for camera_name, config in self.camera_config.items():
            try:
                source = None
                if self.input_source_type == 'video':
                    source = self.video_files.get(camera_name)
                else: # rtsp
                    source = config['source']

                # Try primary source first, then backup
                cap = cv2.VideoCapture(source)
                if not cap.isOpened():
                    self.logger.warning(f"Primary source failed for {camera_name}, trying backup")
                    cap = cv2.VideoCapture(config['backup_source'])
                
                if cap.isOpened():
                    # Set camera properties
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config['resolution'][0])
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config['resolution'][1])
                    cap.set(cv2.CAP_PROP_FPS, config['fps'])
                    
                    self.cameras[camera_name] = cap
                    self.logger.info(f"Camera {camera_name} initialized successfully with source: {source}")
                else:
                    self.logger.error(f"Failed to initialize camera {camera_name}")
                    
            except Exception as e:
                self.logger.error(f"Error initializing camera {camera_name}: {e}")
    
    def start_monitoring(self):
        """Start monitoring all cameras"""
        self.running = True
        self.logger.info("Starting camera monitoring...")
        
        # Start individual camera threads
        for camera_name in self.cameras.keys():
            thread = threading.Thread(
                target=self.process_camera_feed,
                args=(camera_name,),
                daemon=True
            )
            thread.start()
            self.camera_threads[camera_name] = thread
            
        self.logger.info("All camera monitoring threads started")
    
    def process_camera_feed(self, camera_name):
        """Process individual camera feed"""
        camera = self.cameras.get(camera_name)
        if not camera:
            return
        
        config = self.camera_config[camera_name]
        camera_type = config['type']
        
        while self.running:
            try:
                ret, frame = camera.read()
                if not ret:
                    self.logger.warning(f"Failed to read frame from {camera_name}")
                    time.sleep(1)
                    continue
                
                # Process frame based on camera type
                if camera_type == 'vehicle_detection':
                    self.process_parking_camera(frame, camera_name)
                elif camera_type == 'person_tracking':
                    self.process_gate_camera(frame, camera_name)
                elif camera_type == 'queue_analysis':
                    self.process_queue_camera(frame, camera_name)
                elif camera_type == 'staff_monitoring':
                    self.process_kitchen_camera(frame, camera_name)
                
                # Small delay to prevent overwhelming CPU
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error processing {camera_name}: {e}")
                time.sleep(1)
    
    def process_parking_camera(self, frame, camera_name):
        """Process parking area camera for vehicle detection"""
        try:
            # Run YOLO detection
            results = self.yolo_model(frame, verbose=False)
            
            vehicle_count = 0
            detections = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Filter for vehicle classes (car, motorcycle, bus, truck)
                        class_id = int(box.cls[0])
                        if class_id in self.model_config['vehicle_detection']['classes']:
                            confidence = float(box.conf[0])
                            if confidence >= self.model_config['vehicle_detection']['confidence_threshold']:
                                vehicle_count += 1
                                
                                # Extract bounding box
                                x1, y1, x2, y2 = box.xyxy[0].tolist()
                                detections.append({
                                    'class_id': class_id,
                                    'confidence': confidence,
                                    'bbox': [x1, y1, x2, y2],
                                    'timestamp': datetime.now()
                                })
            
            # Store detection data
            self.detection_data['parking'] = {
                'vehicle_count': vehicle_count,
                'detections': detections,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error in parking camera processing: {e}")
    
    def process_gate_camera(self, frame, camera_name):
        """Process gate camera for person entry/exit tracking"""
        try:
            # Run YOLO detection for persons
            results = self.yolo_model(frame, verbose=False)
            
            person_count = 0
            detections = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Filter for person class (0)
                        class_id = int(box.cls[0])
                        if class_id == 0:  # Person class
                            confidence = float(box.conf[0])
                            if confidence >= self.model_config['person_detection']['confidence_threshold']:
                                person_count += 1
                                
                                # Extract bounding box
                                x1, y1, x2, y2 = box.xyxy[0].tolist()
                                center_x = (x1 + x2) / 2
                                center_y = (y1 + y2) / 2
                                
                                detections.append({
                                    'class_id': class_id,
                                    'confidence': confidence,
                                    'bbox': [x1, y1, x2, y2],
                                    'center': [center_x, center_y],
                                    'timestamp': datetime.now()
                                })
            
            # Store detection data
            self.detection_data['gate'] = {
                'person_count': person_count,
                'detections': detections,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error in gate camera processing: {e}")
    
    def process_queue_camera(self, frame, camera_name):
        """Process queue camera for queue length analysis"""
        try:
            # Run YOLO detection for persons in queue area
            results = self.yolo_model(frame, verbose=False)
            
            queue_length = 0
            detections = []
            
            config = self.camera_config[camera_name]
            queue_zones = config.get('queue_zones', [])
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Filter for person class
                        class_id = int(box.cls[0])
                        if class_id == 0:  # Person class
                            confidence = float(box.conf[0])
                            if confidence >= self.model_config['person_detection']['confidence_threshold']:
                                
                                # Extract bounding box
                                x1, y1, x2, y2 = box.xyxy[0].tolist()
                                center_x = (x1 + x2) / 2
                                center_y = (y1 + y2) / 2
                                
                                # Check if person is in queue zone
                                for zone in queue_zones:
                                    if (zone['x'] <= center_x <= zone['x'] + zone['width'] and
                                        zone['y'] <= center_y <= zone['y'] + zone['height']):
                                        queue_length += 1
                                        
                                        detections.append({
                                            'class_id': class_id,
                                            'confidence': confidence,
                                            'bbox': [x1, y1, x2, y2],
                                            'center': [center_x, center_y],
                                            'zone': zone['name'],
                                            'timestamp': datetime.now()
                                        })
                                        break
            
            # Store detection data
            self.detection_data['queue'] = {
                'queue_length': queue_length,
                'detections': detections,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error in queue camera processing: {e}")
    
    def process_kitchen_camera(self, frame, camera_name):
        """Process kitchen camera for staff monitoring and hygiene compliance"""
        try:
            # Run YOLO detection for persons
            results = self.yolo_model(frame, verbose=False)
            
            staff_count = 0
            hand_washing_detected = False
            detections = []
            
            config = self.camera_config[camera_name]
            monitoring_zones = config.get('monitoring_zones', {})
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Filter for person class
                        class_id = int(box.cls[0])
                        if class_id == 0:  # Person class
                            confidence = float(box.conf[0])
                            if confidence >= self.model_config['person_detection']['confidence_threshold']:
                                
                                # Extract bounding box
                                x1, y1, x2, y2 = box.xyxy[0].tolist()
                                center_x = (x1 + x2) / 2
                                center_y = (y1 + y2) / 2
                                
                                # Check if person is in work area
                                work_area = monitoring_zones.get('work_area', {})
                                if work_area:
                                    if (work_area['x'] <= center_x <= work_area['x'] + work_area['width'] and
                                        work_area['y'] <= center_y <= work_area['y'] + work_area['height']):
                                        staff_count += 1
                                
                                # Check if person is at wash station (simplified hand washing detection)
                                wash_station = monitoring_zones.get('wash_station', {})
                                if wash_station:
                                    if (wash_station['x'] <= center_x <= wash_station['x'] + wash_station['width'] and
                                        wash_station['y'] <= center_y <= wash_station['y'] + wash_station['height']):
                                        hand_washing_detected = True
                                
                                detections.append({
                                    'class_id': class_id,
                                    'confidence': confidence,
                                    'bbox': [x1, y1, x2, y2],
                                    'center': [center_x, center_y],
                                    'timestamp': datetime.now()
                                })
            
            # Store detection data
            self.detection_data['kitchen'] = {
                'staff_count': staff_count,
                'hand_washing_detected': hand_washing_detected,
                'detections': detections,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error in kitchen camera processing: {e}")
    
    def get_detection_data(self):
        """Get current detection data for all cameras"""
        return self.detection_data.copy()
    
    def stop_monitoring(self):
        """Stop all camera monitoring"""
        self.logger.info("Stopping camera monitoring...")
        self.running = False
        
        # Close all cameras
        for camera in self.cameras.values():
            camera.release()
        
        # Wait for threads to finish
        for thread in self.camera_threads.values():
            if thread.is_alive():
                thread.join(timeout=5)
        
        self.logger.info("Camera monitoring stopped")