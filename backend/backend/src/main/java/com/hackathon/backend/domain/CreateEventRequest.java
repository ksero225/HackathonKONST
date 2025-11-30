package com.hackathon.backend.domain;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class CreateEventRequest {
    private List<Long> userIds;   // ID użytkowników przypisanych do wydarzenia
    private String description;   // opis wydarzenia
    private Double latitude;      // miejsce (np. środek ciężkości)
    private Double longitude;
}
