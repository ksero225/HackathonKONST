package com.hackathon.backend.domain;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@Builder
public class EventSummaryDto {
    private Long eventId;
    private List<Long> userIds;
    private String description;
    private Double latitude;
    private Double longitude;
}
