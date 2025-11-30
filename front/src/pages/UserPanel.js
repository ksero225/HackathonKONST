import React, { useEffect, useState } from "react";
import EventCard from "../components/EventCard";
import EventGroupChat from "../components/EventGroupChat";

const API_BASE = "https://continuable-manuela-podgy.ngrok-free.dev/api";

function UserPanel({ user }) {
  const displayName =
    user?.userName || user?.login || "Użytkowniku";

  const initial = (user?.userName || user?.login || "?")
    .toString()
    .charAt(0)
    .toUpperCase();

  const description =
    user?.userDescription ||
    "Twój opis pojawi się tutaj po rozmowie z botem.";

  const [events, setEvents] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState(null);

  useEffect(() => {
    if (!user) return;

    const userId = user.userId || user.id;

    (async () => {
      try {
        const res = await fetch(
          `${API_BASE}/events/users/${userId}/events`,
          {
            credentials: "include",
          }
        );

        const text = await res.text();

        if (!res.ok) {
          console.error(
            "HTTP błąd przy pobieraniu eventów:",
            res.status,
            text
          );
          return;
        }

        let data;
        try {
          data = JSON.parse(text);
        } catch (e) {
          console.error(
            "Serwer NIE zwrócił JSON, tylko HTML / coś innego:"
          );
          console.log(text);
          return;
        }

        setEvents(data);
      } catch (err) {
        console.error("Błąd pobierania wydarzeń:", err);
      }
    })();
  }, [user]);

  useEffect(() => {
    if (events.length > 0 && !selectedEventId) {
      const first = events[0];
      setSelectedEventId(first.eventId ?? first.id);
    }
  }, [events, selectedEventId]);

  const handleJoin = async (eventId) => {
    if (!user) return;
    const userId = user.userId || user.id;

    try {
      const url = `${API_BASE}/events/users/${userId}/events/${eventId}`;

      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const text = await res.text();

      if (!res.ok) {
        console.error(
          "Błąd zapisywania na wydarzenie:",
          res.status,
          text
        );
        alert("Nie udało się zapisać na wydarzenie.");
        return;
      }

      const userIdNum = Number(userId);

      setEvents((prev) =>
        prev.map((ev) => {
          const evId = ev.eventId ?? ev.id;
          if (evId !== eventId) return ev;

          const oldUserIds = Array.isArray(ev.userIds) ? ev.userIds : [];
          const alreadyIn = oldUserIds.includes(userIdNum);

          const newUserIds = alreadyIn
            ? oldUserIds
            : [...oldUserIds, userIdNum];

          const oldCount =
            ev.participantsCount ?? oldUserIds.length;

          return {
            ...ev,
            userIds: newUserIds,
            participantsCount: alreadyIn ? oldCount : oldCount + 1,
            status: "JOINED",
          };
        })
      );
    } catch (err) {
      console.error("Błąd połączenia przy zapisie:", err);
      alert("Wystąpił problem z połączeniem. Spróbuj ponownie.");
    }
  };

  const handleLeave = async (eventId) => {
    if (!user) return;

    const userId = user.userId || user.id;

    try {
      const url = `${API_BASE}/events/users/${userId}/events/${eventId}`;

      const res = await fetch(url, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const text = await res.text();

      if (!res.ok) {
        console.error(
          "Błąd wypisywania z wydarzenia:",
          res.status,
          text
        );
        alert("Nie udało się zrezygnować z wydarzenia.");
        return;
      }

      const userIdNum = Number(userId);

      setEvents((prev) =>
        prev.map((ev) => {
          const evId = ev.eventId ?? ev.id;
          if (evId !== eventId) return ev;

          const oldUserIds = Array.isArray(ev.userIds) ? ev.userIds : [];
          const newUserIds = oldUserIds.filter(
            (id) => id !== userIdNum
          );

          const oldCount =
            ev.participantsCount ?? oldUserIds.length;

          return {
            ...ev,
            userIds: newUserIds,
            participantsCount: Math.max(0, oldCount - 1),
            status: "SUGGESTED",
          };
        })
      );
    } catch (err) {
      console.error("Błąd połączenia przy rezygnacji:", err);
      alert("Wystąpił problem z połączeniem. Spróbuj ponownie.");
    }
  };

  const handleHide = (eventId) => {
    setEvents((prev) =>
      prev.filter(
        (e) => (e.eventId ?? e.id) !== eventId
      )
    );
    if (selectedEventId === eventId) {
      setSelectedEventId(null);
    }
  };

  return (
    <div>
      <h2 className="mb-4">Panel użytkownika</h2>

      <div className="row">
        <div className="col-md-4 col-lg-3 mb-4">
          <div className="d-flex flex-column align-items-center">
            <div
              className="rounded-circle d-flex align-items-center justify-content-center mb-3"
              style={{
                width: "140px",
                height: "140px",
                fontSize: "3.5rem",
                backgroundColor: "var(--color1)",
                color: "#fff",
              }}
            >
              {initial}
            </div>

            <h5 className="mb-2 text-center">{displayName}</h5>

            <p className="text-muted small text-justify">
              {description}
            </p>
          </div>
        </div>

        <div className="col-md-8 col-lg-9">
          <p className="lead">Cześć, {displayName}!</p>
          <p>
            Poniżej znajdziesz wydarzenia, które AI proponuje lub do
            których jesteś zapisany.
          </p>

          <hr />

          <h4 className="mb-3">Twoje wydarzenia</h4>

          {events.length === 0 ? (
            <p className="text-muted">
              Nie masz jeszcze żadnych wydarzeń. 🙂
            </p>
          ) : (
            <div className="row g-3 align-items-start">
              <div className="col-lg-6">
                {events.map((ev, index) => {
                  const evId = ev.eventId ?? ev.id ?? index;
                  return (
                    <div className="mb-3" key={evId}>
                      <EventCard
                        event={ev}
                        user={user}
                        onJoin={handleJoin}
                        onLeave={handleLeave}
                        onHide={handleHide}
                        onSelect={setSelectedEventId}
                        isSelected={evId === selectedEventId}
                      />
                    </div>
                  );
                })}
              </div>

              <div className="col-lg-6">
                {selectedEventId ? (
                  <EventGroupChat
                    user={user}
                    eventId={selectedEventId}
                  />
                ) : (
                  <p className="text-muted">
                    Wybierz wydarzenie z listy, aby otworzyć czat
                    grupowy.
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default UserPanel;
