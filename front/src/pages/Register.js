// src/pages/Register.js
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

function inferSexFromName(firstName) {
  if (!firstName) return null;
  const n = firstName.trim().toLowerCase();
  if (n.endsWith("a")) return "F";
  return "M";
}

function Register({ setUser }) {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    login: "",
    email: "",
    address: "",
    birthDate: "",
    password: "",
    confirmPassword: "",
    sex: "",
    locationLat: null,
    locationLng: null,
  });

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (form.password !== form.confirmPassword) {
      alert("Hasła nie są takie same.");
      return;
    }

    const userSex = form.sex || inferSexFromName(form.firstName);
    const userAge = form.birthDate;

    const payload = {
      userName: form.firstName,
      userSurname: form.lastName,
      userMail: form.email,
      userAge: userAge,
      userSex: userSex,
      userGeneratedGroup: null,
      userDescription: null,
      userLocationLatitude: form.locationLat,
      userLocationLongitude: form.locationLng,
      userPassword: form.password,
      userLogin: form.login,
    };

    console.log("Wysyłam do backendu (rejestracja):", payload);

    try {
      const res = await fetch(
        "https://continuable-manuela-podgy.ngrok-free.dev/api/users",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      if (!res.ok) {
        console.error("Status:", res.status);
        throw new Error("Błąd serwera przy rejestracji");
      }

      const data = await res.json();
      console.log("Odpowiedź backendu (rejestracja):", data);

      const userId = data.userId || data.id;

      setUser(data);
      localStorage.setItem("user", JSON.stringify(data));

      navigate(`/about-bot?userId=${userId}`);
    } catch (err) {
      console.error(err);
      alert("Nie udało się zarejestrować użytkownika. Spróbuj ponownie.");
    }
  };

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      alert("Twoja przeglądarka nie obsługuje geolokalizacji.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        const coordsText = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;

        setForm((prev) => ({
          ...prev,
          address: coordsText,
          locationLat: lat,
          locationLng: lng,
        }));
      },
      (err) => {
        console.error("Geolocation error:", err);
        if (err.code === 1) {
          alert(
            "Dostęp do lokalizacji został zablokowany. Zezwól na lokalizację w przeglądarce albo wpisz adres ręcznie."
          );
        } else if (err.code === 2) {
          alert(
            "Nie udało się ustalić pozycji. Spróbuj ponownie albo wpisz adres ręcznie."
          );
        } else if (err.code === 3) {
          alert(
            "Przekroczono czas oczekiwania na lokalizację. Spróbuj ponownie albo wpisz adres ręcznie."
          );
        } else {
          alert("Wystąpił błąd lokalizacji. Wpisz adres ręcznie.");
        }
      },
      { enableHighAccuracy: false, timeout: 10000 }
    );
  };

  return (
    <div className="row justify-content-center">
      <div className="col-lg-8 col-xl-6">
        <h2 className="mb-4">Rejestracja</h2>
        <form onSubmit={handleSubmit}>

          <div className="row">
            <div className="col-md-6 mb-3">
              <label className="form-label">Login</label>
              <input
                type="text"
                className="form-control"
                name="login"
                value={form.login}
                onChange={handleChange}
                required
              />
            </div>
            <div className="col-md-6 mb-3">
              <label className="form-label">E-mail</label>
              <input
                type="email"
                className="form-control"
                name="email"
                value={form.email}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="row">
            <div className="col-md-6 mb-3">
              <label className="form-label">Hasło</label>
              <input
                type="password"
                className="form-control"
                name="password"
                value={form.password}
                onChange={handleChange}
                required
              />
            </div>
            <div className="col-md-6 mb-3">
              <label className="form-label">Powtórz hasło</label>
              <input
                type="password"
                className="form-control"
                name="confirmPassword"
                value={form.confirmPassword}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="row">
            <div className="col-md-6 mb-3">
              <label className="form-label">Imię</label>
              <input
                type="text"
                className="form-control"
                name="firstName"
                value={form.firstName}
                onChange={handleChange}
                required
              />
            </div>
            <div className="col-md-6 mb-3">
              <label className="form-label">Nazwisko</label>
              <input
                type="text"
                className="form-control"
                name="lastName"
                value={form.lastName}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="mb-3">
            <label className="form-label">
              Adres / współrzędne (miasto, ulica lub GPS)
            </label>
            <div className="input-group">
              <input
                type="text"
                className="form-control"
                placeholder="np. Gliwice, ul. Akademicka 2 lub 50.12345, 18.12345"
                name="address"
                value={form.address}
                onChange={handleChange}
                required
              />
              <button
                type="button"
                className="btn btn-outline-success"
                onClick={handleGetLocation}
              >
                Lokalizuj
              </button>
            </div>
          </div>

          <div className="row">
            <div className="col-md-6 mb-3">
              <label className="form-label">Data urodzenia</label>
              <input
                type="date"
                className="form-control"
                name="birthDate"
                value={form.birthDate}
                onChange={handleChange}
                required
              />
            </div>

            <div className="col-md-6 mb-3">
              <label className="form-label">Płeć</label>
              <select
                className="form-select"
                name="sex"
                value={form.sex}
                onChange={handleChange}
              >
                <option value="">Nie chcę podawać</option>
                <option value="F">Kobieta</option>
                <option value="M">Mężczyzna</option>
                <option value="O">Inna</option>
              </select>
            </div>
          </div>

          <button type="submit" className="btn btn-success w-100">
            Zarejestruj się
          </button>
        </form>
      </div>
    </div>
  );
}

export default Register;
