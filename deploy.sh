#!/bin/bash

# 🐳 Deadman Switch Docker Deployment Script
# Simple script to deploy the application with Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "🐳 Deadman Switch Docker Deployment"
    echo "=================================="
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "Docker is running"
}

check_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install docker-compose first."
        exit 1
    fi
    
    print_success "docker-compose is available"
}

show_menu() {
    echo ""
    echo "Select deployment option:"
    echo "1) Development (SQLite, hot reload)"
    echo "2) Production (PostgreSQL + Redis)"
    echo "3) Build Docker image only"
    echo "4) Stop all services"
    echo "5) View logs"
    echo "6) Clean up (remove containers and volumes)"
    echo "7) Exit"
    echo ""
}

deploy_development() {
    print_info "Starting development environment..."
    docker-compose -f docker-compose.dev.yml up --build
}

deploy_production() {
    print_info "Starting production environment..."
    docker-compose up --build
}

build_image() {
    print_info "Building Docker image..."
    docker build -t deadman-switch .
    print_success "Docker image built successfully"
}

stop_services() {
    print_info "Stopping all services..."
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    docker-compose down 2>/dev/null || true
    print_success "All services stopped"
}

view_logs() {
    echo ""
    echo "Select logs to view:"
    echo "1) Development logs"
    echo "2) Production logs"
    echo "3) Back to main menu"
    echo ""
    read -p "Enter your choice (1-3): " log_choice
    
    case $log_choice in
        1)
            print_info "Showing development logs (Ctrl+C to exit)..."
            docker-compose -f docker-compose.dev.yml logs -f
            ;;
        2)
            print_info "Showing production logs (Ctrl+C to exit)..."
            docker-compose logs -f
            ;;
        3)
            return
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
}

cleanup() {
    print_warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        print_info "Cleaning up..."
        docker-compose -f docker-compose.dev.yml down -v 2>/dev/null || true
        docker-compose down -v 2>/dev/null || true
        docker system prune -f
        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

show_info() {
    print_info "Application URLs:"
    echo "  🌐 Web App: http://localhost:8000"
    echo "  📚 API Docs: http://localhost:8000/docs"
    echo "  ❤️  Health Check: http://localhost:8000/health"
    echo ""
    print_info "Default Credentials:"
    echo "  👤 Username: admin"
    echo "  📧 Email: admin@deadmanswitch.com"
    echo "  🔑 Password: admin123"
    echo ""
    print_warning "Please change the admin password after first login!"
}

# Main script
main() {
    print_header
    
    # Check prerequisites
    check_docker
    check_compose
    
    while true; do
        show_menu
        read -p "Enter your choice (1-7): " choice
        
        case $choice in
            1)
                deploy_development
                show_info
                ;;
            2)
                deploy_production
                show_info
                ;;
            3)
                build_image
                ;;
            4)
                stop_services
                ;;
            5)
                view_logs
                ;;
            6)
                cleanup
                ;;
            7)
                print_success "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please enter 1-7."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main function
main "$@"
