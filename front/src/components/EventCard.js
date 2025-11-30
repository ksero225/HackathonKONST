import React from "react";
import { distanceInKm } from "../utils/distance";

function formatDistance(km) {
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(1)} km`;
}

function getPlaceFromDescription(description) {
  if (!description) return "Lokalizacja wydarzenia";
  const firstSentence = description.split(".")[0];
  return firstSentence.trim() || "Lokalizacja wydarzenia";
}

function EventCard({
  event,
  user,
  onJoin,
  onLeave,
  onHide,
  onSelect,
  isSelected,
}) {
  const eventId = event.eventId ?? event.id;
  const lat = event.latitude ?? event.lat;
  const lng = event.longitude ?? event.lng;

  const userLat =
    user?.lat ??
    user?.locationLat ??
    user?.userLocationLatitude ??
    null;

  const userLng =
    user?.lng ??
    user?.locationLng ??
    user?.userLocationLongitude ??
    null;

  const distance =
    userLat != null &&
    userLng != null &&
    lat != null &&
    lng != null
      ? distanceInKm(userLat, userLng, lat, lng)
      : null;

  const placeName =
    event.placeName || getPlaceFromDescription(event.description);

  const participantsCount =
    event.participantsCount ??
    (Array.isArray(event.userIds) ? event.userIds.length : 0);
  const capacity = event.capacity ?? null;

  const joinedViaStatus = event.status === "JOINED";
  const joinedViaUserIds =
    Array.isArray(event.userIds) && user?.userId != null
      ? event.userIds.includes(user.userId)
      : false;

  const isJoined = joinedViaStatus || joinedViaUserIds;
  const isPast = event.status === "PAST";

  const handleCardClick = () => {
    if (onSelect && eventId != null) {
      onSelect(eventId);
    }
  };

  let descriptionText = event.description || "";
  const usedDescriptionAsPlace = !event.placeName && !!event.description;
  if (usedDescriptionAsPlace && descriptionText) {
    const firstDot = descriptionText.indexOf(".");
    if (firstDot !== -1) {
      descriptionText = descriptionText.slice(firstDot + 1).trim();
    }
  }

  return (
    <div
      className={`card h-100 shadow-sm ${
        isSelected ? "border border-2 border-success" : ""
      }`}
      onClick={handleCardClick}
      style={{ cursor: onSelect ? "pointer" : "default" }}
    >
      <div className="card-body d-flex flex-column">
        <div className="d-flex justify-content-between align-items-start mb-2">
          <div>
            <h5 className="card-title mb-1">
              {event.name || "Wspólne wydarzenie"}
            </h5>
            <small className="text-muted d-block">
              📍 {placeName}
            </small>
          </div>

          {distance !== null && (
            <span
              className="badge"
              style={{
                backgroundColor: "var(--color1)",
                color: "white",
                padding: "6px 12px",
                borderRadius: "8px",
                marginTop: "4px",
                marginRight: "4px",
              }}
            >
              {formatDistance(distance)}
            </span>
          )}
        </div>

        {descriptionText && (
          <p className="small text-muted mb-2">{descriptionText}</p>
        )}

        <div className="d-flex justify-content-between align-items-center mb-2">
          <small>
            👥 {participantsCount}
            {capacity ? ` / ${capacity} osób` : " osób zapisanych"}
          </small>
          <small className="text-muted">
            {isPast
              ? "Wydarzenie zakończone"
              : isJoined
              ? "Jesteś zapisany"
              : "Propozycja od AI"}
          </small>
        </div>

        <div className="mb-3 rounded overflow-hidden"></div>

        <div className="mt-auto d-flex justify-content-between">
          {!isPast && (
            <>
              {!isJoined ? (
                <button
                  type="button"
                  className="btn btn-sm btn-success"
                  onClick={(e) => {
                    e.stopPropagation();
                    onJoin?.(eventId);
                  }}
                >
                  Weź udział
                </button>
              ) : (
                <button
                  type="button"
                  className="btn btn-sm btn-outline-danger"
                  onClick={(e) => {
                    e.stopPropagation();
                    onLeave?.(eventId);
                  }}
                >
                  Zrezygnuj
                </button>
              )}

              <button
                type="button"
                className="btn btn-sm btn-outline-secondary"
                onClick={(e) => {
                  e.stopPropagation();
                  onHide?.(eventId);
                }}
              >
                Ukryj
              </button>
            </>
          )}

          {isPast && (
            <button
              type="button"
              className="btn btn-sm btn-outline-secondary ms-auto"
              disabled
              onClick={(e) => e.stopPropagation()}
            >
              Zakończone
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default EventCard;
