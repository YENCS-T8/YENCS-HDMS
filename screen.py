#!/usr/bin/env python3
"""
Enhanced LocalCast - Multi-Monitor Screen Casting Server
Cast different webpages or screens to Monitor 1, Monitor 2, and Monitor 3
- Admin computer controls three viewer computers via a web interface.
- Supports rendering and streaming webpage content, desktop, or custom content.
- Webpages are 'locked' to each viewer during casting.
"""

import logging
import sys
import os
from typing import Any, Dict, Optional
from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import base64
import threading
import time
import io
from PIL import Image, ImageDraw, ImageFont
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
import socket
import mss
from datetime import datetime

# Force unbuffered stdout to ensure logs appear in terminal
sys.stdout.reconfigure(line_buffering=True)

# Set up logging with file path and line number
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('localcast.log')
    ],
    force=True  # Ensure this config overrides any existing handlers
)
logger = logging.getLogger(__name__)

# Test logging immediately
logger.debug("Logging test: DEBUG message - should appear in terminal and localcast.log")
logger.info("Logging test: INFO message - should appear in terminal and localcast.log")
logger.error("Logging test: ERROR message - should appear in terminal and localcast.log")

# Check for required dependencies
try:
    import flask_socketio
    import PIL
    import mss
    import selenium
except ImportError as e:
    logger.error(f"Missing dependency: {e}. Please run: pip install flask flask-socketio pillow mss selenium")
    sys.exit(1)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'localcast_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)

class MultiMonitorCaster:
    def __init__(self):
        # Get number of available monitors
        with mss.mss() as sct:
            self.monitor_count = len(sct.monitors) - 1
            logger.info(f"Detected {self.monitor_count} monitors")
        # Initialize Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_window_size(1280, 720)  # Default resolution for webpage capture
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromeDriver: {e}")
            logger.info("Ensure Chrome and ChromeDriver are installed and versions match.")
            sys.exit(1)
        self.monitor_casters = {
            'monitor1': {
                'id': '068243DF-2EE6-42C7-B358-D66BAD7FEF81',
                'is_casting': False,
                'quality': 80,
                'fps': 30,
                'scale': 1.0,
                'source_monitor': 0,
                'cast_thread': None,
                'frame_count': 0,
                'connected_clients': set(),
                'screen_content': 'desktop',  # Options: desktop, custom, webpage
                'webpage_url': None,
                'last_webpage_image': None,
                'last_webpage_update': 0,
            },
            'monitor2': {
                'id': 'A75199C3-927D-43AF-B866-D5E45254D2FC',
                'is_casting': False,
                'quality': 80,
                'fps': 30,
                'scale': 1.0,
                'source_monitor': 1 if self.monitor_count > 1 else 0,
                'cast_thread': None,
                'frame_count': 0,
                'connected_clients': set(),
                'screen_content': 'webpage',
                'webpage_url': None,
                'last_webpage_image': None,
                'last_webpage_update': 0,
            },
            'monitor3': {
                'id': 'B8290E4F-1C3A-4B9E-AF12-7C8F9D3E6A7B',
                'is_casting': False,
                'quality': 80,
                'fps': 30,
                'scale': 1.0,
                'source_monitor': 2 if self.monitor_count > 2 else 0,
                'cast_thread': None,
                'frame_count': 0,
                'connected_clients': set(),
                'screen_content': 'webpage',
                'webpage_url': None,
                'last_webpage_image': None,
                'last_webpage_update': 0,
            }
        }

    def get_monitors(self):
        """Get available physical monitors"""
        try:
            with mss.mss() as sct:
                monitors = [
                    {
                        'id': i,
                        'width': monitor['width'],
                        'height': monitor['height'],
                        'left': monitor['left'],
                        'top': monitor['top']
                    }
                    for i, monitor in enumerate(sct.monitors[1:], start=0)
                ]
                logger.debug(f"Available monitors: {monitors}")
                return monitors
        except Exception as e:
            logger.error(f"Error getting monitors: {e}")
            return []

    def capture_screen(self, monitor_key):
        """Capture content for specific monitor"""
        try:
            monitor_config = self.monitor_casters[monitor_key]
            content_type = monitor_config['screen_content']
            logger.debug(f"Capturing {content_type} for {monitor_key}")
            if content_type == 'desktop':
                return self._capture_desktop(monitor_config, monitor_key)
            elif content_type == 'custom':
                return self._capture_custom_content(monitor_config, monitor_key)
            elif content_type == 'webpage':
                return self._capture_webpage_content(monitor_config, monitor_key)
        except Exception as e:
            logger.error(f"Screen capture error for {monitor_key}: {e}")
            return None

    def _capture_desktop(self, config, monitor_key):
        """Capture desktop screen"""
        try:
            with mss.mss() as sct:
                monitor_idx = config['source_monitor']
                if monitor_idx >= len(sct.monitors) - 1:
                    logger.warning(f"Invalid monitor index {monitor_idx} for {monitor_key}, falling back to 0")
                    monitor_idx = 0
                monitor = sct.monitors[monitor_idx + 1]
                screenshot = sct.grab(monitor)
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb, 'raw', 'RGB')
                if config['scale'] != 1.0:
                    new_size = (int(img.width * config['scale']), int(img.height * config['scale']))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                return self._encode_image(img, config)
        except Exception as e:
            logger.error(f"Desktop capture error for {monitor_key}: {e}")
            return None

    def _capture_custom_content(self, config, monitor_key):
        """Generate custom content for demonstration or fallback"""
        try:
            width, height = 1280, 720  # Match Selenium resolution
            img = Image.new('RGB', (width, height), color='black')
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()

            if monitor_key == 'monitor1':
                for y in range(height):
                    for x in range(width):
                        red = int(255 * (x / width))
                        img.putpixel((x, y), (red, 0, 0))
                draw.text((50, height//2), "Monitor 1 - Fallback", fill="white", font=font)
            elif monitor_key == 'monitor2':
                for y in range(height):
                    for x in range(width):
                        blue = int(255 * (x / width))
                        img.putpixel((x, y), (0, 0, blue))
                draw.text((50, height//2), "Monitor 2 - Fallback", fill="white", font=font)
            else:  # monitor3
                for y in range(height):
                    for x in range(width):
                        green = int(255 * (x / width))
                        img.putpixel((x, y), (0, green, 0))
                draw.text((50, height//2), "Monitor 3 - Fallback", fill="white", font=font)

            logger.debug(f"Generated custom content for {monitor_key}")
            return self._encode_image(img, config)
        except Exception as e:
            logger.error(f"Custom content error for {monitor_key}: {e}")
            return None

    def _capture_webpage_content(self, config, monitor_key):
        """Capture webpage content using Selenium"""
        try:
            url = config.get('webpage_url')
            if not url or not url.startswith(('http://', 'https://')):
                logger.error(f"Invalid webpage URL for {monitor_key}: {url}")
                return self._capture_custom_content(config, monitor_key)

            # Use cached image if not enough time has passed
            current_time = time.time()
            if current_time - config['last_webpage_update'] < 5 and config['last_webpage_image']:
                logger.debug(f"Using cached webpage image for {monitor_key}: {url}")
                return config['last_webpage_image']

            # Navigate to the webpage
            logger.info(f"Loading webpage for {monitor_key}: {url}")
            try:
                self.driver.get(url)
                # Wait for the page to load (up to 10 seconds)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                logger.info(f"Webpage loaded successfully for {monitor_key}: {url}")
            except TimeoutException:
                logger.error(f"Timeout while loading webpage for {monitor_key}: {url}")
                return self._capture_custom_content(config, monitor_key)
            except WebDriverException as e:
                logger.error(f"WebDriver error while loading webpage for {monitor_key}: {url}, {str(e)}")
                return self._capture_custom_content(config, monitor_key)

            # Capture screenshot
            try:
                screenshot = self.driver.get_screenshot_as_png()
                img = Image.open(io.BytesIO(screenshot)).convert('RGB')
                logger.info(f"Screenshot captured for {monitor_key}: {url}")
            except Exception as e:
                logger.error(f"Failed to capture screenshot for {monitor_key}: {url}, {str(e)}")
                return self._capture_custom_content(config, monitor_key)

            # Resize if needed
            if config['scale'] != 1.0:
                new_size = (int(img.width * config['scale']), int(img.height * config['scale']))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Encode and cache the image
            encoded_img = self._encode_image(img, config)
            config['last_webpage_image'] = encoded_img
            config['last_webpage_update'] = current_time
            logger.debug(f"Captured and encoded webpage for {monitor_key}: {url}")
            return encoded_img
        except Exception as e:
            logger.error(f"Unexpected error in webpage capture for {monitor_key}: {e}")
            return self._capture_custom_content(config, monitor_key)

    def _encode_image(self, img, config):
        """Encode image to base64"""
        try:
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=config['quality'], optimize=True)
            img_bytes = buffer.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            return {
                'image': f'data:image/jpeg;base64,{img_base64}',
                'width': img.width,
                'height': img.height,
                'timestamp': time.time(),
                'monitor': config['id']
            }
        except Exception as e:
            logger.error(f"Image encoding error: {e}")
            return None

    def start_casting(self, monitor_key):
        """Start casting for specific monitor"""
        try:
            if monitor_key not in self.monitor_casters:
                logger.error(f"Invalid monitor key: {monitor_key}")
                return False
            config = self.monitor_casters[monitor_key]
            if config['is_casting']:
                logger.info(f"{monitor_key} is already casting")
                return False
            config['is_casting'] = True
            config['frame_count'] = 0

            def cast_loop():
                while config['is_casting'] and len(config['connected_clients']) > 0:
                    try:
                        frame_data = self.capture_screen(monitor_key)
                        if frame_data:
                            frame_data['monitor'] = monitor_key
                            config['frame_count'] += 1
                            socketio.emit('screen_frame', frame_data, room=f'monitor_{monitor_key}')
                        else:
                            logger.warning(f"No frame data captured for {monitor_key}")
                        time.sleep(1.0 / config['fps'])
                    except Exception as e:
                        logger.error(f"Cast loop error for {monitor_key}: {e}")
                        break
                config['is_casting'] = False
                config['last_webpage_image'] = None
                logger.info(f"Casting stopped for {monitor_key}")

            if not config['cast_thread'] or not config['cast_thread'].is_alive():
                config['cast_thread'] = threading.Thread(target=cast_loop)
                config['cast_thread'].daemon = True
                config['cast_thread'].start()
                logger.info(f"Started casting for {monitor_key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error starting casting for {monitor_key}: {e}")
            return False

    def stop_casting(self, monitor_key):
        """Stop casting for specific monitor"""
        try:
            if monitor_key in self.monitor_casters:
                self.monitor_casters[monitor_key]['is_casting'] = False
                self.monitor_casters[monitor_key]['last_webpage_image'] = None
                logger.info(f"Stopped casting for {monitor_key}")
        except Exception as e:
            logger.error(f"Error stopping casting for {monitor_key}: {e}")

    def update_settings(self, monitor_key, settings):
        """Update settings for specific monitor"""
        try:
            if monitor_key in self.monitor_casters:
                config = self.monitor_casters[monitor_key]
                config.update(settings)
                logger.info(f"Updated settings for {monitor_key}: {settings}")
        except Exception as e:
            logger.error(f"Error updating settings for {monitor_key}: {e}")

    def add_client(self, monitor_key, client_id):
        """Add client to monitor room"""
        try:
            if monitor_key in self.monitor_casters:
                self.monitor_casters[monitor_key]['connected_clients'].add(client_id)
                logger.info(f"Client {client_id} added to {monitor_key}")
        except Exception as e:
            logger.error(f"Error adding client to {monitor_key}: {e}")

    def remove_client(self, monitor_key, client_id):
        """Remove client from monitor room"""
        try:
            if monitor_key in self.monitor_casters:
                self.monitor_casters[monitor_key]['connected_clients'].discard(client_id)
                logger.info(f"Client {client_id} removed from {monitor_key}")
                if len(self.monitor_casters[monitor_key]['connected_clients']) == 0:
                    self.stop_casting(monitor_key)
        except Exception as e:
            logger.error(f"Error removing client from {monitor_key}: {e}")

    def cleanup(self):
        """Clean up resources on shutdown"""
        try:
            self.driver.quit()
            logger.info("Selenium WebDriver closed")
        except Exception as e:
            logger.error(f"Error closing WebDriver: {e}")

caster = MultiMonitorCaster()

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        logger.info(f"Local IP detected: {ip}")
        return ip
    except Exception as e:
        logger.warning(f"Could not detect local IP: {e}. Falling back to 'localhost'")
        return "localhost"

@app.route('/')
def home():
    try:
        logger.info("Accessing control panel at /")
        return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced LocalCast - Multi-Monitor Casting</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Arial', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        .monitor-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .monitor-panel {
            background: rgba(255,255,255,0.1);
            padding: 25px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 2px solid rgba(255,255,255,0.2);
        }
        
        .monitor1 { border-color: #ff6b6b; }
        .monitor2 { border-color: #4ecdc4; }
        .monitor3 { border-color: #a2e05b; }
        
        .monitor-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .monitor-title {
            font-size: 1.5em;
            font-weight: bold;
        }
        
        .monitor-status {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        
        .status-active { background: #4CAF50; }
        .status-inactive { background: #666; }
        
        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .control-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        
        .control-group label {
            font-weight: bold;
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        button {
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .btn-primary { background: linear-gradient(45deg, #4CAF50, #45a049); color: white; }
        .btn-danger { background: linear-gradient(45deg, #f44336, #d32f2f); color: white; }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        
        input, select {
            padding: 10px;
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 5px;
            background: rgba(255,255,255,0.1);
            color: white;
            backdrop-filter: blur(10px);
        }
        
        .preview-section {
            margin-top: 20px;
            padding: 15px;
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
        }
        
        .screen-preview {
            width: 100%;
            max-height: 200px;
            object-fit: contain;
            border-radius: 5px;
            display: none;
        }
        
        .no-preview {
            text-align: center;
            padding: 40px;
            opacity: 0.7;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 15px;
            font-size: 0.9em;
        }
        
        .stats div {
            text-align: center;
            padding: 5px;
            background: rgba(255,255,255,0.1);
            border-radius: 5px;
        }
        
        .viewer-links {
            margin-top: 15px;
            padding: 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 5px;
        }
        
        .viewer-links a {
            color: #fff;
            text-decoration: none;
            display: block;
            margin: 2px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🖥 Enhanced LocalCast</h1>
        <p>Multi-Monitor Screen Casting - Cast different webpages or screens to Monitor 1, Monitor 2, and Monitor 3</p>
    </div>
    
    <div class="monitor-grid">
        <!-- Monitor 1 Panel -->
        <div class="monitor-panel monitor1">
            <div class="monitor-header">
                <div class="monitor-title">🔴 Monitor 1</div>
                <div id="status1" class="monitor-status status-inactive">Inactive</div>
            </div>
            
            <div class="stats">
                <div>Clients: <span id="clients1">0</span></div>
                <div>FPS: <span id="fps1">0</span></div>
                <div>Frames: <span id="frames1">0</span></div>
            </div>
            
            <div class="controls">
                <div class="control-group">
                    <label>Content Source</label>
                    <select id="content1">
                        <option value="desktop">Desktop</option>
                        <option value="custom">Custom Screen</option>
                        <option value="webpage" selected>Webpage</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label>Source Monitor</label>
                    <select id="source-monitor1">
                        <option value="0">Primary Monitor</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label>Webpage URL</label>
                    <input type="text" id="webpage-url1" placeholder="e.g., https://example.com">
                </div>
                
                <div class="control-group">
                    <label>Quality</label>
                    <input type="range" id="quality1" min="10" max="100" value="80">
                    <span id="quality-display1">80%</span>
                </div>
                
                <div class="control-group">
                    <label>FPS</label>
                    <select id="fps-select1">
                        <option value="15">15 FPS</option>
                        <option value="24">24 FPS</option>
                        <option value="30" selected>30 FPS</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label>Scale</label>
                    <select id="scale1">
                        <option value="0.5">50%</option>
                        <option value="0.75">75%</option>
                        <option value="1.0" selected>100%</option>
                    </select>
                </div>
            </div>
            
            <div class="controls">
                <button id="start1" class="btn-primary">🚀 Start Monitor 1</button>
                <button id="stop1" class="btn-danger" disabled>⏹ Stop Monitor 1</button>
            </div>
            
            <div class="preview-section">
                <h4>Preview:</h4>
                <img id="preview1" class="screen-preview" alt="Monitor 1 Preview">
                <div id="no-preview1" class="no-preview">Click "Start Monitor 1" to begin casting</div>
            </div>
            
            <div class="viewer-links">
                <strong>Monitor 1 Viewer URLs:</strong>
                <a href="/viewer/monitor1" target="_blank" id="viewer-url1-local">Loading...</a>
                <a href="#" target="_blank" id="viewer-url1-network">Loading...</a>
            </div>
        </div>
        
        <!-- Monitor 2 Panel -->
        <div class="monitor-panel monitor2">
            <div class="monitor-header">
                <div class="monitor-title">🔵 Monitor 2</div>
                <div id="status2" class="monitor-status status-inactive">Inactive</div>
            </div>
            
            <div class="stats">
                <div>Clients: <span id="clients2">0</span></div>
                <div>FPS: <span id="fps2">0</span></div>
                <div>Frames: <span id="frames2">0</span></div>
            </div>
            
            <div class="controls">
                <div class="control-group">
                    <label>Content Source</label>
                    <select id="content2">
                        <option value="desktop">Desktop</option>
                        <option value="custom">Custom Screen</option>
                        <option value="webpage" selected>Webpage</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label>Source Monitor</label>
                    <select id="source-monitor2">
                        <option value="0">Primary Monitor</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label>Webpage URL</label>
                    <input type="text" id="webpage-url2" placeholder="e.g., https://news.com">
                </div>
                
                <div class="control-group">
                    <label>Quality</label>
                    <input type="range" id="quality2" min="10" max="100" value="80">
                    <span id="quality-display2">80%</span>
                </div>
                
                <div class="control-group">
                    <label>FPS</label>
                    <select id="fps-select2">
                        <option value="15">15 FPS</option>
                        <option value="24">24 FPS</option>
                        <option value="30" selected>30 FPS</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label>Scale</label>
                    <select id="scale2">
                        <option value="0.5">50%</option>
                        <option value="0.75">75%</option>
                        <option value="1.0" selected>100%</option>
                    </select>
                </div>
            </div>
            
            <div class="controls">
                <button id="start2" class="btn-primary">🚀 Start Monitor 2</button>
                <button id="stop2" class="btn-danger" disabled>⏹ Stop Monitor 2</button>
            </div>
            
            <div class="preview-section">
                <h4>Preview:</h4>
                <img id="preview2" class="screen-preview" alt="Monitor 2 Preview">
                <div id="no-preview2" class="no-preview">Click "Start Monitor 2" to begin casting</div>
            </div>
            
            <div class="viewer-links">
                <strong>Monitor 2 Viewer URLs:</strong>
                <a href="/viewer/monitor2" target="_blank" id="viewer-url2-local">Loading...</a>
                <a href="#" target="_blank" id="viewer-url2-network">Loading...</a>
            </div>
        </div>
        
        <!-- Monitor 3 Panel -->
        <div class="monitor-panel monitor3">
            <div class="monitor-header">
                <div class="monitor-title">🟢 Monitor 3</div>
                <div id="status3" class="monitor-status status-inactive">Inactive</div>
            </div>
            
            <div class="stats">
                <div>Clients: <span id="clients3">0</span></div>
                <div>FPS: <span id="fps3">0</span></div>
                <div>Frames: <span id="frames3">0</span></div>
            </div>
            
            <div class="controls">
                <div class="control-group">
                    <label>Content Source</label>
                    <select id="content3">
                        <option value="desktop">Desktop</option>
                        <option value="custom">Custom Screen</option>
                        <option value="webpage" selected>Webpage</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label>Source Monitor</label>
                    <select id="source-monitor3">
                        <option value="0">Primary Monitor</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label>Webpage URL</label>
                    <input type="text" id="webpage-url3" placeholder="e.g., https://wikipedia.org">
                </div>
                
                <div class="control-group">
                    <label>Quality</label>
                    <input type="range" id="quality3" min="10" max="100" value="80">
                    <span id="quality-display3">80%</span>
                </div>
                
                <div class="control-group">
                    <label>FPS</label>
                    <select id="fps-select3">
                        <option value="15">15 FPS</option>
                        <option value="24">24 FPS</option>
                        <option value="30" selected>30 FPS</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label>Scale</label>
                    <select id="scale3">
                        <option value="0.5">50%</option>
                        <option value="0.75">75%</option>
                        <option value="1.0" selected>100%</option>
                    </select>
                </div>
            </div>
            
            <div class="controls">
                <button id="start3" class="btn-primary">🚀 Start Monitor 3</button>
                <button id="stop3" class="btn-danger" disabled>⏹ Stop Monitor 3</button>
            </div>
            
            <div class="preview-section">
                <h4>Preview:</h4>
                <img id="preview3" class="screen-preview" alt="Monitor 3 Preview">
                <div id="no-preview3" class="no-preview">Click "Start Monitor 3" to begin casting</div>
            </div>
            
            <div class="viewer-links">
                <strong>Monitor 3 Viewer URLs:</strong>
                <a href="/viewer/monitor3" target="_blank" id="viewer-url3-local">Loading...</a>
                <a href="#" target="_blank" id="viewer-url3-network">Loading...</a>
            </div>
        </div>
    </div>
    
    <script>
        const socket = io({transports: ['websocket', 'polling']});
        let localIP = 'localhost';
        
        socket.on('connect', () => {
            console.log('Connected to server');
            loadMonitors();
            updateNetworkInfo();
        });
        
        socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
        });
        
        const monitors = ['monitor1', 'monitor2', 'monitor3'];
        
        monitors.forEach(monitor => {
            const num = monitor.slice(-1);
            
            socket.on('screen_frame', (data) => {
                if (data.monitor === monitor) {
                    const preview = document.getElementById(`preview${num}`);
                    const noPreview = document.getElementById(`no-preview${num}`);
                    preview.src = data.image;
                    preview.style.display = 'block';
                    noPreview.style.display = 'none';
                    document.getElementById(`frames${num}`).textContent = 
                        parseInt(document.getElementById(`frames${num}`).textContent) + 1;
                }
            });
            
            socket.on(`client_count_${monitor}`, (count) => {
                document.getElementById(`clients${num}`).textContent = count;
            });
            
            socket.on('cast_status', (status) => {
                if (status.monitor === monitor) {
                    if (status.is_casting) {
                        document.getElementById(`status${num}`).textContent = 'Active';
                        document.getElementById(`status${num}`).className = 'monitor-status status-active';
                    } else {
                        document.getElementById(`status${num}`).textContent = 'Inactive';
                        document.getElementById(`status${num}`).className = 'monitor-status status-inactive';
                        document.getElementById(`preview${num}`).style.display = 'none';
                        document.getElementById(`no-preview${num}`).style.display = 'block';
                    }
                }
            });
            
            document.getElementById(`start${num}`).addEventListener('click', () => {
                const settings = {
                    quality: parseInt(document.getElementById(`quality${num}`).value),
                    fps: parseInt(document.getElementById(`fps-select${num}`).value),
                    scale: parseFloat(document.getElementById(`scale${num}`).value),
                    source_monitor: parseInt(document.getElementById(`source-monitor${num}`).value),
                    screen_content: document.getElementById(`content${num}`).value,
                    webpage_url: document.getElementById(`webpage-url${num}`).value
                };
                
                socket.emit('start_cast', { monitor, settings });
                socket.emit('join_monitor', monitor);
                
                document.getElementById(`start${num}`).disabled = true;
                document.getElementById(`stop${num}`).disabled = false;
                document.getElementById(`status${num}`).textContent = 'Active';
                document.getElementById(`status${num}`).className = 'monitor-status status-active';
            });
            
            document.getElementById(`stop${num}`).addEventListener('click', () => {
                socket.emit('stop_cast', monitor);
                socket.emit('leave_monitor', monitor);
                
                document.getElementById(`start${num}`).disabled = false;
                document.getElementById(`stop${num}`).disabled = true;
                document.getElementById(`status${num}`).textContent = 'Inactive';
                document.getElementById(`status${num}`).className = 'monitor-status status-inactive';
                
                document.getElementById(`preview${num}`).style.display = 'none';
                document.getElementById(`no-preview${num}`).style.display = 'block';
            });
            
            document.getElementById(`quality${num}`).addEventListener('input', (e) => {
                document.getElementById(`quality-display${num}`).textContent = e.target.value + '%';
            });
        });
        
        function loadMonitors() {
            fetch('/api/monitors')
                .then(response => response.json())
                .then(monitors => {
                    ['1', '2', '3'].forEach(num => {
                        const select = document.getElementById(`source-monitor${num}`);
                        select.innerHTML = '';
                        monitors.forEach((monitor, index) => {
                            const option = document.createElement('option');
                            option.value = monitor.id;
                            option.textContent = `Monitor ${monitor.id} (${monitor.width}x${monitor.height})`;
                            select.appendChild(option);
                            if (num === '1' && index === 0) select.value = monitor.id;
                            if (num === '2' && index === 1) select.value = monitor.id;
                            if (num === '3' && index === 2) select.value = monitor.id;
                        });
                    });
                })
                .catch(error => console.error('Error loading monitors:', error));
        }
        
        function updateNetworkInfo() {
            fetch('/api/network-info')
                .then(response => response.json())
                .then(data => {
                    localIP = data.local_ip;
                    ['1', '2', '3'].forEach(num => {
                        document.getElementById(`viewer-url${num}-local`).href = `http://localhost:5000/viewer/monitor${num}`;
                        document.getElementById(`viewer-url${num}-local`).textContent = `http://localhost:5000/viewer/monitor${num}`;
                        document.getElementById(`viewer-url${num}-network`).href = `http://${localIP}:5000/viewer/monitor${num}`;
                        document.getElementById(`viewer-url${num}-network`).textContent = `http://${localIP}:5000/viewer/monitor${num}`;
                    });
                })
                .catch(error => console.error('Error updating network info:', error));
        }
    </script>
</body>
</html>
        ''')
    except Exception as e:
        logger.error(f"Error in home route: {e}")
        return f"Internal Server Error: {str(e)}", 500

@app.route('/viewer/<monitor_key>')
def viewer(monitor_key):
    try:
        if monitor_key not in ['monitor1', 'monitor2', 'monitor3']:
            logger.error(f"Invalid monitor key: {monitor_key}")
            return "Invalid monitor key. Please check the URL.", 404
        monitor_name = f"Monitor {monitor_key[-1]}"
        monitor_color = {
            'monitor1': '#ff6b6b',
            'monitor2': '#4ecdc4',
            'monitor3': '#a2e05b'
        }[monitor_key]
        logger.info(f"Viewer accessed for {monitor_key}")
        return render_template_string(f'''
<!DOCTYPE html>
<html>
<head>
    <title>LocalCast Viewer - {monitor_name}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            background: #000; 
            overflow: hidden; 
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            font-family: Arial, sans-serif;
        }}
        
        .viewer-container {{
            position: relative;
            width: 100%;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        
        .screen-display {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            border: 3px solid {monitor_color};
            border-radius: 10px;
            box-shadow: 0 0 30px {monitor_color}40;
        }}
        
        .controls {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.9);
            padding: 15px;
            border-radius: 10px;
            color: white;
            z-index: 1000;
            backdrop-filter: blur(10px);
            border: 2px solid {monitor_color};
        }}
        
        .controls button {{
            background: {monitor_color};
            border: none;
            color: white;
            padding: 8px 12px;
            margin: 2px;
            border-radius: 5px;
            cursor: pointer;
        }}
        
        .controls button:hover {{
            opacity: 0.8;
        }}
        
        .status {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(0,0,0,0.9);
            padding: 15px;
            border-radius: 10px;
            color: white;
            font-size: 12px;
            backdrop-filter: blur(10px);
            border: 2px solid {monitor_color};
        }}
        
        .no-signal {{
            color: #888;
            text-align: center;
            font-size: 18px;
        }}
        
        .loading {{
            color: #fff;
            text-align: center;
            font-size: 16px;
        }}
    </style>
</head>
<body>
    <div class="viewer-container">
        <img id="screen-display" class="screen-display" style="display: none;" alt="{monitor_name} Cast">
        <div id="loading" class="loading">📡 Connecting to {monitor_name}...</div>
        <div id="no-signal" class="no-signal" style="display: none;">
            📺 No active cast on {monitor_name}<br>
            <small>Start casting from the control panel or check logs for errors</small>
        </div>
    </div>
    
    <div class="controls">
        <div style="margin-bottom: 10px;">
            <strong>🖥 {monitor_name} Viewer</strong>
        </div>
        <button onclick="toggleFullscreen()">⛶ Fullscreen</button>
        <button onclick="refreshConnection()">🔄 Refresh</button>
        <button onclick="window.close()">✕ Close</button>
    </div>
    
    <div class="status">
        <div><strong>{monitor_name}</strong></div>
        <div>Status: <span id="connection-status">Connecting...</span></div>
        <div>FPS: <span id="fps-counter">0</span></div>
        <div>Quality: <span id="quality-info">Unknown</span></div>
    </div>
    
    <script>
        const socket = io({{transports: ['websocket', 'polling']}});
        const screenDisplay = document.getElementById('screen-display');
        const loadingDiv = document.getElementById('loading');
        const noSignalDiv = document.getElementById('no-signal');
        const monitorKey = '{monitor_key}';
        
        let frameCount = 0;
        let lastFrameTime = Date.now();
        let isFullscreen = false;
        
        socket.on('connect', () => {{
            document.getElementById('connection-status').textContent = 'Connected';
            loadingDiv.style.display = 'none';
            socket.emit('join_monitor', monitorKey);
        }});
        
        socket.on('connect_error', (error) => {{
            console.error('Connection error:', error);
            document.getElementById('connection-status').textContent = 'Connection Failed';
        }});
        
        socket.on('disconnect', () => {{
            document.getElementById('connection-status').textContent = 'Disconnected';
            screenDisplay.style.display = 'none';
            loadingDiv.style.display = 'block';
            noSignalDiv.style.display = 'none';
        }});
        
        socket.on('screen_frame', (data) => {{
            if (data.monitor === monitorKey) {{
                screenDisplay.src = data.image;
                screenDisplay.style.display = 'block';
                loadingDiv.style.display = 'none';
                noSignalDiv.style.display = 'none';
                
                frameCount++;
                const now = Date.now();
                if (now - lastFrameTime >= 1000) {{
                    document.getElementById('fps-counter').textContent = frameCount;
                    frameCount = 0;
                    lastFrameTime = now;
                }}
                
                document.getElementById('quality-info').textContent = '{caster.monitor_casters[monitor_key]["quality"]}%';
            }}
        }});
        
        socket.on('cast_status', (status) => {{
            if (status.monitor === monitorKey) {{
                if (!status.is_casting) {{
                    screenDisplay.style.display = 'none';
                    loadingDiv.style.display = 'none';
                    noSignalDiv.style.display = 'block';
                    document.getElementById('connection-status').textContent = 'No Active Cast';
                    document.getElementById('fps-counter').textContent = '0';
                }} else {{
                    document.getElementById('connection-status').textContent = 'Active';
                }}
            }}
        }});
        
        function toggleFullscreen() {{
            if (!isFullscreen) {{
                if (document.documentElement.requestFullscreen) {{
                    document.documentElement.requestFullscreen();
                }} else if (document.documentElement.webkitRequestFullscreen) {{
                    document.documentElement.webkitRequestFullscreen();
                }}
                isFullscreen = true;
            }} else {{
                if (document.exitFullscreen) {{
                    document.exitFullscreen();
                }} else if (document.webkitExitFullscreen) {{
                    document.webkitExitFullscreen();
                }}
                isFullscreen = false;
            }}
        }}
        
        function refreshConnection() {{
            socket.disconnect();
            socket.connect();
            screenDisplay.style.display = 'none';
            loadingDiv.style.display = 'block';
            noSignalDiv.style.display = 'none';
            document.getElementById('connection-status').textContent = 'Connecting...';
            document.getElementById('fps-counter').textContent = '0';
        }}
        
        window.addEventListener('resize', () => {{
            screenDisplay.style.maxWidth = '100%';
            screenDisplay.style.maxHeight = '100%';
        }});
        
        window.addEventListener('beforeunload', () => {{
            socket.emit('leave_monitor', monitorKey);
            socket.disconnect();
        }});
        
        socket.emit('join_monitor', monitorKey);
    </script>
</body>
</html>
        ''')
    except Exception as e:
        logger.error(f"Error in viewer route for {monitor_key}: {e}")
        return f"Internal Server Error: {str(e)}", 500

@app.route('/api/network-info')
def network_info():
    try:
        logger.info("Fetching network info")
        return jsonify({
            'local_ip': get_local_ip(),
            'port': 5000
        })
    except Exception as e:
        logger.error(f"Error in network-info route: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitors')
def api_monitors():
    try:
        logger.info("Fetching available monitors")
        return jsonify(caster.get_monitors())
    except Exception as e:
        logger.error(f"Error in monitors route: {e}")
        return jsonify({'error': str(e)}), 500

@socketio.on('join_monitor')
def handle_join_monitor(monitor_key):
    try:
        if monitor_key in caster.monitor_casters:
            client_id = request.sid
            join_room(f'monitor_{monitor_key}')
            caster.add_client(monitor_key, client_id)
            emit('client_count_' + monitor_key, len(caster.monitor_casters[monitor_key]['connected_clients']), room=f'monitor_{monitor_key}')
            emit('cast_status', {'is_casting': caster.monitor_casters[monitor_key]['is_casting'], 'monitor': monitor_key}, to=client_id)
            logger.info(f"Client {client_id} joined monitor {monitor_key}")
    except Exception as e:
        logger.error(f"Error in join_monitor for {monitor_key}: {e}")

@socketio.on('leave_monitor')
def handle_leave_monitor(monitor_key):
    try:
        if monitor_key in caster.monitor_casters:
            client_id = request.sid
            leave_room(f'monitor_{monitor_key}')
            caster.remove_client(monitor_key, client_id)
            emit('client_count_' + monitor_key, len(caster.monitor_casters[monitor_key]['connected_clients']), room=f'monitor_{monitor_key}')
            logger.info(f"Client {client_id} left monitor {monitor_key}")
    except Exception as e:
        logger.error(f"Error in leave_monitor for {monitor_key}: {e}")

@socketio.on('start_cast')
def handle_start_cast(data):
    try:
        monitor_key = data['monitor']
        if monitor_key in caster.monitor_casters:
            settings = data.get('settings', {})
            caster.update_settings(monitor_key, settings)
            if caster.start_casting(monitor_key):
                emit('cast_status', {'is_casting': True, 'monitor': monitor_key}, room=f'monitor_{monitor_key}')
    except Exception as e:
        logger.error(f"Error in start_cast for {monitor_key}: {e}")

@socketio.on('stop_cast')
def handle_stop_cast(monitor_key):
    try:
        if monitor_key in caster.monitor_casters:
            caster.stop_casting(monitor_key)
            emit('cast_status', {'is_casting': False, 'monitor': monitor_key}, room=f'monitor_{monitor_key}')
    except Exception as e:
        logger.error(f"Error in stop_cast for {monitor_key}: {e}")

@app.route('/some_endpoint', methods=['POST'])
def some_func():
    try:
        data: Optional[Dict[Any, Any]] = request.get_json(silent=True)
        if data is None:
            logger.error("No valid JSON data provided in request")
            return jsonify({'error': 'No valid JSON data provided'}), 400
        logger.info(f"Received data at /some_endpoint: {data}")
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        logger.error(f"Error in some_endpoint: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    local_ip = get_local_ip()
    print("🖥 Enhanced LocalCast - Multi-Monitor Screen Casting Server")
    print("=" * 70)
    print(f"🌐 Server starting on:")
    print(f"   • Local: http://localhost:5000")
    print(f"   • Network: http://{local_ip}:5000")
    print(f"📱 Viewer URLs:")
    print(f"   • Monitor 1 Local: http://localhost:5000/viewer/monitor1")
    print(f"   • Monitor 1 Network: http://{local_ip}:5000/viewer/monitor1")
    print(f"   • Monitor 2 Local: http://localhost:5000/viewer/monitor2")
    print(f"   • Monitor 2 Network: http://{local_ip}:5000/viewer/monitor2")
    print(f"   • Monitor 3 Local: http://localhost:5000/viewer/monitor3")
    print(f"   • Monitor 3 Network: http://{local_ip}:5000/viewer/monitor3")
    print("=" * 70)
    print("\n📋 Setup Instructions:")
    print("1. Install dependencies: pip install flask flask-socketio pillow mss selenium")
    print("2. Install Chrome and ChromeDriver (ensure versions match)")
    print("3. Run the server: python -u localcast.py")
    print("4. Open the control panel: http://localhost:5000")
    print("5. For each monitor, select 'Webpage' and enter the URL (e.g., https://example.com)")
    print("6. Click 'Start Monitor X' to lock and stream the webpage to the viewer")
    print("7. Access viewer URLs on other devices to view the streams")
    print("8. Check terminal and localcast.log for errors if webpages don't load")
    print("   Logs now include file path and line number for easier debugging")
    print("\n🎯 Key Features:")
    print("• Stream different webpages to Monitors 1, 2, and 3")
    print("• Webpages are locked to each viewer during casting")
    print("• Support for desktop, custom content, and webpage streaming")
    print("• Adjustable quality, FPS, and scaling")
    print("• Fullscreen viewer mode with controls")
    print("• Automatic network discovery")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
        caster.cleanup()
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        caster.cleanup()