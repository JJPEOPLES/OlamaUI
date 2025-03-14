package com.ollama.chat.model;

import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
public class ChatRequest {
    private String model;
    private List<ChatMessage> messages;
    private boolean stream = false;
    private Map<String, Object> options;
}