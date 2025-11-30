package com.hackathon.backend.mappers;

import com.hackathon.backend.domain.EventEntity;
import com.hackathon.backend.domain.EventSummaryDto;
import com.hackathon.backend.domain.UserEntity;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class EventMapper {
    public EventSummaryDto toDto(EventEntity entity) {
        if (entity == null) return null;

        List<Long> userIds = entity.getUsers()
                .stream()
                .map(UserEntity::getUserId)
                .toList();

        return EventSummaryDto.builder()
                .eventId(entity.getId())
                .userIds(userIds)
                .description(entity.getDescription())
                .latitude(entity.getLatitude())
                .longitude(entity.getLongitude())
                .build();
    }
}
