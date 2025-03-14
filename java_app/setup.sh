#!/bin/bash
# Setup script for Ollama Chat Java App

echo "Setting up Ollama Chat Java App..."

# Check if Java is installed
if ! command -v java &> /dev/null; then
    echo "Java is not installed. Please install Java 11+ and try again."
    exit 1
fi

# Check Java version
JAVA_VERSION=$(java -version 2>&1 | awk -F '"' '/version/ {print $2}')
echo "Detected Java version: $JAVA_VERSION"

# Check if Maven is installed
if ! command -v mvn &> /dev/null; then
    echo "Maven is not installed. Please install Maven 3.6+ and try again."
    exit 1
fi

# Build the application
echo "Building the application (this may take a moment)..."
mvn clean package -DskipTests

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Build successful!"
    echo ""
    echo "To start the application, run:"
    echo "java -jar target/chat-1.0.0.jar"
    echo ""
    echo "Then visit http://localhost:8080 in your browser."
else
    echo "Build failed. Please check the error messages above."
    exit 1
fi