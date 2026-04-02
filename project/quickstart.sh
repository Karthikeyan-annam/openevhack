#!/bin/bash
# Quick start script for Smart Waste Management Environment

set -e

echo "Smart Waste Management Environment - Quick Start"
echo "=================================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+.\d+')
echo "✓ Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null
echo "✓ Dependencies installed"

# Copy .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠ Edit .env file with your OpenAI API key"
fi

echo ""
echo "Ready to start!"
echo ""
echo "Options:"
echo "1. Run inference:    python inference.py"
echo "2. Start API server: python -m uvicorn app:app --reload"
echo ""
