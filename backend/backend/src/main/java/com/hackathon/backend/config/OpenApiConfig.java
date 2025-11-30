package com.hackathon.backend.config;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Info;
import org.springframework.context.annotation.Configuration;

@Configuration
@OpenAPIDefinition(
        info = @Info(
                title = "Hackathon Backend API",
                version = "1.0",
                description = "API do obsługi użytkowników i generowania opisów"
        )
)
public class OpenApiConfig {
}
