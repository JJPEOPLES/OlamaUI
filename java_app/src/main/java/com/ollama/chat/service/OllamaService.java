package com.ollama.chat.service;

import com.ollama.chat.config.AppConfig;
import com.ollama.chat.model.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class OllamaService {

    private final RestTemplate restTemplate;
    private final AppConfig appConfig;

    /**
     * Get available models from Ollama
     */
    public List<ModelInfo> getModels() {
        try {
            String url = appConfig.getOllamaApiUrl() + "/tags";
            ModelsResponse response = restTemplate.getForObject(url, ModelsResponse.class);
            return response != null ? response.getModels() : Collections.emptyList();
        } catch (RestClientException e) {
            log.error("Error fetching models from Ollama", e);
            return Collections.emptyList();
        }
    }

    /**
     * Send a chat request to Ollama
     */
    public ChatResponse chat(String model, List<ChatMessage> messages, double temperature, int maxTokens) {
        try {
            String url = appConfig.getOllamaApiUrl() + "/chat";
            
            // Create request body
            ChatRequest request = new ChatRequest();
            request.setModel(model);
            request.setMessages(messages);
            
            // Set options
            Map<String, Object> options = new HashMap<>();
            options.put("temperature", temperature);
            options.put("num_predict", maxTokens);
            request.setOptions(options);
            
            // Set headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<ChatRequest> entity = new HttpEntity<>(request, headers);
            
            // Make the request
            return restTemplate.postForObject(url, entity, ChatResponse.class);
        } catch (RestClientException e) {
            log.error("Error sending chat request to Ollama", e);
            ChatResponse errorResponse = new ChatResponse();
            errorResponse.setError("Failed to communicate with Ollama API: " + e.getMessage());
            return errorResponse;
        }
    }
}