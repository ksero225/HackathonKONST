package com.hackathon.backend.controllers;

import com.hackathon.backend.domain.*;
import com.hackathon.backend.repositories.DescriptionRepository;
import com.hackathon.backend.repositories.UserRepository;
import com.hackathon.backend.services.UserQueryService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserDescriptionController {
    private final UserRepository userRepository;
    private final DescriptionRepository descriptionRepository;

    @MessageMapping("/description")
    @SendTo("/topic/description")
    public ResponseEntity<DescriptionChatMessage> handleDescription(DescriptionChatMessage inMessage) {
        System.out.println("WS odebrano: " + inMessage);
        return ResponseEntity.ok(inMessage);
    }

    @MessageMapping("/groups")
    @SendTo("/topic/groups")
    public List<UserGroupLocationWsDto> handleUsersGroups(List<UserGroupLocationWsDto> users) {
        return users;
    }

    @PutMapping("/{userId}/description")
    public ResponseEntity<DescriptionDto> updateDescription(
            @PathVariable Long userId,
            @RequestBody DescriptionUpdateRequest request
    ) {

        UserEntity user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found: " + userId));

        DescriptionEntity description = user.getDescription();
        if (description == null) {
            description = new DescriptionEntity();
        }

        description.setText(request.getText());
        description.setTraits(request.getTraits());

        description = descriptionRepository.save(description);

        user.setDescription(description);
        userRepository.save(user);

        DescriptionDto response = DescriptionDto.builder()
                .id(description.getId())
                .text(description.getText())
                .traits(description.getTraits())
                .build();

        System.out.println("response: " + response);

        return ResponseEntity.ok(response);
    }

    private final UserQueryService userQueryService;

    @GetMapping("/features")
    public List<AllFeaturesRequest> getUsersFeaturesAndLocations(){
        return userQueryService.getAllUsersWithTraitsAndLocation();
    }
}
