package com.hackathon.backend.repositories;

import com.hackathon.backend.domain.EventEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface EventRepository extends JpaRepository<EventEntity, Long> {
    @Query("SELECT e FROM EventEntity e JOIN e.users u WHERE u.userId = :userId")
    List<EventEntity> findEventsByUserId(@Param("userId") Long userId);

    boolean existsByIdAndUsers_UserId(Long id, Long userId);


}
