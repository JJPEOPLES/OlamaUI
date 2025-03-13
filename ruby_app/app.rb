require 'sinatra'
require 'sinatra/json'
require 'json'
require 'faraday'
require 'faraday_middleware'

# Configuration
set :port, 4567
set :bind, '0.0.0.0'
set :public_folder, File.dirname(__FILE__) + '/public'
set :ollama_api_url, ENV['OLLAMA_API_URL'] || 'http://localhost:11434/api'

# Initialize Faraday client for Ollama API
def ollama_client
  @ollama_client ||= Faraday.new(url: settings.ollama_api_url) do |faraday|
    faraday.request :json
    faraday.response :json
    faraday.adapter Faraday.default_adapter
  end
end

# Routes
get '/' do
  erb :index
end

# Get available models
get '/api/models' do
  begin
    response = ollama_client.get('tags')
    json response.body
  rescue => e
    status 500
    json error: "Failed to fetch models: #{e.message}"
  end
end

# Chat with a model
post '/api/chat' do
  begin
    request_payload = JSON.parse(request.body.read)

    model = request_payload['model']
    messages = request_payload['messages'] || []
    options = request_payload['options'] || {}

    # Prepare the request to Ollama
    ollama_payload = {
      model: model,
      messages: messages,
      stream: false
    }

    # Add options if provided
    if options.any?
      ollama_payload[:options] = options
    end

    # Send request to Ollama
    response = ollama_client.post('chat', ollama_payload.to_json)

    # Return the response
    json response.body
  rescue => e
    status 500
    json error: "Chat request failed: #{e.message}"
  end
end

# Version info
get '/api/version' do
  json version: "1.0.0",
       ollama_url: settings.ollama_api_url,
       ruby_version: RUBY_VERSION
end

# Error handling
error do
  status 500
  json error: env['sinatra.error'].message
end