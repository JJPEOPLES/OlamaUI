package com.ollama.chat.controller;

import com.ollama.chat.config.AppConfig;
import com.ollama.chat.model.ModelInfo;
import com.ollama.chat.service.OllamaService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.List;

@Controller
@RequiredArgsConstructor
public class WebController {

    private final OllamaService ollamaService;
    private final AppConfig appConfig;

    @GetMapping("/")
    public String index(Model model) {
        List<ModelInfo> models = ollamaService.getModels();
        model.addAttribute("models", models);
        model.addAttribute("apiUrl", appConfig.getOllamaApiUrl());
        return "index";
    }
}