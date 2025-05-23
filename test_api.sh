#!/bin/bash
# Simple script to test API endpoints using curl

echo "Testing API endpoints..."
echo "1. Testing summary endpoint"
curl -s -X GET http://localhost:8000/v1/analysis/summary | head -n 20
echo
echo

echo "2. Testing weights endpoint"
curl -s -X GET http://localhost:8000/v1/analysis/weights | head -n 20
echo
echo

echo "Tests completed"
