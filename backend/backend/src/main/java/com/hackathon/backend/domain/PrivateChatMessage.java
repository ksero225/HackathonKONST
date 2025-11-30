package com.hackathon.backend.domain;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class PrivateChatMessage {
    private Long senderId;
    private Long recipientId;
    private String content;
}
