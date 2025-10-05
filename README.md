# Multi-threaded HTTP Server

A high-performance HTTP server built from scratch using low-level socket programming in Python. This server demonstrates advanced networking concepts including multi-threading, binary file transfer, security features, and HTTP protocol implementation.

## Features

### Core Functionality
- ✅ Multi-threaded request handling with configurable thread pool
- ✅ Binary file transfer support (PNG, JPEG, TXT files)
- ✅ HTML file serving with proper Content-Type headers
- ✅ JSON POST request processing with file creation
- ✅ HTTP/1.1 keep-alive connection support
- ✅ Comprehensive logging and monitoring

### Security Features
- ✅ Path traversal protection (blocks `../`, `./`, etc.)
- ✅ Host header validation
- ✅ Request size limits (8KB headers + 1MB body)
- ✅ Security violation logging
- ✅ Input validation and sanitization

### Connection Management
- ✅ Configurable connection timeout (30 seconds)
- ✅ Connection limits (100 requests per connection)
- ✅ Thread pool with queue management
- ✅ Graceful connection handling and cleanup

## Quick Start

### Prerequisites
- Python 3.6 or higher
- Pillow library (for test image generation)

```bash
pip install Pillow
```

### Running the Server

1. **Basic usage (localhost:8080)**:
   ```bash
   ./server.py
   ```

2. **Custom port**:
   ```bash
   ./server.py 8000
   ```

3. **Custom host and port**:
   ```bash
   ./server.py 8000 0.0.0.0
   ```

4. **Full configuration**:
   ```bash
   ./server.py 8000 0.0.0.0 20
   ```
   - Port: 8000
   - Host: 0.0.0.0 (all interfaces)
   - Max threads: 20

### Command Line Arguments
```
./server.py [port] [host] [max_threads]
```

- `port`: Port number (default: 8080)
- `host`: Host address (default: 127.0.0.1)
- `max_threads`: Maximum thread pool size (default: 10)

## Project Structure

```
Socket-P/
├── server.py              # Main HTTP server implementation
├── resources/             # Web content directory
│   ├── index.html         # Default home page
│   ├── about.html         # About page
│   ├── contact.html       # Contact/testing page
│   ├── sample.txt         # Test text file
│   ├── document.txt       # Another test text file
│   ├── logo.png          # Small PNG image (1KB)
│   ├── photo.jpg         # JPEG image (9KB)
│   ├── large_image.png   # Large PNG image (8.6MB)
│   └── uploads/          # Directory for POST uploads
└── README.md             # This file
```

## API Endpoints

### GET Requests

#### HTML Files (Rendered in Browser)
- `GET /` → serves `resources/index.html`
- `GET /about.html` → serves `resources/about.html`
- `GET /contact.html` → serves `resources/contact.html`

**Response Headers:**
```
Content-Type: text/html; charset=utf-8
```

#### Binary Files (Downloaded as Files)
- `GET /sample.txt` → downloads text file
- `GET /logo.png` → downloads PNG image
- `GET /photo.jpg` → downloads JPEG image
- `GET /large_image.png` → downloads large PNG (8.6MB)

**Response Headers:**
```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="filename.ext"
```

### POST Requests

#### JSON Data Upload
- `POST /upload` with JSON body → creates timestamped file in `uploads/`

**Request:**
```bash
curl -X POST http://localhost:8080/upload \\
  -H "Content-Type: application/json" \\
  -d '{"name": "test", "message": "Hello World"}'
```

**Response:**
```json
{
  "status": "success",
  "message": "File created successfully",
  "filepath": "/uploads/upload_20241005_143022_a7b9.json"
}
```

## Testing the Server

### 1. Basic Functionality Tests

**HTML Serving:**
```bash
curl http://localhost:8080/
curl http://localhost:8080/about.html
curl http://localhost:8080/contact.html
```

**Binary File Downloads:**
```bash
curl -O http://localhost:8080/sample.txt
curl -O http://localhost:8080/logo.png
curl -O http://localhost:8080/photo.jpg
curl -O http://localhost:8080/large_image.png
```

**JSON POST:**
```bash
curl -X POST http://localhost:8080/upload \\
  -H "Content-Type: application/json" \\
  -d '{"test": "data", "timestamp": "2024-10-05"}'
```

### 2. Security Tests (Should Return Errors)

**Path Traversal Attempts:**
```bash
curl http://localhost:8080/../etc/passwd          # 403 Forbidden
curl http://localhost:8080/../../sensitive.txt   # 403 Forbidden
curl http://localhost:8080/./.././config         # 403 Forbidden
```

**Invalid Host Header:**
```bash
curl -H "Host: evil.com" http://localhost:8080/   # 403 Forbidden
```

**Unsupported Methods:**
```bash
curl -X PUT http://localhost:8080/test            # 405 Method Not Allowed
curl -X DELETE http://localhost:8080/test         # 405 Method Not Allowed
```

**Invalid Content-Type for POST:**
```bash
curl -X POST http://localhost:8080/upload \\
  -H "Content-Type: text/plain" \\
  -d "not json"                                   # 415 Unsupported Media Type
```

### 3. Concurrency Tests

**Multiple Simultaneous Downloads:**
```bash
for i in {1..10}; do
  curl -O http://localhost:8080/large_image.png &
done
wait
```

**Stress Test:**
```bash
for i in {1..50}; do
  curl -s http://localhost:8080/ > /dev/null &
done
wait
```

### 4. File Integrity Verification

**Verify downloaded files match originals:**
```bash
# Download files
curl -O http://localhost:8080/logo.png
curl -O http://localhost:8080/photo.jpg

# Compare checksums (macOS)
shasum resources/logo.png logo.png
shasum resources/photo.jpg photo.jpg

# Compare checksums (Linux)
sha256sum resources/logo.png logo.png
sha256sum resources/photo.jpg photo.jpg
```

## Server Architecture

### Thread Pool Design
- Configurable thread pool with default 10 worker threads
- Connection queue with overflow handling
- Thread-safe logging and resource management
- Graceful shutdown with connection cleanup

### Request Processing Pipeline
1. **Accept Connection** → Add to connection queue
2. **Worker Thread** → Process from queue
3. **Parse Request** → Extract method, path, headers, body
4. **Security Validation** → Host header, path traversal checks
5. **Route Handler** → GET (files) or POST (JSON)
6. **Response Generation** → Appropriate headers and content
7. **Keep-Alive Management** → Connection reuse or close

### Security Implementation

**Path Traversal Protection:**
- Blocks `../`, `./`, absolute paths
- Path normalization and validation
- Restricts access to `resources/` directory only

**Host Header Validation:**
- Accepts only valid host:port combinations
- Prevents host header injection attacks
- Logs security violations

**Input Validation:**
- Request size limits (8KB + 1MB body)
- JSON validation for POST requests
- Proper URL decoding and sanitization

## HTTP Protocol Compliance

### Supported Methods
- `GET`: File serving (HTML rendering, binary downloads)
- `POST`: JSON data processing
- Others return `405 Method Not Allowed`

### HTTP Status Codes
- `200 OK`: Successful GET requests
- `201 Created`: Successful POST requests  
- `400 Bad Request`: Malformed requests, missing Host header
- `403 Forbidden`: Path traversal, invalid Host header
- `404 Not Found`: File not found
- `405 Method Not Allowed`: Unsupported HTTP methods
- `415 Unsupported Media Type`: Wrong Content-Type, unsupported file types
- `500 Internal Server Error`: Server-side errors
- `503 Service Unavailable`: Thread pool exhausted

### Connection Management
- **HTTP/1.1 Keep-Alive**: Default behavior
- **HTTP/1.0**: Close after response
- **Timeout**: 30 seconds for idle connections
- **Request Limit**: 100 requests per connection
- **Headers**: `Keep-Alive: timeout=30, max=100`

## Binary Transfer Implementation

### File Types Supported
| Extension | Content-Type | Behavior |
|-----------|--------------|----------|
| `.html` | `text/html; charset=utf-8` | Rendered in browser |
| `.txt` | `application/octet-stream` | Downloaded as file |
| `.png` | `application/octet-stream` | Downloaded as file |
| `.jpg/.jpeg` | `application/octet-stream` | Downloaded as file |
| Others | N/A | `415 Unsupported Media Type` |

### Binary Transfer Features
- Files read in binary mode for data integrity
- Proper `Content-Length` calculation
- `Content-Disposition: attachment` for downloads
- Large file support (tested with 8.6MB image)
- Chunked reading for memory efficiency

## Logging Format

The server provides comprehensive logging with timestamps:

```
[2024-10-05 14:30:00] HTTP Server started on http://127.0.0.1:8080
[2024-10-05 14:30:00] Thread pool size: 10
[2024-10-05 14:30:00] Serving files from 'resources' directory
[2024-10-05 14:30:00] Press Ctrl+C to stop the server
[2024-10-05 14:30:15] [Thread-1] Connection from 127.0.0.1:54321
[2024-10-05 14:30:15] [Thread-1] Request: GET /logo.png HTTP/1.1
[2024-10-05 14:30:15] [Thread-1] Host validation: localhost:8080 ✓
[2024-10-05 14:30:15] [Thread-1] Sending binary file: logo.png (1154 bytes)
[2024-10-05 14:30:15] [Thread-1] Response: 200 OK (1154 bytes transferred)
[2024-10-05 14:30:15] [Thread-1] Connection closed (1 requests served)
```

## Performance Considerations

### Optimizations Implemented
- Thread pool prevents thread creation overhead
- Connection reuse with keep-alive
- Binary mode file reading
- Efficient buffer management
- Request size limits prevent DoS

### Scalability Features
- Configurable thread pool size
- Connection queuing for load bursts
- Timeout management for resource cleanup
- Memory-efficient large file handling

## Known Limitations

1. **Single-process**: No multi-process scaling
2. **Memory Usage**: Large files loaded entirely into memory
3. **SSL/TLS**: No HTTPS support (HTTP only)
4. **Virtual Hosts**: Single host serving only
5. **Caching**: No HTTP caching headers
6. **Compression**: No gzip/deflate encoding

## Error Handling

The server implements robust error handling:
- Socket errors and timeouts
- File system errors (permissions, not found)
- JSON parsing errors
- Thread synchronization errors
- Connection cleanup on failures

## Development and Testing

### Code Quality
- Comprehensive docstrings and comments
- Error handling at all levels
- Thread-safe operations
- Resource cleanup (sockets, files)
- PEP 8 compliant code style

### Testing Coverage
- ✅ Basic HTTP functionality
- ✅ Binary file integrity
- ✅ Security vulnerability prevention
- ✅ Concurrency and thread safety
- ✅ Error conditions and edge cases
- ✅ HTTP protocol compliance

## License

This project is created for educational purposes as part of a socket programming assignment.

## Author

Socket Programming Assignment - Multi-threaded HTTP Server Implementation