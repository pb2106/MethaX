#!/bin/bash
# MethaX Quick Setup Script

echo "🚀 MethaX Setup Script"
echo "======================"
echo ""

# Check if we're in the right directory
if [ ! -f ".env.example" ]; then
    echo "❌ Error: Must run from MethaX root directory"
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env created"
else
    echo "✓ .env already exists"
fi

# Navigate to backend
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "📦 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt

echo "✅ Dependencies installed"

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

echo "✅ Database initialized"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the server:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python run.py"
echo ""
echo "API will be available at:"
echo "  http://localhost:8000"
echo "  http://localhost:8000/docs (Interactive API docs)"
echo ""
