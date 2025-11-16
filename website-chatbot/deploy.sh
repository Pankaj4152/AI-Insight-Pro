#!/bin/bash

# AIInsightPro Chatbot Deployment Script
echo "🚀 Starting AIInsightPro Chatbot Deployment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded from .env"
else
    echo "❌ .env file not found. Please create it with your API keys."
    exit 1
fi

# Check if API keys are set
if [ -z "$GEMINI_API_KEY" ] || [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ API keys not found in .env file. Please check your configuration."
    exit 1
fi

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t aiinsightpro-chatbot . || {
    echo "❌ Docker build failed"
    exit 1
}

# Stop existing container if running
echo "🛑 Stopping existing container..."
docker stop aiinsightpro-chatbot 2>/dev/null || true
docker rm aiinsightpro-chatbot 2>/dev/null || true

# Run new container
echo "🚀 Starting new container..."
docker run -d \
  --name aiinsightpro-chatbot \
  -p 8080:8080 \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  -e CHROMA_DB_PATH="/app/chroma_db" \
  -v "$(pwd)/chroma_db:/app/chroma_db" \
  --restart unless-stopped \
  aiinsightpro-chatbot

# Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 10

# Test the deployment
echo "🧪 Testing deployment..."
if curl -f http://localhost:8080/api/health > /dev/null 2>&1; then
    echo "✅ Deployment successful! Chatbot is running at http://localhost:8080"
    echo "📋 API Endpoints:"
    echo "   - Health Check: http://localhost:8080/api/health"
    echo "   - Chat: POST http://localhost:8080/api/chat"
    echo ""
    echo "📝 Example usage:"
    echo 'curl -X POST "http://localhost:8080/api/chat" -H "Content-Type: application/json" -d '"'"'{"query": "What is AIInsightPro?"}'"'"
else
    echo "❌ Deployment failed. Check container logs:"
    docker logs aiinsightpro-chatbot
    exit 1
fi

echo "🎉 Deployment complete!"
