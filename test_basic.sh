#!/bin/bash

# Simple test script for HTTP server using curl
# Tests basic functionality without requiring Python libraries

echo "🧪 HTTP Server Test Suite (curl-based)"
echo "======================================"

BASE_URL="http://localhost:8080"

# Check if server is running
echo "Checking if server is running..."
if ! curl -s --connect-timeout 3 "$BASE_URL/" > /dev/null 2>&1; then
    echo "❌ Server is not running on localhost:8080"
    echo "   Please start the server first: python3 server.py"
    exit 1
fi

echo "✅ Server is running!"
echo

# Test counters
TESTS_PASSED=0
TOTAL_TESTS=0

# Test 1: HTML serving
echo "1. Testing HTML serving..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if curl -s -I "$BASE_URL/" | grep -q "200 OK" && curl -s -I "$BASE_URL/" | grep -q "text/html"; then
    echo "   ✅ HTML serving works"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo "   ❌ HTML serving failed"
fi

# Test 2: Binary file download
echo "2. Testing binary file download..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if curl -s -I "$BASE_URL/sample.txt" | grep -q "200 OK" && curl -s -I "$BASE_URL/sample.txt" | grep -q "octet-stream"; then
    echo "   ✅ Binary file download works"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo "   ❌ Binary file download failed"
fi

# Test 3: JSON POST
echo "3. Testing JSON POST..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/upload" \
    -H "Content-Type: application/json" \
    -d '{"test": "data", "timestamp": "2024-10-05"}')

if echo "$RESPONSE" | grep -q "201" && echo "$RESPONSE" | grep -q "success"; then
    echo "   ✅ JSON POST works"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo "   ❌ JSON POST failed"
fi

# Test 4: 404 handling
echo "4. Testing 404 error handling..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if curl -s -I "$BASE_URL/nonexistent.html" | grep -q "404"; then
    echo "   ✅ 404 handling works"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo "   ❌ 404 handling failed"
fi

# Test 5: Method validation (405)
echo "5. Testing unsupported method..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if curl -s -I -X PUT "$BASE_URL/" | grep -q "405"; then
    echo "   ✅ Method validation works"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo "   ❌ Method validation failed"
fi

# Test 6: Path traversal security
echo "6. Testing path traversal protection..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if curl -s -I "$BASE_URL/../etc/passwd" | grep -q "403"; then
    echo "   ✅ Path traversal protection works"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo "   ❌ Path traversal protection failed"
fi

# Test 7: Host header validation
echo "7. Testing host header validation..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if curl -s -I -H "Host: evil.com" "$BASE_URL/" | grep -q "403"; then
    echo "   ✅ Host header validation works"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo "   ❌ Host header validation failed"
fi

# Test 8: File integrity (small file)
echo "8. Testing file integrity..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f "resources/sample.txt" ]; then
    ORIGINAL_SIZE=$(wc -c < "resources/sample.txt")
    DOWNLOADED_SIZE=$(curl -s "$BASE_URL/sample.txt" | wc -c)
    
    if [ "$ORIGINAL_SIZE" -eq "$DOWNLOADED_SIZE" ]; then
        echo "   ✅ File integrity verified ($ORIGINAL_SIZE bytes)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "   ❌ File integrity failed (original: $ORIGINAL_SIZE, downloaded: $DOWNLOADED_SIZE)"
    fi
else
    echo "   ⚠️  Sample file not found, skipping integrity test"
fi

# Test 9: Concurrent requests
echo "9. Testing concurrent requests..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
SUCCESS_COUNT=0

for i in {1..5}; do
    if curl -s "$BASE_URL/sample.txt" > /dev/null & then
        ((SUCCESS_COUNT++))
    fi
done

wait  # Wait for all background processes

if [ $SUCCESS_COUNT -ge 4 ]; then
    echo "   ✅ Concurrent requests work ($SUCCESS_COUNT/5 successful)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo "   ❌ Concurrent requests failed ($SUCCESS_COUNT/5 successful)"
fi

# Final results
echo
echo "======================================"
echo "🏁 FINAL RESULTS: $TESTS_PASSED/$TOTAL_TESTS tests passed"

if [ $TESTS_PASSED -eq $TOTAL_TESTS ]; then
    echo "🎉 ALL TESTS PASSED! Server is working correctly."
    exit 0
else
    FAILED=$((TOTAL_TESTS - TESTS_PASSED))
    echo "⚠️  $FAILED tests failed."
    exit 1
fi