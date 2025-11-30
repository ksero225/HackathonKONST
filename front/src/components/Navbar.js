import React from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";

function Navbar({ user, onLogout }) {
  const navigate = useNavigate();

  const handleLogoutClick = () => {
    onLogout();
    navigate("/");
  };

  return (
    <nav
      className="navbar navbar-expand-lg navbar-light shadow-sm"
      style={{ backgroundColor: "var(--color1)" }}
    >
      <div className="container">
        <Link className="navbar-brand text-white fw-bold" to="/">
          ZróbmyToRazem
        </Link>

        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#mainNavbar"
          aria-controls="mainNavbar"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon" />
        </button>

        <div className="collapse navbar-collapse" id="mainNavbar">
          <ul className="navbar-nav ms-auto align-items-lg-center">
            {user ? (
              <>
                <li className="nav-item me-2">
                  <NavLink className="nav-link text-white" to="/panel">
                    Panel użytkownika
                  </NavLink>
                </li>
                <li className="nav-item">
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-light"
                    onClick={handleLogoutClick}
                  >
                    Wyloguj
                  </button>
                </li>
              </>
            ) : (
              <>
                <li className="nav-item">
                  <NavLink className="nav-link text-white" to="/login">
                    Zaloguj
                  </NavLink>
                </li>
                <li className="nav-item">
                  <NavLink className="nav-link text-white" to="/register">
                    Zarejestruj
                  </NavLink>
                </li>
              </>
            )}
          </ul>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
