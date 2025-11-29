package com.hackathon.backend.mappers;

import com.hackathon.backend.domain.UserDto;
import com.hackathon.backend.domain.UserEntity;
import org.springframework.stereotype.Component;

@Component
public class UserMapper {

    public UserDto toDto(UserEntity entity) {
        if (entity == null) return null;

        return UserDto.builder()
                .userId(entity.getUserId())
                .userName(entity.getUserName())
                .userSurname(entity.getUserSurname())
                .userMail(entity.getUserMail())
                .userAge(entity.getUserAge())
                .userSex(entity.getUserSex())
                .userGeneratedGroup(entity.getUserGeneratedGroup())
                .userDescription(entity.getUserDescription())
                .userLocationLatitude(entity.getUserLocationLatitude())
                .userLocationLongitude(entity.getUserLocationLongitude())
                .build();
    }

    public UserEntity toEntity(UserDto dto) {
        if (dto == null) return null;

        return UserEntity.builder()
                .userId(dto.getUserId())
                .userName(dto.getUserName())
                .userSurname(dto.getUserSurname())
                .userMail(dto.getUserMail())
                .userAge(dto.getUserAge())
                .userSex(dto.getUserSex())
                .userGeneratedGroup(dto.getUserGeneratedGroup())
                .userDescription(dto.getUserDescription())
                .userLocationLatitude(dto.getUserLocationLatitude())
                .userLocationLongitude(dto.getUserLocationLongitude())
                .build();
    }
}
