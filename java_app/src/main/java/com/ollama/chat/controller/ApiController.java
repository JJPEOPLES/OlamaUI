package com.ollama.chat.controller;

import com.ollama.chat.model.ChatMessage;
import com.ollama.chat.model.ChatResponse;
import com.ollama.chat.model.ModelInfo;
import com.ollama.chat.service.OllamaService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class ApiController {

    private final OllamaService ollamaService;

    @GetMapping("/models")
    public ResponseEntity<List<ModelInfo>> getModels() {
        return ResponseEntity.ok(ollamaService.getModels());
    }

    @PostMapping("/chat")
    public ResponseEntity<ChatResponse> chat(@RequestBody Map<String, Object> request) {
        String model = (String) request.get("model");
        @SuppressWarnings("unchecked")
        List<ChatMessage> messages = (List<ChatMessage>) request.get("messages");
        
        // Get options with defaults
        Map<String, Object> options = request.containsKey("options") ? 
            (Map<String, Object>) request.get("options") : new HashMap<>();
        
        double temperature = options.containsKey("temperature") ? 
            Double.parseDouble(options.get("temperature").toString()) : 0.7;
        
        int maxTokens = options.containsKey("num_predict") ? 
            Integer.parseInt(options.get("num_predict").toString()) : 1024;
        
        ChatResponse response = ollamaService.chat(model, messages, temperature, maxTokens);
        
        if (response.getError() != null) {
            return ResponseEntity.badRequest().body(response);
        }
        
        return ResponseEntity.ok(response);
    }

    @GetMapping("/version")
    public ResponseEntity<Map<String, String>> getVersion() {
        Map<String, String> version = new HashMap<>();
        version.put("version", "1.0.0");
        version.put("java_version", System.getProperty("java.version"));
        return ResponseEntity.ok(version);
    }
}