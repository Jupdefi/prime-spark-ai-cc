#!/bin/bash
# Check deployment metrics

set -e

ENVIRONMENT=$1
DEPLOYMENT_TYPE=$2

NAMESPACE="prime-spark"
DEPLOYMENT_NAME=""

case $ENVIRONMENT in
  staging)
    DEPLOYMENT_NAME="staging-kva-api"
    ;;
  production)
    DEPLOYMENT_NAME="prod-kva-api"
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    exit 1
    ;;
esac

echo "Checking metrics for $DEPLOYMENT_NAME in $NAMESPACE"

# Check pod status
echo "Checking pod status..."
ready_pods=$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
desired_pods=$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.replicas}')

if [ "$ready_pods" != "$desired_pods" ]; then
  echo "FAILED: $ready_pods/$desired_pods pods ready"
  exit 1
fi
echo "PASSED: $ready_pods/$desired_pods pods ready"

# Check error rate
echo "Checking error rate..."
error_rate=$(kubectl exec -n $NAMESPACE deployment/$DEPLOYMENT_NAME -- \
  curl -s http://localhost:8002/metrics | grep http_requests_total | grep -E "status=\"5" | awk '{sum+=$2} END {print sum}')

if [ -z "$error_rate" ]; then
  error_rate=0
fi

if [ "$error_rate" -gt 10 ]; then
  echo "FAILED: Error rate too high: $error_rate"
  exit 1
fi
echo "PASSED: Error rate acceptable: $error_rate"

# Check CPU usage
echo "Checking CPU usage..."
cpu_usage=$(kubectl top pod -n $NAMESPACE -l app=kva-api --no-headers | awk '{sum+=$2} END {print sum}')
echo "Current CPU usage: $cpu_usage"

# Check memory usage
echo "Checking memory usage..."
memory_usage=$(kubectl top pod -n $NAMESPACE -l app=kva-api --no-headers | awk '{sum+=$3} END {print sum}')
echo "Current memory usage: $memory_usage"

echo "All metrics checks passed!"
exit 0
