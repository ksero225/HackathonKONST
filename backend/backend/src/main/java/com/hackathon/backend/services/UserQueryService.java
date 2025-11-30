package com.hackathon.backend.services;

import com.hackathon.backend.domain.AllFeaturesRequest;
import com.hackathon.backend.mappers.UserMapper;
import com.hackathon.backend.repositories.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class UserQueryService {
    private final UserRepository userRepository;
    private final UserMapper userMapper;

    public List<AllFeaturesRequest> getAllUsersWithTraitsAndLocation(){
        return userRepository.findAll()
                .stream()
                .map(userMapper::toGroupFeatures)
                .toList();
    }
}
