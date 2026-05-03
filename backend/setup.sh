#!/bin/bash

# Setup script for Linux/Mac - Gym Management System Backend

echo ""
echo "============================================"
echo " Gym Management System - Backend Setup"
echo "============================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "[1/5] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error creating virtual environment"
    exit 1
fi

echo "[2/5] Activating virtual environment..."
source venv/bin/activate

echo "[3/5] Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error installing dependencies"
    exit 1
fi

echo "[4/5] Copying .env template..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file - please update with your database credentials"
fi

echo "[5/5] Creating database tables..."
python -c "from database import init_db; init_db(); print('Database initialized')"

echo ""
echo "============================================"
echo " Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Update .env with your PostgreSQL credentials"
echo "  2. Run: python seed_data.py (to populate demo data)"
echo "  3. Run: uvicorn main:app --reload"
echo ""
echo "Backend will be available at: http://localhost:8000"
echo "API Docs at: http://localhost:8000/docs"
echo ""
