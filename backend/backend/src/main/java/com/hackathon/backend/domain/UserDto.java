package com.hackathon.backend.domain;

import jakarta.persistence.Column;
import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserDto {
    private Long userId;
    private String userName;
    private String userSurname;
    private String userMail;
    private String userPassword;
    private String userAge;
    private String userSex;
    private String userGeneratedGroup;
    private Long descriptionId;
    private Double userLocationLatitude;
    private Double userLocationLongitude;
}
