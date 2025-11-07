#!/bin/bash
# Smoke tests for Prime Spark AI deployment

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

echo "Running smoke tests against: $BASE_URL"

# Test 1: Health check
echo "Test 1: Health check..."
response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
if [ "$response" != "200" ]; then
  echo "FAILED: Health check returned $response"
  exit 1
fi
echo "PASSED: Health check"

# Test 2: Ready check
echo "Test 2: Ready check..."
response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health/ready")
if [ "$response" != "200" ]; then
  echo "FAILED: Ready check returned $response"
  exit 1
fi
echo "PASSED: Ready check"

# Test 3: Metrics endpoint
echo "Test 3: Metrics endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/metrics")
if [ "$response" != "200" ]; then
  echo "FAILED: Metrics endpoint returned $response"
  exit 1
fi
echo "PASSED: Metrics endpoint"

# Test 4: API version
echo "Test 4: API version..."
version=$(curl -s "$BASE_URL/api/v1/version" | jq -r '.version')
if [ -z "$version" ]; then
  echo "FAILED: Could not retrieve version"
  exit 1
fi
echo "PASSED: API version $version"

echo "All smoke tests passed!"
exit 0
