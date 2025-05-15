"""
ChiX - Professional VS Code-inspired C Code Editor
Main entry point for the application
"""

import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket

# Ensure the correct working directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chix.app import ChiXApp

# Simple HTTP server that confirms our application is running
class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>ChiX Editor</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    line-height: 1.6;
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                }
                h1 {
                    color: #0078d7;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #252526;
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.3);
                }
                .feature {
                    margin-bottom: 20px;
                }
                .status {
                    color: #5cb85c;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>ChiX Editor</h1>
                <p class="status">Editor is running</p>
                <p>ChiX is a professional VS Code-inspired C code editor with advanced features.</p>
                
                <div class="feature">
                    <h2>Features</h2>
                    <ul>
                        <li>Syntax highlighting for C code</li>
                        <li>Code intelligence and suggestions</li>
                        <li>Integrated compiler and debugger</li>
                        <li>Multi-file project support</li>
                        <li>Modern UI with themes</li>
                    </ul>
                </div>
                
                <p>The editor is running in desktop mode. This page confirms the service is active.</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))

def start_server():
    # Find an available port, with preference for 5000
    port = 5000
    server_address = ('0.0.0.0', port)
    
    try:
        httpd = HTTPServer(server_address, StatusHandler)
        print(f"Starting HTTP server on port {port}")
        httpd.serve_forever()
    except:
        print(f"Could not start server on port {port}")

if __name__ == "__main__":
    # Start the HTTP server in a separate thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Start the ChiX Editor app in the main thread
    app = ChiXApp()
    app.start()
