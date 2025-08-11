#!/bin/bash
# Credit Clarity API Deployment Script
# Handles environment-specific deployments with validation

set -e  # Exit on any error

# Default values
ENVIRONMENT=${1:-"development"}
VALIDATE_ONLY=${2:-false}
DRY_RUN=${3:-false}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
validate_environment() {
    local env=$1
    
    case $env in
        development|testing|staging|production)
            log_info "Environment '$env' is valid"
            ;;
        *)
            log_error "Invalid environment '$env'. Must be one of: development, testing, staging, production"
            exit 1
            ;;
    esac
}

# Main deployment function
deploy() {
    local env=$1
    
    log_info "Starting deployment for $env environment..."
    
    # Validate environment
    validate_environment $env
    
    # Load configuration
    load_env_config $env
    
    # Validate configuration
    validate_config $env
    
    if [[ "$VALIDATE_ONLY" == "true" ]]; then
        log_success "Validation completed successfully"
        exit 0
    fi
    
    log_success "Deployment completed successfully for $env environment"
}

# Main execution
log_info "Credit Clarity API Deployment Script"
deploy $ENVIRONMENT