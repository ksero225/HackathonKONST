// src/App.js
import React, { useEffect, useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import UserPanel from "./pages/UserPanel";
import AboutBot from "./pages/AboutBot";
import Navbar from "./components/Navbar";
import ThemeControls from "./components/ThemeControls";

function RequireProfileDescription({ user, children }) {
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const userId = user.userId || user.id;

  if (!user.userDescription) {
    return (
      <Navigate
        to={`/about-bot?userId=${userId}`}
        replace
      />
    );
  }

  return children;
}

function App() {
  const [theme, setTheme] = useState("light");
  const [contrast, setContrast] = useState("normal");
  const [fontSize, setFontSize] = useState("medium");

  const [user, setUser] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem("user");
      }
    }
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute("data-theme", theme);
    root.setAttribute("data-contrast", contrast === "high" ? "high" : "normal");
  }, [theme, contrast]);

  useEffect(() => {
    const root = document.documentElement;
    if (fontSize === "small") {
      root.style.setProperty("--font-size-base", "14px");
    } else if (fontSize === "large") {
      root.style.setProperty("--font-size-base", "18px");
    } else {
      root.style.setProperty("--font-size-base", "16px");
    }
  }, [fontSize]);

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("user");
  };

  return (
    <div className="app min-vh-100 d-flex flex-column">
      <Navbar user={user} onLogout={handleLogout} />
      <div className="container flex-grow-1 py-4">
        <ThemeControls
          theme={theme}
          setTheme={setTheme}
          contrast={contrast}
          setContrast={setContrast}
          fontSize={fontSize}
          setFontSize={setFontSize}
        />

        <Routes>
          <Route path="/" element={<Home />} />

          <Route
            path="/login"
            element={
              user
                ? <Navigate to="/panel" replace />
                : <Login setUser={setUser} />
            }
          />

          <Route
            path="/register"
            element={<Register setUser={setUser} />}
          />

          {/* PANEL – wymaga usera **i** opisu z bota */}
          <Route
            path="/panel"
            element={
              <RequireProfileDescription user={user}>
                <UserPanel user={user} />
              </RequireProfileDescription>
            }
          />

          {/* ABOUT-BOT – tu nie blokujemy, bo tu właśnie robimy opis */}
          <Route
  path="/about-bot"
  element={<AboutBot user={user} setUser={setUser} />}
/>

        </Routes>
      </div>
      <footer className="text-center py-3 small text-muted">
        &copy; {new Date().getFullYear()} AI Mission Radar
      </footer>
    </div>
  );
}

export default App;
