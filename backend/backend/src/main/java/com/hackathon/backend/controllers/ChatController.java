package com.hackathon.backend.controllers;

import com.hackathon.backend.domain.DescriptionChatMessage;
import com.hackathon.backend.domain.EventChatMessage;
import com.hackathon.backend.services.EventService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Controller;

@Controller
@RequiredArgsConstructor
public class ChatController {
    private final SimpMessagingTemplate messagingTemplate;
    private final EventService eventService;

    @MessageMapping("/event-chat")
    public void handleEventChat(EventChatMessage message) {
        System.out.println("WS event-chat | eventId=" + message.getEventId()
                + " senderId=" + message.getSenderId()
                + " content=" + message.getContent());

        boolean allowed = eventService.isUserInEvent(
                message.getEventId(),
                message.getSenderId()
        );

        if (!allowed) {
            System.out.println("User " + message.getSenderId()
                    + " nie należy do eventu " + message.getEventId()
                    + " – odrzucam wiadomość");
            return;
        }

        String destination = "/topic/event-chat." + message.getEventId();
        messagingTemplate.convertAndSend(destination, message);
    }
}
