# Ollama Chat - Java Implementation

A Spring Boot web application for interacting with Ollama models.

## Requirements

- Java 11 or higher
- Maven 3.6 or higher
- Ollama installed and running on your machine

## Quick Start

### Building the Application

```bash
# Navigate to the java_app directory
cd java_app

# Build the application
mvn clean package

# Run the application
java -jar target/chat-1.0.0.jar
```

### Using Maven Spring Boot Plugin

```bash
# Navigate to the java_app directory
cd java_app

# Run the application directly with Maven
mvn spring-boot:run
```

## Configuration

The application is configured to connect to Ollama at `http://localhost:11434/api` by default. You can change this by:

1. Editing `src/main/resources/application.properties`
2. Setting the `ollama.api.url` property when running the application:

```bash
java -jar target/chat-1.0.0.jar --ollama.api.url=http://your-ollama-server:11434/api
```

## Features

- Chat with any model available in your Ollama installation
- Adjust temperature and other generation parameters
- Attach files to provide context to the model
- Insert code snippets with syntax highlighting
- Step-by-step reasoning toggle
- Save chat histories to JSON files
- Responsive design that works on mobile and desktop
- Markdown and code syntax highlighting

## API Endpoints

- `GET /api/models` - Get available models
- `POST /api/chat` - Send a chat message
- `GET /api/version` - Get version information

## Development

This application is built with:

- Spring Boot 2.7.x
- Thymeleaf for server-side templating
- Bootstrap 5 for responsive UI
- jQuery for DOM manipulation
- Marked.js for Markdown rendering
- Highlight.js for code syntax highlighting

To modify the application:

1. Edit the Java files in `src/main/java/com/ollama/chat/`
2. Edit the HTML templates in `src/main/resources/templates/`
3. Edit the static resources in `src/main/resources/static/`

## Troubleshooting

### Connection Issues

Make sure Ollama is running:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags
```

### Port Conflicts

If port 8080 is already in use, you can change it:

```bash
# Change the port to 8081
java -jar target/chat-1.0.0.jar --server.port=8081
```

Or edit `application.properties` to set a different port.