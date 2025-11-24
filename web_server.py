"""
Simple web server to display parsed Suntech messages
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from typing import List, Dict, Any
import threading
import os
from datetime import datetime


def make_handler(message_store: List[Dict[str, Any]], beacon_scan_store: List[Dict[str, Any]], log_dir: str = None):
    """Factory function to create handler class with message_store and beacon_scan_store"""
    class MessageHandler(BaseHTTPRequestHandler):
        """HTTP request handler for serving parsed messages"""
        
        def do_GET(self):
            """Handle GET requests"""
            # Handle log file requests
            if self.path.startswith('/api/logs'):
                self._handle_log_requests()
                return
            
            if self.path == '/' or self.path == '/index.html':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                # Get the directory where this script is located
                script_dir = os.path.dirname(os.path.abspath(__file__))
                html_path = os.path.join(script_dir, 'templates', 'index.html')
                
                # Read and serve the HTML file
                try:
                    with open(html_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    try:
                        self.wfile.write(html_content.encode('utf-8'))
                    except (BrokenPipeError, OSError):
                        # Client disconnected before response was sent - ignore
                        pass
                except FileNotFoundError:
                    try:
                        self.wfile.write(b'<html><body><h1>Error: index.html not found</h1></body></html>')
                    except (BrokenPipeError, OSError):
                        pass
            
            elif self.path == '/table.html' or self.path == '/table.index':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                # Get the directory where this script is located
                script_dir = os.path.dirname(os.path.abspath(__file__))
                html_path = os.path.join(script_dir, 'templates', 'table.html')
                
                # Read and serve the HTML file
                try:
                    with open(html_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    try:
                        self.wfile.write(html_content.encode('utf-8'))
                    except (BrokenPipeError, OSError):
                        # Client disconnected before response was sent - ignore
                        pass
                except FileNotFoundError:
                    try:
                        self.wfile.write(b'<html><body><h1>Error: table.html not found</h1></body></html>')
                    except (BrokenPipeError, OSError):
                        pass
            
            elif self.path == '/api/messages':
                # API endpoint to get messages as JSON
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # Get messages (thread-safe)
                messages = list(message_store)
                try:
                    self.wfile.write(json.dumps(messages, indent=2).encode('utf-8'))
                except (BrokenPipeError, OSError):
                    # Client disconnected before response was sent - ignore
                    pass
            
            elif self.path == '/api/beacon-scans':
                # API endpoint to get beacon scans as JSON
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # Get beacon scans (thread-safe)
                scans = list(beacon_scan_store)
                try:
                    self.wfile.write(json.dumps(scans, indent=2).encode('utf-8'))
                except (BrokenPipeError, OSError):
                    # Client disconnected before response was sent - ignore
                    pass
            
            else:
                self.send_response(404)
                self.end_headers()
                try:
                    self.wfile.write(b'Not Found')
                except (BrokenPipeError, OSError):
                    # Client disconnected before response was sent - ignore
                    pass
        
        def _handle_log_requests(self):
            """Handle log file viewing requests"""
            script_dir = os.path.dirname(os.path.abspath(__file__))
            log_directory = log_dir or os.path.join(script_dir, 'logs')
            
            try:
                if self.path == '/api/logs/list':
                    # List all log files
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    log_files = []
                    if os.path.exists(log_directory):
                        for filename in sorted(os.listdir(log_directory), reverse=True):
                            if filename.endswith('.log'):
                                filepath = os.path.join(log_directory, filename)
                                file_size = os.path.getsize(filepath)
                                mod_time = os.path.getmtime(filepath)
                                log_files.append({
                                    'filename': filename,
                                    'size': file_size,
                                    'modified': datetime.fromtimestamp(mod_time).isoformat()
                                })
                    
                    try:
                        self.wfile.write(json.dumps(log_files, indent=2).encode('utf-8'))
                    except (BrokenPipeError, OSError):
                        # Client disconnected before response was sent - ignore
                        pass
                
                elif self.path.startswith('/api/logs/view/'):
                    # View a specific log file
                    filename = self.path.replace('/api/logs/view/', '')
                    # Security: only allow .log files and prevent directory traversal
                    if not filename.endswith('.log') or '..' in filename or '/' in filename:
                        self.send_response(400)
                        self.end_headers()
                        try:
                            self.wfile.write(b'Invalid filename')
                        except (BrokenPipeError, OSError):
                            pass
                        return
                    
                    filepath = os.path.join(log_directory, filename)
                    if os.path.exists(filepath) and os.path.isfile(filepath):
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        
                        # Read and return log file content
                        log_entries = []
                        with open(filepath, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    try:
                                        log_entries.append(json.loads(line))
                                    except json.JSONDecodeError:
                                        # If not JSON, add as raw text
                                        log_entries.append({'raw': line})
                        
                        try:
                            self.wfile.write(json.dumps(log_entries, indent=2).encode('utf-8'))
                        except (BrokenPipeError, OSError):
                            # Client disconnected before response was sent - ignore
                            pass
                    else:
                        self.send_response(404)
                        self.end_headers()
                        try:
                            self.wfile.write(b'Log file not found')
                        except (BrokenPipeError, OSError):
                            pass
                else:
                    self.send_response(404)
                    self.end_headers()
                    try:
                        self.wfile.write(b'Not Found')
                    except (BrokenPipeError, OSError):
                        pass
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                try:
                    self.wfile.write(f'Error: {str(e)}'.encode('utf-8'))
                except (BrokenPipeError, OSError):
                    pass
        
        def log_message(self, format, *args):
            """Override to reduce logging noise"""
            pass
    
    return MessageHandler


class WebServer:
    """Simple web server for displaying parsed messages"""
    
    def __init__(self, port: int, message_store: List[Dict[str, Any]], beacon_scan_store: List[Dict[str, Any]]):
        self.port = port
        self.message_store = message_store
        self.beacon_scan_store = beacon_scan_store
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the web server in a separate thread"""
        # Get log directory from server if available
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(script_dir, 'logs')
        handler_class = make_handler(self.message_store, self.beacon_scan_store, log_dir)
        self.server = HTTPServer(('', self.port), handler_class)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        print(f"Web server started on http://localhost:{self.port}")
        print(f"  - Main page: http://localhost:{self.port}/")
        print(f"  - Beacon table: http://localhost:{self.port}/table.html (or /table.index)")
        print(f"  - Log files directory: {log_dir}")
    
    def stop(self):
        """Stop the web server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()


if __name__ == "__main__":
    # For testing
    message_store = []
    beacon_scan_store = []
    web_server = WebServer(8080, message_store, beacon_scan_store)
    web_server.start()
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        web_server.stop()

