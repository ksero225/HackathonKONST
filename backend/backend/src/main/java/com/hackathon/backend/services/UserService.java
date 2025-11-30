package com.hackathon.backend.services;

import com.hackathon.backend.domain.UserDto;
import com.hackathon.backend.domain.UserEntity;
import com.hackathon.backend.mappers.UserMapper;
import com.hackathon.backend.repositories.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;

    public UserDto createUser(UserDto dto) {
        UserEntity entity = userMapper.toEntity(dto);
        entity.setUserId(null);

        entity.setUserPassword(passwordEncoder.encode(dto.getUserPassword()));

        UserEntity saved = userRepository.save(entity);

        return userMapper.toDto(saved);
    }

    public UserDto getUserById(Long id) {
        UserEntity entity = userRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "User not found"));

        UserDto dto = userMapper.toDto(entity);
        dto.setUserPassword(null);

        return dto;
    }

    public UserDto login(String email, String rawPassword) {
        UserEntity user = userRepository.findUserByUserMail(email)
                .orElseThrow(() ->
                        new ResponseStatusException(HttpStatus.NOT_FOUND, "User not found"));

        if (!passwordEncoder.matches(rawPassword, user.getUserPassword())) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Invalid password");
        }

        UserDto dto = userMapper.toDto(user);

        dto.setUserPassword(null);
        return dto;
    }

    public void deleteUser(Long id) {
        if (!userRepository.existsById(id)) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "User with id " + id + " not found");
        }
        userRepository.deleteById(id);
    }

    public List<UserDto> getAllUsers() {
        return userRepository.findAll()
                .stream()
                .map(userMapper::toDto)
                .toList();
    }
}
