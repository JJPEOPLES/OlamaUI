package com.ollama.chat.model;

import lombok.Data;

import java.util.List;

@Data
public class ModelsResponse {
    private List<ModelInfo> models;
}