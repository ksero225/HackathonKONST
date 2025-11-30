package com.hackathon.backend.repositories;

import com.hackathon.backend.domain.DescriptionEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface DescriptionRepository extends JpaRepository<DescriptionEntity, Long> {
}
