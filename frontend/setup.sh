#!/bin/bash

# Setup script for Linux/Mac - Gym Management System Frontend

echo ""
echo "============================================"
echo " Gym Management System - Frontend Setup"
echo "============================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

echo "Node.js version:"
node --version

echo ""
echo "[1/3] Installing dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "Error installing dependencies"
    exit 1
fi

echo "[2/3] Configuration complete."

echo "[3/3] Build check..."
npm run build
if [ $? -ne 0 ]; then
    echo "Warning: Build had issues, but dev server can still run"
fi

echo ""
echo "============================================"
echo " Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Start backend: cd ../backend && uvicorn main:app --reload"
echo "  2. Run: npm run dev"
echo ""
echo "Frontend will be available at: http://localhost:5173"
echo ""
