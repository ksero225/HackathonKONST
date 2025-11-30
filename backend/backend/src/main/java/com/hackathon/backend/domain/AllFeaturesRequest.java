package com.hackathon.backend.domain;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.List;
import java.util.Map;

@Getter
@Setter
@Builder
public class AllFeaturesRequest {
    private Long groupId;
    private Long userId;
    private Map<String, Float> topTraits;
    private Double latitude;
    private Double longitude;
}
