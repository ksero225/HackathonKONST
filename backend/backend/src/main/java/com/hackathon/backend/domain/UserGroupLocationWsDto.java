package com.hackathon.backend.domain;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class UserGroupLocationWsDto {
    private Long groupId;
    private List<Long> users;
    private List<String> topTraits;
    private Double latitude;
    private Double longitude;
}
