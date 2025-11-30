package com.hackathon.backend.domain;

import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
public class LoginDto {
    private String userLogin;
    private String userPassword;
}
