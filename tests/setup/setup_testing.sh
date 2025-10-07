#!/bin/bash

# Video Streaming System Testing Setup Script
# This script sets up the testing environment

set -e

echo "🧪 Setting up Video Streaming System Testing Environment"
echo "========================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "database_migration_video_streaming.sql" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# 1. Check prerequisites
print_status "Checking prerequisites..."

# Check if PostgreSQL is running
if ! systemctl is-active --quiet postgresql; then
    print_warning "PostgreSQL is not running. Starting it..."
    sudo systemctl start postgresql
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is required but not installed"
    exit 1
fi

print_success "Prerequisites check completed"

# 2. Install Python dependencies for testing
print_status "Installing Python testing dependencies..."

pip3 install requests psycopg2-binary --user

print_success "Python dependencies installed"

# 3. Apply database migrations
print_status "Applying database migrations..."

# Read database connection from DB_pass file
if [ -f ".env/DB_pass" ]; then
    DB_URL=$(cat .env/DB_pass)
    # Extract components from PostgreSQL URL
    # Format: postgresql+psycopg://user:pass@host:port/db
    DB_USER=$(echo $DB_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    DB_PASS=$(echo $DB_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    DB_HOST=$(echo $DB_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DB_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_NAME=$(echo $DB_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
    
    print_status "Applying migrations to database: $DB_NAME"
    
    # Apply migrations
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f database_migration_video_streaming.sql
    
    if [ $? -eq 0 ]; then
        print_success "Database migrations applied successfully"
    else
        print_error "Failed to apply database migrations"
        exit 1
    fi
else
    print_warning ".env/DB_pass file not found. Please apply migrations manually:"
    print_warning "psql -h 127.0.0.1 -U deckport_app -d deckport -f database_migration_video_streaming.sql"
fi

# 4. Create necessary directories
print_status "Creating video storage directories..."

mkdir -p arena_videos
mkdir -p arena_thumbnails  
mkdir -p battle_recordings
mkdir -p surveillance_recordings

print_success "Video storage directories created"

# 5. Check if API server is running
print_status "Checking API server status..."

if curl -s http://127.0.0.1:8002/v1/health > /dev/null 2>&1; then
    print_success "API server is running"
else
    print_warning "API server is not running. Please start it:"
    print_warning "cd services/api && source venv/bin/activate && python wsgi.py"
fi

# 6. Check if frontend server is running
print_status "Checking frontend server status..."

if curl -s http://127.0.0.1:5000 > /dev/null 2>&1; then
    print_success "Frontend server is running"
else
    print_warning "Frontend server is not running. Please start it:"
    print_warning "cd frontend && python app.py"
fi

# 7. Make test script executable
print_status "Setting up test scripts..."

chmod +x test_video_streaming.py

print_success "Test scripts are ready"

# 8. Create sample test data (optional)
print_status "Creating sample test data..."

# Create a simple test request file for load testing
cat > arena_request.json << EOF
{
    "preferred_themes": ["nature", "crystal"],
    "preferred_rarities": ["rare", "epic"],
    "difficulty_preference": 5,
    "player_level": 10
}
EOF

print_success "Sample test data created"

# 9. Summary and next steps
echo ""
echo "========================================================"
print_success "Testing environment setup completed!"
echo "========================================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Start the API server (if not running):"
echo "   cd services/api && source venv/bin/activate && python wsgi.py"
echo ""
echo "2. Start the frontend server (if not running):"
echo "   cd frontend && python app.py"
echo ""
echo "3. Run the automated tests:"
echo "   python test_video_streaming.py"
echo ""
echo "4. Follow the manual testing guide:"
echo "   cat TESTING_GUIDE.md"
echo ""
echo "5. Access the admin surveillance dashboard:"
echo "   http://127.0.0.1:5000/admin/surveillance"
echo ""
echo "🔧 Troubleshooting:"
echo "- Check logs: journalctl -u api.service -f"
echo "- Database: psql -h 127.0.0.1 -U deckport_app -d deckport"
echo "- API health: curl http://127.0.0.1:8002/v1/health"
echo ""
print_success "Happy testing! 🧪"
