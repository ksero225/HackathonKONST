package com.hackathon.backend.domain;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.HashMap;
import java.util.Map;

@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "desciptions")
public class DescriptionEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 2048)
    private String text;

    @ElementCollection
    @CollectionTable(
            name = "description_traits",
            joinColumns = @JoinColumn(name = "description_id")
    )
    @MapKeyColumn(name = "trait_name")
    @Column(name = "trait_value")
    private Map<String, Float> traits = new HashMap<>();

}
