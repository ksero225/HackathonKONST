package com.hackathon.backend.domain;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class EventChatMessage {
    private Long eventId;
    private Long senderId;
    private String content;
}
