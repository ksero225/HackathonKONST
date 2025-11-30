import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

function Login({ setUser }) {
  const navigate = useNavigate();

  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const payload = {
      userLogin: login,
      userPassword: password,
    };

    console.log("Wysyłam dane logowania:", payload);

    try {
      const res = await fetch(
        "https://continuable-manuela-podgy.ngrok-free.dev/api/users/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      if (!res.ok) {
        console.error("Status logowania:", res.status);
        setError("Nieprawidłowy login lub hasło.");
        return;
      }

      const data = await res.json();
      console.log("Odpowiedź logowania:", data);

      setUser(data);
      localStorage.setItem("user", JSON.stringify(data));

      navigate("/panel");
    } catch (err) {
      console.error("Błąd połączenia przy logowaniu:", err);
      setError("Problem z połączeniem z serwerem. Spróbuj ponownie.");
    }
  };

  return (
    <div className="row justify-content-center">
      <div className="col-md-6 col-lg-4">
        <h2 className="mb-4">Logowanie</h2>

        {error && (
          <div className="alert alert-danger py-2">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">Login</label>
            <input
              type="text"
              className="form-control"
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              required
            />
          </div>
          <div className="mb-3">
            <label className="form-label">Hasło</label>
            <input
              type="password"
              className="form-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn btn-success w-100 mb-3">
            Zaloguj
          </button>
        </form>
      </div>
    </div>
  );
}

export default Login;
