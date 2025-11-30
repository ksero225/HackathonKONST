package com.hackathon.backend.config;

import com.hackathon.backend.domain.DescriptionEntity;
import com.hackathon.backend.domain.UserDto;
import com.hackathon.backend.domain.UserEntity;
import com.hackathon.backend.mappers.UserMapper;
import com.hackathon.backend.repositories.DescriptionRepository;
import com.hackathon.backend.repositories.UserRepository;
import com.hackathon.backend.services.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.util.*;

@Component
@RequiredArgsConstructor
public class DataInit implements CommandLineRunner {
    private final UserRepository userRepository;
    private final UserService userService;
    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;



    private static final Random RAND = new Random();

    private static final List<String> FIRST_NAMES = List.of(
            "Jan", "Anna", "Kamil", "Ola", "Marek", "Paweł", "Julia",
            "Karolina", "Piotr", "Ewa", "Maciej", "Natalia"
    );

    private static final List<String> LAST_NAMES = List.of(
            "Kowalski", "Nowak", "Wiśniewski", "Kamińska", "Jankowski",
            "Wójcik", "Mazur", "Lewandowska", "Zieliński"
    );

    private static final List<String> GROUPS = List.of(
            "SPORT", "KAWIARNIA", "PLANSZOWKI"
    );

    private static final List<String> TRAIT_POOL = List.of(
            "bieganie", "gry", "muzyka", "pływanie", "taniec",
            "jachty", "rower", "programowanie", "gotowanie"
    );

    @Override
    public void run(String... args) {
        //userRepository.deleteAll();

        List<UserEntity> users = new ArrayList<>();

        for (int i = 0; i < 100; i++) {
//            UserEntity entity = generateUser(i);
//            UserDto dto = userMapper.toDto(entity);
//            userService.createUser(dto);
            users.add(generateUser(i));
        }

        userRepository.saveAll(users);
    }

    private UserEntity generateUser(int index) {
        String first = random(FIRST_NAMES);
        String last = random(LAST_NAMES);

        String rawPassword = "pass";
        String encodedPassword = passwordEncoder.encode(rawPassword);

        String email = (first + "." + last + index + "@example.com").toLowerCase();

        // ---- Random Poland coordinates ----
        double lat = 51.5 + RAND.nextDouble() * (53.2 - 51.5); // Mazowieckie szerokość
        double lon = 19.0 + RAND.nextDouble() * (22.5 - 19.0); // Mazowieckie długość

        lat = round5(lat);
        lon = round5(lon);
        // -----------------------------------

        DescriptionEntity desc = new DescriptionEntity();
        desc.setText("Jestem " + first + ". Lubię różne aktywności! (" + index + ")");
        desc.setTraits(generateRandomTraits()); // 0.7–1.0

        return UserEntity.builder()
                .userName(first)
                .userSurname(last)
                .userMail(email)
                .userPassword(encodedPassword)
                .userAge(String.valueOf(18 + RAND.nextInt(30)))
                .userSex(RAND.nextBoolean() ? "M" : "F")
                .userGeneratedGroup(random(GROUPS))
                .description(desc)
                .userLocationLatitude(lat)
                .userLocationLongitude(lon)
                .build();
    }

    private double round5(double value) {
        return Math.round(value * 100000.0) / 100000.0;
    }
    private Map<String, Float> generateRandomTraits() {
        Map<String, Float> traits = new HashMap<>();

        int count = 3 + RAND.nextInt(5); // 3–7 cech

        // robimy mutowalną kopię, na której można zrobić shuffle
        List<String> shuffled = new ArrayList<>(TRAIT_POOL);
        Collections.shuffle(shuffled, RAND);

        for (int i = 0; i < count; i++) {
            float value = 0.7f + RAND.nextFloat() * 0.3f; // 0.7–1.0
            traits.put(shuffled.get(i), value);
        }

        return traits;
    }

    private <T> T random(List<T> list) {
        return list.get(RAND.nextInt(list.size()));
    }
}
