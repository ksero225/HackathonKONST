package com.hackathon.backend.services;

import com.hackathon.backend.domain.CreateEventRequest;
import com.hackathon.backend.domain.EventEntity;
import com.hackathon.backend.domain.EventSummaryDto;
import com.hackathon.backend.domain.UserEntity;
import com.hackathon.backend.mappers.EventMapper;
import com.hackathon.backend.repositories.EventRepository;
import com.hackathon.backend.repositories.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Service
@RequiredArgsConstructor
public class EventService {
    private final EventRepository eventRepository;
    private final UserRepository userRepository;
    private final EventMapper eventMapper;

    public EventSummaryDto createEvent(CreateEventRequest request) {
        List<UserEntity> users = userRepository.findAllById(request.getUserIds());
        Set<UserEntity> userSet = new HashSet<>(users);

        EventEntity event = EventEntity.builder()
                .description(request.getDescription())
                .latitude(request.getLatitude())
                .longitude(request.getLongitude())
                .users(userSet)
                .build();

        EventEntity saved = eventRepository.save(event);
        return eventMapper.toDto(saved);
    }

    public EventSummaryDto getEventById(Long eventId) {
        EventEntity event = eventRepository.findById(eventId)
                .orElseThrow(() -> new RuntimeException("Event not found: " + eventId));

        return eventMapper.toDto(event);
    }

    public List<EventSummaryDto> getEventsForUser(Long userId) {
        List<EventEntity> events = eventRepository.findEventsByUserId(userId);
        return events.stream()
                .map(eventMapper::toDto)
                .toList();
    }

    public boolean isUserInEvent(Long eventId, Long userId) {
        return eventRepository.existsByIdAndUsers_UserId(eventId, userId);
    }
}
