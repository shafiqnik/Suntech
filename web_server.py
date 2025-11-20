"""
Simple web server to display parsed Suntech messages
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from typing import List, Dict, Any
import threading
import os


def make_handler(message_store: List[Dict[str, Any]], beacon_scan_store: List[Dict[str, Any]]):
    """Factory function to create handler class with message_store and beacon_scan_store"""
    class MessageHandler(BaseHTTPRequestHandler):
        """HTTP request handler for serving parsed messages"""
        
        def do_GET(self):
            """Handle GET requests"""
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
                    self.wfile.write(html_content.encode('utf-8'))
                except FileNotFoundError:
                    self.wfile.write(b'<html><body><h1>Error: index.html not found</h1></body></html>')
            
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
                    self.wfile.write(html_content.encode('utf-8'))
                except FileNotFoundError:
                    self.wfile.write(b'<html><body><h1>Error: table.html not found</h1></body></html>')
            
            elif self.path == '/api/messages':
                # API endpoint to get messages as JSON
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # Get messages (thread-safe)
                messages = list(message_store)
                self.wfile.write(json.dumps(messages, indent=2).encode('utf-8'))
            
            elif self.path == '/api/beacon-scans':
                # API endpoint to get beacon scans as JSON
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # Get beacon scans (thread-safe)
                scans = list(beacon_scan_store)
                self.wfile.write(json.dumps(scans, indent=2).encode('utf-8'))
            
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Not Found')
        
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
        handler_class = make_handler(self.message_store, self.beacon_scan_store)
        self.server = HTTPServer(('', self.port), handler_class)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        print(f"Web server started on http://localhost:{self.port}")
        print(f"  - Main page: http://localhost:{self.port}/")
        print(f"  - Beacon table: http://localhost:{self.port}/table.html (or /table.index)")
    
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

