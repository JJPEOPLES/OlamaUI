package com.ollama.chat.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AppConfig {

    @Value("${ollama.api.url:http://localhost:11434/api}")
    private String ollamaApiUrl;

    public String getOllamaApiUrl() {
        return ollamaApiUrl;
    }
}