// src/pages/Home.js
import React from "react";
import { Link } from "react-router-dom";

function Home() {
  return (
    <div className="row align-items-center">
      <div className="col-md-6 mb-4 mb-md-0">
        <h1 className="mb-3">Zróbmy to razem</h1>
        <p className="lead">
          Aplikacja, która dobiera Ci ludzi i misje w czasie rzeczywistym. 
          Bieganie, escape roomy, wspólna nauka – wszystko w jednym miejscu.
        </p>
        <div className="d-flex flex-wrap gap-2 mt-4">
          <Link to="/register" className="btn btn-lg btn-success">
            Zarejestruj się
          </Link>
          <Link to="/login" className="btn btn-lg btn-outline-success">
            Zaloguj się
          </Link>
        </div>
      </div>

      {/* PRAWY BOK – FEJKOWE STATY, MNIEJSZE KAFELKI */}
      <div className="col-md-6 mb-4 mb-md-0">
        <div className="stats-panel p-3 p-sm-4 rounded-3 h-100">
          <div className="row row-cols-2 g-3">
            <div className="col">
              <div className="stat-card rounded-3 p-3 h-100">
                <p className="mb-1 small text-muted text-uppercase stat-card-label">
                  Aktywne wydarzenia
                </p>
                <p className="mb-0 fw-bold stat-card-value">128</p>
              </div>
            </div>
            <div className="col">
              <div className="stat-card rounded-3 p-3 h-100">
                <p className="mb-1 small text-muted text-uppercase stat-card-label">
                  Aktywni użytkownicy
                </p>
                <p className="mb-0 fw-bold stat-card-value">742</p>
              </div>
            </div>
            <div className="col">
              <div className="stat-card rounded-3 p-3 h-100">
                <p className="mb-1 small text-muted text-uppercase stat-card-label">
                  Miasta w radarze
                </p>
                <p className="mb-0 fw-bold stat-card-value">23</p>
              </div>
            </div>
            <div className="col">
              <div className="stat-card rounded-3 p-3 h-100">
                <p className="mb-1 small text-muted text-uppercase stat-card-label">
                  Spotkania dziś
                </p>
                <p className="mb-0 fw-bold stat-card-value">39</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* SEKCJA Z FICZERAMI */}
      <div className="col-12 mt-5">
        <h2 className="h4 mb-3 text-center">Co potrafi AI Mission Radar?</h2>
        <p className="text-center text-muted mb-4">
          Kilka rzeczy, które dzieją się w tle, kiedy po prostu szukasz ludzi do działania.
        </p>

        <div className="row g-3">
          <div className="col-12 col-sm-6 col-lg-3">
            <div className="feature-card feature-card-delay-1 h-100 text-center p-3 rounded-3">
              <div className="feature-icon mb-2" aria-hidden="true">
                🔍
              </div>
              <h3 className="h6 mb-1">Dopasowywanie ludzi</h3>
              <p className="small text-muted mb-0">
                Łączymy Cię z osobami o podobnych celach, tempie i stylu spędzania czasu.
              </p>
            </div>
          </div>

          <div className="col-12 col-sm-6 col-lg-3">
            <div className="feature-card feature-card-delay-2 h-100 text-center p-3 rounded-3">
              <div className="feature-icon mb-2" aria-hidden="true">
                🧠
              </div>
              <h3 className="h6 mb-1">Inteligentny bot</h3>
              <p className="small text-muted mb-0">
                Krótka rozmowa wystarczy, by zbudować Twój profil i zasugerować odpowiednie misje.
              </p>
            </div>
          </div>

          <div className="col-12 col-sm-6 col-lg-3">
            <div className="feature-card feature-card-delay-3 h-100 text-center p-3 rounded-3">
              <div className="feature-icon mb-2" aria-hidden="true">
                🚀
              </div>
              <h3 className="h6 mb-1">Misje w czasie rzeczywistym</h3>
              <p className="small text-muted mb-0">
                Widzisz, co dzieje się teraz w Twojej okolicy – nie tylko statyczne ogłoszenia.
              </p>
            </div>
          </div>

          <div className="col-12 col-sm-6 col-lg-3">
            <div className="feature-card feature-card-delay-4 h-100 text-center p-3 rounded-3">
              <div className="feature-icon mb-2" aria-hidden="true">
                🤝
              </div>
              <h3 className="h6 mb-1">Budowanie grup</h3>
              <p className="small text-muted mb-0">
                Z pojedynczych misji tworzą się stałe ekipy – do biegania, nauki albo grania.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;
