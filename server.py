#!/usr/bin/env python3
"""
Multi-threaded HTTP Server
A high-performance HTTP server built from scratch using socket programming.

Features:
- Multi-threaded request handling with thread pool
- Binary file transfer support (PNG, JPEG, TXT)
- JSON POST request processing
- Security features (path traversal protection, host validation)
- Connection keep-alive support
- Comprehensive logging

Author: Socket Programming Assignment
"""

import socket
import threading
import os
import sys
import json
import time
import re
import logging
from datetime import datetime
from urllib.parse import unquote
from queue import Queue, Empty
import mimetypes
import hashlib
import random
from pathlib import Path


class HTTPServer:
    """Multi-threaded HTTP Server implementation"""
    
    def __init__(self, host='127.0.0.1', port=8080, max_threads=10):
        """Initialize the HTTP server"""
        self.host = host
        self.port = port
        self.max_threads = max_threads
        self.server_socket = None
        self.running = False
        
        # Thread pool management
        self.thread_pool = []
        self.connection_queue = Queue()
        self.active_connections = 0
        self.connections_lock = threading.Lock()
        
        # Server info
        self.server_name = "Multi-threaded HTTP Server"
        self.resources_dir = os.path.join(os.path.dirname(__file__), 'resources')
        self.uploads_dir = os.path.join(self.resources_dir, 'uploads')
        
        # Ensure directories exist
        os.makedirs(self.uploads_dir, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Configure comprehensive logging"""
        # Create logger
        self.logger = logging.getLogger('HTTPServer')
        self.logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '[%(asctime)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
    
    def log(self, message, thread_name=None):
        """Thread-safe logging method"""
        if thread_name:
            self.logger.info(f"[{thread_name}] {message}")
        else:
            self.logger.info(message)
    
    def start(self):
        """Start the HTTP server"""
        try:
            # Create socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind and listen
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(50)  # Queue size of 50 as specified
            
            self.running = True
            
            # Log startup
            self.log(f"HTTP Server started on http://{self.host}:{self.port}")
            self.log(f"Thread pool size: {self.max_threads}")
            self.log(f"Serving files from '{self.resources_dir}' directory")
            self.log("Press Ctrl+C to stop the server")
            
            # Start worker threads
            self.start_thread_pool()
            
            # Accept connections
            self.accept_connections()
            
        except KeyboardInterrupt:
            self.log("Server shutdown requested")
        except Exception as e:
            self.log(f"Server error: {e}")
        finally:
            self.stop()
    
    def start_thread_pool(self):
        """Initialize the worker thread pool"""
        for i in range(self.max_threads):
            thread = threading.Thread(
                target=self.worker_thread, 
                name=f"Thread-{i+1}",
                daemon=True
            )
            thread.start()
            self.thread_pool.append(thread)
            
        self.log(f"Started {self.max_threads} worker threads")
    
    def worker_thread(self):
        """Worker thread that processes client connections"""
        thread_name = threading.current_thread().name
        
        while self.running:
            try:
                # Get connection from queue (timeout to check running status)
                client_socket, client_address = self.connection_queue.get(timeout=1)
                
                if client_socket is None:  # Shutdown signal
                    break
                
                with self.connections_lock:
                    self.active_connections += 1
                
                self.log(f"Connection from {client_address[0]}:{client_address[1]}", thread_name)
                
                # Handle the connection with keep-alive support
                self.handle_client_connection(client_socket, client_address, thread_name)
                
            except Empty:
                # Queue timeout - continue to check running status
                continue
            except Exception as e:
                self.log(f"Worker thread error: {e}", thread_name)
            finally:
                with self.connections_lock:
                    if self.active_connections > 0:
                        self.active_connections -= 1
    
    def accept_connections(self):
        """Accept incoming client connections"""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                
                # Check if thread pool is saturated
                if self.connection_queue.qsize() >= self.max_threads * 2:
                    self.log("Warning: Thread pool saturated, queuing connection")
                
                # Add connection to queue
                self.connection_queue.put((client_socket, client_address))
                
            except socket.error as e:
                if self.running:
                    self.log(f"Accept error: {e}")
                break
    
    def handle_client_connection(self, client_socket, client_address, thread_name):
        """Handle a client connection with keep-alive support"""
        connection_count = 0
        max_requests = 100  # Maximum requests per connection
        
        try:
            client_socket.settimeout(30)  # 30 second timeout
            
            while connection_count < max_requests and self.running:
                try:
                    # Receive request
                    request_data = self.receive_request(client_socket)
                    if not request_data:
                        break  # Client closed connection
                    
                    connection_count += 1
                    
                    # Parse request
                    request = self.parse_request(request_data)
                    if not request:
                        self.send_error_response(client_socket, 400, "Bad Request")
                        break
                    
                    # Log request
                    self.log(f"Request: {request['method']} {request['path']} {request['version']}", thread_name)
                    
                    # Validate host header (security requirement)
                    if not self.validate_host_header(request, client_socket, thread_name):
                        break
                    
                    # Handle the request
                    keep_alive = self.handle_request(request, client_socket, thread_name, connection_count, max_requests)
                    
                    if not keep_alive:
                        break
                        
                except socket.timeout:
                    self.log(f"Connection timeout", thread_name)
                    break
                except ConnectionResetError:
                    self.log(f"Client disconnected", thread_name)
                    break
                except Exception as e:
                    self.log(f"Request handling error: {e}", thread_name)
                    try:
                        self.send_error_response(client_socket, 500, "Internal Server Error")
                    except:
                        pass
                    break
        
        finally:
            try:
                client_socket.close()
                self.log(f"Connection closed ({connection_count} requests served)", thread_name)
            except:
                pass
    
    def receive_request(self, client_socket):
        """Receive and parse HTTP request data"""
        request_data = b""
        
        while True:
            try:
                # Receive data in chunks
                chunk = client_socket.recv(8192)
                if not chunk:
                    break
                
                request_data += chunk
                
                # Check if we have received the full headers
                if b'\r\n\r\n' in request_data:
                    # Split headers and body
                    headers_end = request_data.find(b'\r\n\r\n')
                    headers = request_data[:headers_end + 4]
                    body_received = request_data[headers_end + 4:]
                    
                    # Check if we need to receive more body data
                    headers_str = headers.decode('utf-8', errors='ignore')
                    content_length = self.extract_content_length(headers_str)
                    
                    if content_length > 0:
                        # Receive remaining body data
                        while len(body_received) < content_length:
                            remaining = content_length - len(body_received)
                            chunk = client_socket.recv(min(remaining, 8192))
                            if not chunk:
                                break
                            body_received += chunk
                    
                    return headers + body_received
                
                # Prevent oversized requests
                if len(request_data) > 8192 + 1024*1024:  # 8KB headers + 1MB body max
                    break
                    
            except socket.timeout:
                break
            except Exception:
                break
        
        return request_data if request_data else None
    
    def extract_content_length(self, headers_str):
        """Extract Content-Length from headers"""
        try:
            for line in headers_str.split('\r\n'):
                if line.lower().startswith('content-length:'):
                    return int(line.split(':', 1)[1].strip())
        except:
            pass
        return 0
    
    def parse_request(self, request_data):
        """Parse HTTP request and return request dictionary"""
        try:
            request_str = request_data.decode('utf-8', errors='ignore')
            
            # Split headers and body
            if '\r\n\r\n' in request_str:
                headers_part, body = request_str.split('\r\n\r\n', 1)
            else:
                headers_part = request_str
                body = ""
            
            lines = headers_part.split('\r\n')
            if not lines:
                return None
            
            # Parse request line
            request_line = lines[0]
            parts = request_line.split()
            if len(parts) != 3:
                return None
            
            method, path, version = parts
            
            # Parse headers
            headers = {}
            for line in lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
            
            return {
                'method': method.upper(),
                'path': unquote(path),  # URL decode the path
                'version': version,
                'headers': headers,
                'body': body
            }
            
        except Exception:
            return None
    
    def validate_host_header(self, request, client_socket, thread_name):
        """Validate Host header for security"""
        host_header = request['headers'].get('host', '')
        
        if not host_header:
            self.log("Security violation: Missing Host header", thread_name)
            self.send_error_response(client_socket, 400, "Bad Request", "Missing Host header")
            return False
        
        # Valid hosts include localhost and the server's IP with correct port
        valid_hosts = [
            f"{self.host}:{self.port}",
            f"localhost:{self.port}",
            f"127.0.0.1:{self.port}"
        ]
        
        if self.port == 80:
            valid_hosts.extend([self.host, "localhost", "127.0.0.1"])
        
        if host_header not in valid_hosts:
            self.log(f"Security violation: Invalid Host header: {host_header}", thread_name)
            self.send_error_response(client_socket, 403, "Forbidden", "Invalid Host header")
            return False
        
        self.log(f"Host validation: {host_header} ✓", thread_name)
        return True
    
    def handle_request(self, request, client_socket, thread_name, connection_count, max_requests):
        """Handle HTTP request and return whether to keep connection alive"""
        method = request['method']
        path = request['path']
        
        try:
            if method == 'GET':
                return self.handle_get_request(request, client_socket, thread_name, connection_count, max_requests)
            elif method == 'POST':
                return self.handle_post_request(request, client_socket, thread_name, connection_count, max_requests)
            else:
                self.send_error_response(client_socket, 405, "Method Not Allowed", f"Method {method} is not supported")
                return False
                
        except Exception as e:
            self.log(f"Error handling {method} {path}: {e}", thread_name)
            self.send_error_response(client_socket, 500, "Internal Server Error")
            return False
    
    def handle_get_request(self, request, client_socket, thread_name, connection_count, max_requests):
        """Handle GET request for files"""
        path = request['path']
        
        # Security: Validate and sanitize path
        safe_path = self.validate_and_sanitize_path(path)
        if not safe_path:
            self.log(f"Security violation: Path traversal attempt: {path}", thread_name)
            self.send_error_response(client_socket, 403, "Forbidden", "Access denied")
            return False
        
        file_path = os.path.join(self.resources_dir, safe_path)
        
        # Check if file exists
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            self.send_error_response(client_socket, 404, "Not Found", f"File {path} not found")
            return self.should_keep_alive(request, connection_count, max_requests)
        
        # Get file extension to determine content type
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == '.html':
            return self.serve_html_file(file_path, client_socket, thread_name, request, connection_count, max_requests)
        elif ext in ['.txt', '.png', '.jpg', '.jpeg']:
            return self.serve_binary_file(file_path, client_socket, thread_name, request, connection_count, max_requests)
        else:
            self.send_error_response(client_socket, 415, "Unsupported Media Type", f"File type {ext} not supported")
            return self.should_keep_alive(request, connection_count, max_requests)
    
    def validate_and_sanitize_path(self, path):
        """Validate and sanitize file path to prevent directory traversal"""
        # Remove leading slash
        if path.startswith('/'):
            path = path[1:]
        
        # Handle root path
        if path == '' or path == '/':
            path = 'index.html'
        
        # Security checks
        if '..' in path or path.startswith('/') or '\\' in path:
            return None
        
        # Additional security: ensure path doesn't contain suspicious patterns
        if re.search(r'(\.\.)|(\.\/)|(\/\.)|(\\\.)|(^\/)', path):
            return None
        
        # Normalize the path
        try:
            safe_path = os.path.normpath(path)
            # Ensure the normalized path doesn't go outside resources directory
            if safe_path.startswith('..') or os.path.isabs(safe_path):
                return None
            return safe_path
        except:
            return None
    
    def serve_html_file(self, file_path, client_socket, thread_name, request, connection_count, max_requests):
        """Serve HTML file with text/html content type"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            content_type = "text/html; charset=utf-8"
            self.send_successful_response(
                client_socket, content, content_type, 
                request, connection_count, max_requests
            )
            
            self.log(f"Served HTML file: {os.path.basename(file_path)} ({len(content)} bytes)", thread_name)
            return self.should_keep_alive(request, connection_count, max_requests)
            
        except Exception as e:
            self.log(f"Error serving HTML file {file_path}: {e}", thread_name)
            self.send_error_response(client_socket, 500, "Internal Server Error")
            return False
    
    def serve_binary_file(self, file_path, client_socket, thread_name, request, connection_count, max_requests):
        """Serve binary file (images, text files) for download"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            filename = os.path.basename(file_path)
            content_type = "application/octet-stream"
            
            # Send response with Content-Disposition for download
            self.send_binary_response(
                client_socket, content, filename, 
                request, connection_count, max_requests
            )
            
            self.log(f"Sending binary file: {filename} ({len(content)} bytes)", thread_name)
            self.log(f"Response: 200 OK ({len(content)} bytes transferred)", thread_name)
            
            return self.should_keep_alive(request, connection_count, max_requests)
            
        except Exception as e:
            self.log(f"Error serving binary file {file_path}: {e}", thread_name)
            self.send_error_response(client_socket, 500, "Internal Server Error")
            return False
    
    def handle_post_request(self, request, client_socket, thread_name, connection_count, max_requests):
        """Handle POST request for JSON data"""
        # Check Content-Type
        content_type = request['headers'].get('content-type', '')
        
        if not content_type.startswith('application/json'):
            self.send_error_response(client_socket, 415, "Unsupported Media Type", "Only application/json is supported")
            return self.should_keep_alive(request, connection_count, max_requests)
        
        # Parse JSON body
        try:
            json_data = json.loads(request['body'])
        except json.JSONDecodeError:
            self.send_error_response(client_socket, 400, "Bad Request", "Invalid JSON data")
            return self.should_keep_alive(request, connection_count, max_requests)
        
        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = ''.join(random.choices('abcdef0123456789', k=4))
        filename = f"upload_{timestamp}_{random_id}.json"
        filepath = os.path.join(self.uploads_dir, filename)
        
        # Save JSON to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2)
            
            # Create response
            response_data = {
                "status": "success",
                "message": "File created successfully", 
                "filepath": f"/uploads/{filename}"
            }
            
            response_json = json.dumps(response_data, indent=2)
            self.send_post_response(client_socket, response_json, request, connection_count, max_requests)
            
            self.log(f"JSON file created: {filename}", thread_name)
            return self.should_keep_alive(request, connection_count, max_requests)
            
        except Exception as e:
            self.log(f"Error saving JSON file: {e}", thread_name)
            self.send_error_response(client_socket, 500, "Internal Server Error")
            return False
    
    def should_keep_alive(self, request, connection_count, max_requests):
        """Determine if connection should be kept alive"""
        # Check connection limit
        if connection_count >= max_requests:
            return False
        
        # Check Connection header
        connection_header = request['headers'].get('connection', '').lower()
        version = request.get('version', 'HTTP/1.1')
        
        if connection_header == 'close':
            return False
        elif connection_header == 'keep-alive':
            return True
        else:
            # Default behavior based on HTTP version
            return version == 'HTTP/1.1'
    
    def send_successful_response(self, client_socket, content, content_type, request, connection_count, max_requests):
        """Send successful HTTP response"""
        keep_alive = self.should_keep_alive(request, connection_count, max_requests)
        
        response = f"HTTP/1.1 200 OK\r\n"
        response += f"Content-Type: {content_type}\r\n"
        response += f"Content-Length: {len(content)}\r\n"
        response += f"Date: {self.get_http_date()}\r\n"
        response += f"Server: {self.server_name}\r\n"
        response += f"Connection: {'keep-alive' if keep_alive else 'close'}\r\n"
        
        if keep_alive:
            response += "Keep-Alive: timeout=30, max=100\r\n"
        
        response += "\r\n"
        
        # Send headers
        self.send_all(client_socket, response.encode())
        # Send content
        self.send_all(client_socket, content)
    
    def send_all(self, client_socket, data):
        """Ensure all data is sent through the socket"""
        total_sent = 0
        while total_sent < len(data):
            try:
                sent = client_socket.send(data[total_sent:])
                if sent == 0:
                    raise RuntimeError("Socket connection broken")
                total_sent += sent
            except socket.error:
                raise RuntimeError("Failed to send data")
    
    def send_binary_response(self, client_socket, content, filename, request, connection_count, max_requests):
        """Send binary file response with download headers"""
        keep_alive = self.should_keep_alive(request, connection_count, max_requests)
        
        response = f"HTTP/1.1 200 OK\r\n"
        response += f"Content-Type: application/octet-stream\r\n"
        response += f"Content-Length: {len(content)}\r\n"
        response += f"Content-Disposition: attachment; filename=\"{filename}\"\r\n"
        response += f"Date: {self.get_http_date()}\r\n"
        response += f"Server: {self.server_name}\r\n"
        response += f"Connection: {'keep-alive' if keep_alive else 'close'}\r\n"
        
        if keep_alive:
            response += "Keep-Alive: timeout=30, max=100\r\n"
        
        response += "\r\n"
        
        # Send headers
        self.send_all(client_socket, response.encode())
        # Send binary content in chunks for large files
        self.send_all(client_socket, content)
    
    def send_post_response(self, client_socket, json_content, request, connection_count, max_requests):
        """Send POST response"""
        keep_alive = self.should_keep_alive(request, connection_count, max_requests)
        
        response = f"HTTP/1.1 201 Created\r\n"
        response += f"Content-Type: application/json\r\n"
        response += f"Content-Length: {len(json_content.encode())}\r\n"
        response += f"Date: {self.get_http_date()}\r\n"
        response += f"Server: {self.server_name}\r\n"
        response += f"Connection: {'keep-alive' if keep_alive else 'close'}\r\n"
        
        if keep_alive:
            response += "Keep-Alive: timeout=30, max=100\r\n"
        
        response += "\r\n"
        
        # Send response
        self.send_all(client_socket, response.encode())
        self.send_all(client_socket, json_content.encode())
    
    def send_error_response(self, client_socket, status_code, status_text, message=""):
        """Send HTTP error response"""
        try:
            if not message:
                message = status_text
            
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{status_code} {status_text}</title>
</head>
<body>
    <h1>{status_code} {status_text}</h1>
    <p>{message}</p>
    <hr>
    <p><em>{self.server_name}</em></p>
</body>
</html>"""
            
            response = f"HTTP/1.1 {status_code} {status_text}\r\n"
            response += f"Content-Type: text/html; charset=utf-8\r\n"
            response += f"Content-Length: {len(html_content.encode())}\r\n"
            response += f"Date: {self.get_http_date()}\r\n"
            response += f"Server: {self.server_name}\r\n"
            response += f"Connection: close\r\n"
            
            if status_code == 503:
                response += "Retry-After: 60\r\n"
            
            response += "\r\n"
            
            self.send_all(client_socket, response.encode())
            self.send_all(client_socket, html_content.encode())
            
        except Exception:
            pass  # Ignore errors when sending error responses
    
    def get_http_date(self):
        """Get current date in RFC 7231 format"""
        return time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
    
    def stop(self):
        """Stop the server gracefully"""
        self.running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Signal worker threads to stop
        for _ in range(self.max_threads):
            self.connection_queue.put((None, None))
        
        self.log("Server stopped")


def main():
    """Main entry point"""
    # Parse command line arguments
    host = '127.0.0.1'
    port = 8080
    max_threads = 10
    
    if len(sys.argv) >= 2:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)
    
    if len(sys.argv) >= 3:
        host = sys.argv[2]
    
    if len(sys.argv) >= 4:
        try:
            max_threads = int(sys.argv[3])
            if max_threads <= 0:
                raise ValueError("Thread count must be positive")
        except ValueError as e:
            print(f"Invalid thread count: {e}")
            sys.exit(1)
    
    # Create and start server
    server = HTTPServer(host, port, max_threads)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server.stop()


if __name__ == "__main__":
    main()