package com.hackathon.backend.domain;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.Map;

@Getter
@Setter
@Builder
public class DescriptionDto {
    private Long id;
    private String text;
    private Map<String, Float> traits;
}
