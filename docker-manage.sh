#!/bin/bash

# Supply Chain Docker Management Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Supply Chain - Docker Environment${NC}"
echo ""

# Function to wait for backend to be ready
wait_for_backend() {
    echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
    for i in {1..30}; do
        if docker compose exec -T backend uv run python src/manage.py check --database default &> /dev/null; then
            echo -e "${GREEN}Backend is ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    echo -e "${RED}Backend failed to start in time${NC}"
    return 1
}

# Parse command
case "${1}" in
    up)
        echo -e "${GREEN}Starting all services...${NC}"
        docker compose up -d
        echo ""
        echo -e "${GREEN}Services starting! Access points:${NC}"
        echo "  - Frontend:        http://localhost:4200"
        echo "  - Backend API:     http://localhost:8000"
        echo "  - Admin Panel:     http://localhost:8000/admin"
        echo "  - RabbitMQ UI:     http://localhost:15672 (guest/guest)"
        echo "  - MinIO Console:   http://localhost:9001 (minioadmin/minioadmin)"
        echo ""
        echo -e "${YELLOW}Run 'docker compose logs -f' to view logs${NC}"
        ;;
    
    seed)
        echo -e "${GREEN}Seeding database with mock data...${NC}"
        if wait_for_backend; then
            docker compose exec backend uv run python src/manage.py seed_data
            echo ""
            echo -e "${GREEN}Database seeded successfully!${NC}"
            echo -e "Main user: ${YELLOW}teodor${NC} (password: ${YELLOW}teodorpass${NC})"
        fi
        ;;
    
    reset)
        echo -e "${YELLOW}Resetting all data...${NC}"
        read -p "Are you sure? This will delete all data (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker compose exec backend uv run python src/manage.py reset_data --force
            echo -e "${GREEN}Data reset complete!${NC}"
        else
            echo -e "${YELLOW}Reset cancelled${NC}"
        fi
        ;;
    
    reset-seed)
        echo -e "${GREEN}Resetting and seeding database...${NC}"
        if wait_for_backend; then
            docker compose exec backend uv run python src/manage.py reset_data --force
            docker compose exec backend uv run python src/manage.py seed_data
            echo ""
            echo -e "${GREEN}Database reset and seeded successfully!${NC}"
            echo -e "Main user: ${YELLOW}teodor${NC} (password: ${YELLOW}teodorpass${NC})"
        fi
        ;;
    
    migrate)
        echo -e "${GREEN}Running database migrations...${NC}"
        docker compose exec backend uv run python src/manage.py migrate
        ;;
    
    makemigrations)
        echo -e "${GREEN}Creating new migrations...${NC}"
        docker compose exec backend uv run python src/manage.py makemigrations
        ;;
    
    shell)
        echo -e "${GREEN}Opening Django shell...${NC}"
        docker compose exec backend uv run python src/manage.py shell
        ;;
    
    logs)
        if [ -z "$2" ]; then
            docker compose logs -f
        else
            docker compose logs -f "$2"
        fi
        ;;
    
    down)
        echo -e "${YELLOW}Stopping all services...${NC}"
        docker compose down
        echo -e "${GREEN}All services stopped${NC}"
        ;;
    
    down-v)
        echo -e "${RED}Stopping all services and removing volumes...${NC}"
        read -p "This will delete all data including the database! Continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker compose down -v
            echo -e "${GREEN}All services stopped and data removed${NC}"
        else
            echo -e "${YELLOW}Cancelled${NC}"
        fi
        ;;
    
    rebuild)
        echo -e "${GREEN}Rebuilding all containers...${NC}"
        docker compose build --no-cache
        echo -e "${GREEN}Rebuild complete!${NC}"
        ;;
    
    restart)
        if [ -z "$2" ]; then
            echo -e "${YELLOW}Restarting all services...${NC}"
            docker compose restart
        else
            echo -e "${YELLOW}Restarting $2...${NC}"
            docker compose restart "$2"
        fi
        echo -e "${GREEN}Restart complete!${NC}"
        ;;
    
    status)
        docker compose ps
        ;;
    
    *)
        echo "Usage: $0 {command}"
        echo ""
        echo "Commands:"
        echo "  up              - Start all services"
        echo "  seed            - Seed database with mock data"
        echo "  reset           - Reset all data (with confirmation)"
        echo "  reset-seed      - Reset and seed database"
        echo "  migrate         - Run database migrations"
        echo "  makemigrations  - Create new migrations"
        echo "  shell           - Open Django shell"
        echo "  logs [service]  - View logs (optionally for specific service)"
        echo "  down            - Stop all services"
        echo "  down-v          - Stop all services and remove volumes"
        echo "  rebuild         - Rebuild all containers"
        echo "  restart [svc]   - Restart all services or specific service"
        echo "  status          - Show service status"
        echo ""
        echo "Examples:"
        echo "  $0 up              # Start everything"
        echo "  $0 seed            # Seed data after starting"
        echo "  $0 logs backend    # View backend logs"
        echo "  $0 restart backend # Restart just the backend"
        ;;
esac
