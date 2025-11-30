package com.hackathon.backend.controllers;

import com.hackathon.backend.domain.CreateEventRequest;
import com.hackathon.backend.domain.EventSummaryDto;
import com.hackathon.backend.services.EventService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/events")
@RequiredArgsConstructor
public class EventController {
    private final EventService eventService;

    @PostMapping
    public ResponseEntity<EventSummaryDto> createEvent(@RequestBody CreateEventRequest request) {
        EventSummaryDto dto = eventService.createEvent(request);
        return ResponseEntity.ok(dto);
    }

    @GetMapping("/{id}")
    public ResponseEntity<EventSummaryDto> getEvent(@PathVariable Long id) {
        EventSummaryDto dto = eventService.getEventById(id);
        return ResponseEntity.ok(dto);
    }

    @GetMapping("/users/{userId}/events")
    public ResponseEntity<List<EventSummaryDto>> getEventsForUser(@PathVariable Long userId) {
        List<EventSummaryDto> events = eventService.getEventsForUser(userId);
        return ResponseEntity.ok(events);
    }
}
