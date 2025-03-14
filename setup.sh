#!/bin/bash
# Setup script for Ollama Chat JS App

echo "Setting up Ollama Chat JS App..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js 14+ and try again."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d 'v' -f 2 | cut -d '.' -f 1)
echo "Detected Node.js version: $(node -v)"

if [ "$NODE_VERSION" -lt 14 ]; then
    echo "Node.js version 14 or higher is required. Please upgrade Node.js and try again."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install npm and try again."
    exit 1
fi

# Install dependencies
echo "Installing dependencies (this may take a moment)..."
npm install

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "Dependencies installed successfully!"
    echo ""
    echo "To start the application, run:"
    echo "npm start"
    echo ""
    echo "Then visit http://localhost:3000 in your browser."
else
    echo "Failed to install dependencies. Please check the error messages above."
    exit 1
fi