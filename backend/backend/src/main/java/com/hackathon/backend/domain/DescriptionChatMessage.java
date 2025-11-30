package com.hackathon.backend.domain;

import lombok.*;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class DescriptionChatMessage {
    private Long userId;
    private String content;
}
