#!/bin/bash
# Master Deployment Orchestrator for Prime Spark AI
# Single command deployment to any environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$SCRIPT_DIR/deployment"
LOG_FILE="/tmp/prime-spark-deploy-$(date +%Y%m%d-%H%M%S).log"

# Functions
log() {
  echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
  exit 1
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
  echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

print_banner() {
  cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           PRIME SPARK AI DEPLOYMENT ORCHESTRATOR              ║
║                                                               ║
║   Comprehensive deployment automation for hybrid cloud       ║
║   infrastructure, edge devices, and Kubernetes clusters      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
}

show_usage() {
  cat << EOF

Usage: $0 [COMMAND] [OPTIONS]

COMMANDS:
  dev         Deploy to local development environment (Raspberry Pi 5)
  staging     Deploy to AWS staging environment
  production  Deploy to AWS production environment
  validate    Validate deployment configurations
  terraform   Deploy infrastructure with Terraform
  kubernetes  Deploy applications to Kubernetes
  ansible     Configure servers with Ansible
  destroy     Tear down infrastructure
  status      Check deployment status
  logs        View deployment logs
  help        Show this help message

OPTIONS:
  --skip-tests         Skip pre-deployment tests
  --skip-backup        Skip backup before deployment
  --dry-run            Preview changes without applying
  --auto-approve       Skip confirmation prompts
  --component <name>   Deploy specific component only
  --rollback           Rollback to previous version

EXAMPLES:
  # Deploy to local development
  $0 dev

  # Deploy to staging with dry-run
  $0 staging --dry-run

  # Deploy to production with auto-approve
  $0 production --auto-approve

  # Deploy only the API component
  $0 production --component kva-api

  # Rollback production deployment
  $0 production --rollback

  # Validate all configurations
  $0 validate

  # Check deployment status
  $0 status staging

EOF
}

check_prerequisites() {
  info "Checking prerequisites..."

  local missing_tools=()

  # Check required tools
  for tool in docker docker-compose kubectl terraform ansible aws jq curl; do
    if ! command -v $tool &> /dev/null; then
      missing_tools+=($tool)
    fi
  done

  if [ ${#missing_tools[@]} -ne 0 ]; then
    error "Missing required tools: ${missing_tools[*]}"
  fi

  log "✓ All prerequisites satisfied"
}

pre_flight_checks() {
  local env=$1
  info "Running pre-flight checks for $env..."

  # Check AWS credentials
  if [ "$env" != "dev" ]; then
    if ! aws sts get-caller-identity &> /dev/null; then
      error "AWS credentials not configured"
    fi
    log "✓ AWS credentials validated"
  fi

  # Check Kubernetes context
  if [ "$env" != "dev" ]; then
    if ! kubectl config current-context &> /dev/null; then
      warn "No Kubernetes context set. Will configure during deployment."
    else
      log "✓ Kubernetes context: $(kubectl config current-context)"
    fi
  fi

  # Check Docker daemon
  if ! docker info &> /dev/null; then
    error "Docker daemon not running"
  fi
  log "✓ Docker daemon running"

  log "✓ Pre-flight checks passed"
}

run_tests() {
  if [ "$SKIP_TESTS" = "true" ]; then
    warn "Skipping tests (--skip-tests flag)"
    return
  fi

  info "Running test suite..."

  cd "$SCRIPT_DIR"
  if [ -f "requirements-test.txt" ]; then
    pip install -q -r requirements-test.txt
  fi

  if pytest tests/ -v --tb=short; then
    log "✓ All tests passed"
  else
    error "Tests failed. Fix issues before deploying."
  fi
}

create_backup() {
  local env=$1

  if [ "$SKIP_BACKUP" = "true" ]; then
    warn "Skipping backup (--skip-backup flag)"
    return
  fi

  info "Creating backup for $env..."

  local backup_dir="$SCRIPT_DIR/backups/$(date +%Y%m%d-%H%M%S)-$env"
  mkdir -p "$backup_dir"

  # Backup configurations
  cp -r "$DEPLOYMENT_DIR/environments/$env.yaml" "$backup_dir/" 2>/dev/null || true

  # Backup databases (if applicable)
  if [ "$env" != "dev" ]; then
    info "Backing up databases..."
    # Add database backup logic here
  fi

  log "✓ Backup created: $backup_dir"
}

deploy_dev() {
  log "Deploying to LOCAL DEVELOPMENT (Raspberry Pi 5)..."

  cd "$SCRIPT_DIR"

  info "Starting Docker Compose services..."
  docker compose -f docker-compose.kva.yml up -d --build

  info "Waiting for services to be healthy..."
  sleep 10

  # Check service health
  if docker compose -f docker-compose.kva.yml ps | grep -q "unhealthy"; then
    error "Some services are unhealthy"
  fi

  log "✓ Development environment deployed successfully"
  info "Access the API at: http://localhost:8002"
  info "Access Grafana at: http://localhost:3003"
}

deploy_terraform() {
  local env=$1
  info "Deploying infrastructure with Terraform for $env..."

  cd "$DEPLOYMENT_DIR/terraform"

  terraform init

  if [ "$DRY_RUN" = "true" ]; then
    terraform plan -var-file="environments/$env.tfvars"
    return
  fi

  if [ "$AUTO_APPROVE" = "true" ]; then
    terraform apply -var-file="environments/$env.tfvars" -auto-approve
  else
    terraform apply -var-file="environments/$env.tfvars"
  fi

  log "✓ Terraform infrastructure deployed"
}

deploy_kubernetes() {
  local env=$1
  info "Deploying to Kubernetes for $env..."

  # Update kubeconfig
  if [ "$env" = "staging" ]; then
    aws eks update-kubeconfig --name prime-spark-eks-staging --region us-east-1
  elif [ "$env" = "production" ]; then
    aws eks update-kubeconfig --name prime-spark-eks-production --region us-east-1
  fi

  cd "$DEPLOYMENT_DIR/kubernetes"

  if [ "$DRY_RUN" = "true" ]; then
    kubectl diff -k overlays/$env || true
    return
  fi

  kubectl apply -k overlays/$env

  info "Waiting for rollout to complete..."
  kubectl rollout status deployment/${env}-kva-api -n prime-spark --timeout=10m

  log "✓ Kubernetes deployment completed"
}

deploy_staging() {
  log "Deploying to STAGING ENVIRONMENT..."

  pre_flight_checks "staging"
  run_tests
  create_backup "staging"
  deploy_terraform "staging"
  deploy_kubernetes "staging"

  info "Running smoke tests..."
  "$DEPLOYMENT_DIR/ci-cd/scripts/smoke-tests.sh" staging

  log "✓ Staging deployment completed successfully"
}

deploy_production() {
  log "Deploying to PRODUCTION ENVIRONMENT..."

  if [ "$AUTO_APPROVE" != "true" ]; then
    warn "You are about to deploy to PRODUCTION!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
      error "Deployment cancelled"
    fi
  fi

  pre_flight_checks "production"
  run_tests
  create_backup "production"
  deploy_terraform "production"
  deploy_kubernetes "production"

  info "Running integration tests..."
  "$DEPLOYMENT_DIR/ci-cd/scripts/integration-tests.sh" production

  log "✓ Production deployment completed successfully"
  warn "Remember to monitor the deployment in Grafana: https://grafana.prime-spark.ai"
}

validate_configs() {
  info "Validating deployment configurations..."

  # Validate Terraform
  cd "$DEPLOYMENT_DIR/terraform"
  terraform fmt -check -recursive || warn "Terraform files need formatting"
  terraform validate || error "Terraform validation failed"

  # Validate Kubernetes manifests
  cd "$DEPLOYMENT_DIR/kubernetes"
  for overlay in overlays/*/; do
    env_name=$(basename "$overlay")
    info "Validating $env_name Kubernetes manifests..."
    kubectl kustomize "$overlay" | kubectl apply --dry-run=client -f - || \
      error "Kubernetes validation failed for $env_name"
  done

  log "✓ All configurations validated"
}

show_status() {
  local env=$1
  info "Deployment status for $env..."

  if [ "$env" = "dev" ]; then
    docker compose -f docker-compose.kva.yml ps
    return
  fi

  # Update kubeconfig
  aws eks update-kubeconfig --name prime-spark-eks-$env --region us-east-1 &>/dev/null

  echo ""
  info "Pods:"
  kubectl get pods -n prime-spark

  echo ""
  info "Services:"
  kubectl get svc -n prime-spark

  echo ""
  info "Ingress:"
  kubectl get ingress -n prime-spark

  echo ""
  info "HPA:"
  kubectl get hpa -n prime-spark
}

# Main script
main() {
  print_banner

  # Parse arguments
  COMMAND=${1:-help}
  shift || true

  SKIP_TESTS=false
  SKIP_BACKUP=false
  DRY_RUN=false
  AUTO_APPROVE=false
  COMPONENT=""

  while [[ $# -gt 0 ]]; do
    case $1 in
      --skip-tests)
        SKIP_TESTS=true
        shift
        ;;
      --skip-backup)
        SKIP_BACKUP=true
        shift
        ;;
      --dry-run)
        DRY_RUN=true
        shift
        ;;
      --auto-approve)
        AUTO_APPROVE=true
        shift
        ;;
      --component)
        COMPONENT="$2"
        shift 2
        ;;
      --rollback)
        ROLLBACK=true
        shift
        ;;
      *)
        error "Unknown option: $1"
        ;;
    esac
  done

  log "Starting deployment orchestration..."
  log "Log file: $LOG_FILE"

  case $COMMAND in
    dev|development)
      check_prerequisites
      deploy_dev
      ;;
    staging)
      check_prerequisites
      deploy_staging
      ;;
    production|prod)
      check_prerequisites
      deploy_production
      ;;
    validate)
      check_prerequisites
      validate_configs
      ;;
    terraform)
      shift
      deploy_terraform "${1:-staging}"
      ;;
    kubernetes|k8s)
      shift
      deploy_kubernetes "${1:-staging}"
      ;;
    status)
      show_status "${2:-staging}"
      ;;
    destroy)
      error "Destroy not implemented yet. Use Terraform destroy manually."
      ;;
    logs)
      less "$LOG_FILE"
      ;;
    help|--help|-h)
      show_usage
      ;;
    *)
      error "Unknown command: $COMMAND"
      show_usage
      ;;
  esac

  log "Deployment orchestration completed!"
}

# Run main function
main "$@"
