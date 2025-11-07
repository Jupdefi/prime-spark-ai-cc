#!/bin/bash
# Integration tests for Prime Spark AI

set -e

ENVIRONMENT=$1
BASE_URL=""

case $ENVIRONMENT in
  staging)
    BASE_URL="https://staging.prime-spark.ai"
    ;;
  production)
    BASE_URL="https://api.prime-spark.ai"
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    exit 1
    ;;
esac

echo "Running integration tests against: $BASE_URL"

# Test 1: Storage layer
echo "Test 1: Storage layer..."
curl -s -X POST "$BASE_URL/api/v1/storage/test" \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}' | jq -e '.status == "success"' > /dev/null
echo "PASSED: Storage layer"

# Test 2: Analytics engine
echo "Test 2: Analytics engine..."
curl -s -X GET "$BASE_URL/api/v1/analytics/metrics" | jq -e '.metrics' > /dev/null
echo "PASSED: Analytics engine"

# Test 3: Authentication
echo "Test 3: Authentication..."
token=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}' | jq -r '.token')
if [ -z "$token" ]; then
  echo "FAILED: Authentication failed"
  exit 1
fi
echo "PASSED: Authentication"

# Test 4: End-to-end workflow
echo "Test 4: End-to-end workflow..."
curl -s -X POST "$BASE_URL/api/v1/workflow/execute" \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{"workflow": "test"}' | jq -e '.status == "completed"' > /dev/null
echo "PASSED: End-to-end workflow"

echo "All integration tests passed!"
exit 0
