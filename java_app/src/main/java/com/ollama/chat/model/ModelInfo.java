package com.ollama.chat.model;

import lombok.Data;

@Data
public class ModelInfo {
    private String name;
    private String modified_at;
    private long size;
    private String digest;
}