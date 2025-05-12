"""
Test server to verify network connectivity issues
"""

import socket
import http.server
import socketserver
import threading
import time
import webbrowser

def check_port_binding():
    try:
        # Try to bind to the port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 8060))
        s.close()
        return True
    except:
        return False

def simple_http_server():
    # Create a very basic HTTP server
    class SimpleHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test Server</title>
            </head>
            <body>
                <h1>Test Server is Working!</h1>
                <p>If you can see this page, the HTTP server is working correctly.</p>
            </body>
            </html>
            """)
            print("Someone connected to the server!")
    
    # Try different host addresses
    port = 8060
    handlers = [
        ('127.0.0.1', port),
        ('localhost', port),
        ('0.0.0.0', port)
    ]
    
    # Try each handler configuration
    for host, port in handlers:
        try:
            # Try to start with this configuration
            print(f"\nAttempting to start server on {host}:{port}")
            
            with socketserver.TCPServer((host, port), SimpleHandler) as httpd:
                print(f"Server started successfully on {host}:{port}")
                print(f"Try opening: http://{host}:{port}")
                print("Press Ctrl+C to stop the server")
                httpd.serve_forever()
                
        except Exception as e:
            print(f"Failed to start server on {host}:{port}: {e}")
            continue

if __name__ == "__main__":
    print("Testing network connectivity...")
    
    # Check if we can bind to the port
    if check_port_binding():
        print("Port binding test passed - port 8060 is available")
    else:
        print("Port binding test failed - port 8060 is already in use!")
    
    # Try to open a browser automatically (may not work in all environments)
    try:
        # Start the server in a separate thread so we can open the browser
        threading.Thread(target=lambda: time.sleep(1) and webbrowser.open("http://127.0.0.1:8060")).start()
    except:
        pass
    
    # Start the server
    simple_http_server()