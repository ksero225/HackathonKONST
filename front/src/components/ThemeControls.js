// src/components/ThemeControls.js
import React from "react";

function ThemeControls({ theme, setTheme, contrast, setContrast, fontSize, setFontSize }) {
  // tryb wizualny: 3 stany na podstawie theme + contrast
  let mode;
  if (contrast === "high") {
    mode = "high";           // Wysoki kontrast
  } else if (theme === "dark") {
    mode = "dark";           // Ciemny
  } else {
    mode = "light";          // Jasny (domyślnie)
  }

  const activateLight = () => {
    setTheme("light");
    setContrast("normal");
  };

  const activateDark = () => {
    setTheme("dark");
    setContrast("normal");
  };

  const activateHighContrast = () => {
    // wybieramy jasny + wysoki kontrast
    setTheme("light");
    setContrast("high");
  };

  return (
    <div className="d-flex flex-wrap gap-2 justify-content-end mb-3">
      {/* Jasny / Ciemny / Wysoki kontrast */}
      <div className="btn-group" role="group" aria-label="Motyw">
        <button
          className={`btn btn-sm ${mode === "light" ? "btn-success" : "btn-outline-success"}`}
          onClick={activateLight}
        >
          Jasny
        </button>
        <button
          className={`btn btn-sm ${mode === "dark" ? "btn-success" : "btn-outline-success"}`}
          onClick={activateDark}
        >
          Ciemny
        </button>
        <button
          className={`btn btn-sm ${mode === "high" ? "btn-success" : "btn-outline-success"}`}
          onClick={activateHighContrast}
        >
          Wysoki kontrast
        </button>
      </div>

      {/* Rozmiar czcionki */}
      <div className="btn-group" role="group" aria-label="Rozmiar tekstu">
        <button
          className={`btn btn-sm ${fontSize === "small" ? "btn-outline-dark active" : "btn-outline-dark"}`}
          onClick={() => setFontSize("small")}
        >
          A-
        </button>
        <button
          className={`btn btn-sm ${fontSize === "medium" ? "btn-outline-dark active" : "btn-outline-dark"}`}
          onClick={() => setFontSize("medium")}
        >
          A
        </button>
        <button
          className={`btn btn-sm ${fontSize === "large" ? "btn-outline-dark active" : "btn-outline-dark"}`}
          onClick={() => setFontSize("large")}
        >
          A+
        </button>
      </div>
    </div>
  );
}

export default ThemeControls;
