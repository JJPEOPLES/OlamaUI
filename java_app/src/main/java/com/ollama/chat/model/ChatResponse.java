package com.ollama.chat.model;

import lombok.Data;

@Data
public class ChatResponse {
    private ChatMessage message;
    private String model;
    private String created_at;
    private boolean done;
    private String error;
}