package com.hackathon.backend.domain;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class CreateEventRequest {
    private List<Long> userIds;
    private String description;
    private Double latitude;
    private Double longitude;
}
