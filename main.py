"""
Main application entry point for Suntech message parser
Starts both the socket server (port 18160) and web server (port 8080)
"""
import threading
import signal
import sys
from server import ThreadedServer
from web_server import WebServer


def main():
    """Main application entry point"""
    # Shared message store
    message_store = []
    
    # Create and start socket server on port 18160
    socket_server = ThreadedServer('', 18160, message_store)
    socket_thread = threading.Thread(target=socket_server.listen, daemon=True)
    socket_thread.start()
    print("✓ Socket server started on port 18160")
    
    # Create and start web server on port 8080
    web_server = WebServer(8080, message_store)
    web_server.start()
    print("✓ Web server started on http://localhost:8080")
    print("\n" + "="*60)
    print("Suntech Message Parser is running!")
    print("="*60)
    print("Socket Server: Listening on port 18160")
    print("Web Interface: http://localhost:8080")
    print("="*60)
    print("\nPress Ctrl+C to stop...\n")
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\n\nShutting down...")
        web_server.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Keep main thread alive
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()

