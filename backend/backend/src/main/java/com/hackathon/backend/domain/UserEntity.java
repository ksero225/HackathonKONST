package com.hackathon.backend.domain;

import jakarta.persistence.*;
import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Entity
@Table(name = "users")
public class UserEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long userId;

    @Column(nullable = false)
    private String userName;

    @Column(nullable = false)
    private String userSurname;

    @Column(nullable = false)
    private String userMail;

    @Column
    private Integer userAge;

    @Column
    private String userSex;

    @Column
    private String userGeneratedGroup;

    @Column(length = 1024)
    private String userDescription;

    @Column(nullable = false)
    private Double userLocationLatitude;

    @Column(nullable = false)
    private Double userLocationLongitude;
}
