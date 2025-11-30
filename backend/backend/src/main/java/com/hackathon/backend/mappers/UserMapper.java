package com.hackathon.backend.mappers;

import com.hackathon.backend.domain.AllFeaturesRequest;
import com.hackathon.backend.domain.DescriptionEntity;
import com.hackathon.backend.domain.UserDto;
import com.hackathon.backend.domain.UserEntity;
import com.hackathon.backend.repositories.DescriptionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Component
@RequiredArgsConstructor
public class UserMapper {

    private final DescriptionRepository descriptionRepository;

    public UserDto toDto(UserEntity entity) {
        if (entity == null) return null;

        return UserDto.builder()
                .userId(entity.getUserId())
                .userName(entity.getUserName())
                .userSurname(entity.getUserSurname())
                .userMail(entity.getUserMail())
                .userPassword(entity.getUserPassword())
                .userAge(entity.getUserAge())
                .userSex(entity.getUserSex())
                .userGeneratedGroup(entity.getUserGeneratedGroup())
                .descriptionId(
                        entity.getDescription() != null ? entity.getDescription().getId() : null
                )
                .userLocationLatitude(entity.getUserLocationLatitude())
                .userLocationLongitude(entity.getUserLocationLongitude())
                .build();
    }

    public UserEntity toEntity(UserDto dto) {
        if (dto == null) return null;

        DescriptionEntity description = null;
        if (dto.getDescriptionId() != null) {
            description = descriptionRepository.findById(dto.getDescriptionId())
                    .orElse(null);
        }

        return UserEntity.builder()
                .userId(dto.getUserId())
                .userName(dto.getUserName())
                .userSurname(dto.getUserSurname())
                .userMail(dto.getUserMail())
                .userPassword(dto.getUserPassword())
                .userAge(dto.getUserAge())
                .userSex(dto.getUserSex())
                .userGeneratedGroup(dto.getUserGeneratedGroup())
                .description(description)
                .userLocationLatitude(dto.getUserLocationLatitude())
                .userLocationLongitude(dto.getUserLocationLongitude())
                .build();
    }

    public AllFeaturesRequest toGroupFeatures(UserEntity entity) {
        if (entity == null) return null;

        Map<String, Float> traits = null;
        if (entity.getDescription() != null) {
            traits = entity.getDescription().getTraits();
        }

        return AllFeaturesRequest.builder()
                .groupId(0L)
                .userId(entity.getUserId())
                .topTraits(traits)
                .latitude(entity.getUserLocationLatitude())
                .longitude(entity.getUserLocationLongitude())
                .build();
    }
}
