# Multi-threaded HTTP Server

A multi-threaded HTTP server built using socket programming in Python, demonstrating low-level networking concepts and HTTP protocol implementation.

## Features

- Multi-threaded request handling with thread pool
- Binary file transfer support (PNG, JPEG, TXT files)
- HTML file serving with proper Content-Type headers
- JSON POST request processing
- HTTP/1.1 keep-alive connection support
- Path traversal protection and security features

## Running the Server

### Prerequisites

- Python 3.6 or higher

### Start the Server

**Basic usage (localhost:8080):**

```bash
python3 server.py
```

**Custom port:**

```bash
python3 server.py 8000
```

**Custom host and port:**

```bash
python3 server.py 8000 0.0.0.0
```

### Command Line Arguments

```
python3 server.py [port] [host] [max_threads]
```

- `port`: Port number (default: 8080)
- `host`: Host address (default: 127.0.0.1)
- `max_threads`: Maximum thread pool size (default: 10)

## Project Structure

```
Socket-P/
├── server.py              # Main HTTP server implementation
├── resources/             # Web content directory
│   ├── index.html         # Home page
│   ├── about.html         # About page
│   ├── contact.html       # Contact page
│   ├── sample.txt         # Test text file
│   ├── logo.png          # PNG image
│   ├── photo.jpg         # JPEG image
│   └── uploads/          # Directory for POST uploads
└── README.md             # Documentation
```

## Testing the Server

### Access in Browser

Open your browser and navigate to:

- `http://localhost:8080/` - Home page
- `http://localhost:8080/about.html` - About page
- `http://localhost:8080/contact.html` - Contact page

### Test File Downloads

```bash
curl -O http://localhost:8080/sample.txt
curl -O http://localhost:8080/logo.png
curl -O http://localhost:8080/photo.jpg
```

### Test JSON POST

```bash
curl -X POST http://localhost:8080/upload \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "message": "Hello World"}'
```

## Security Features

- **Path Traversal Protection**: Blocks attempts to access files outside the resources directory
- **Host Header Validation**: Prevents host header injection attacks
- **Request Size Limits**: Prevents DoS attacks
- **Input Validation**: Validates JSON data and file paths
