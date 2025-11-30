import React from "react";
import { MapContainer, TileLayer, Marker, Circle } from "react-leaflet";
import L from "leaflet";

const eventIcon = new L.Icon({
  iconUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

function EventMapPreview({ lat, lng }) {
  if (lat == null || lng == null) {
    return (
      <div
        className="mb-3 rounded"
        style={{
          height: "90px",
          background: "#f0f0f0",
        }}
      >
        <div className="small text-muted p-2">
          Brak danych lokalizacji.
        </div>
      </div>
    );
  }

  const center = [lat, lng];

  return (
    <div className="mb-3 rounded overflow-hidden">
      <MapContainer
        center={center}
        zoom={14}
        style={{ height: "150px", width: "100%" }}
        scrollWheelZoom={false}
        dragging={false}
        doubleClickZoom={false}
        zoomControl={false}
        attributionControl={false}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={center} icon={eventIcon} />
        <Circle
          center={center}
          radius={200}
          pathOptions={{ color: "#3388ff", fillOpacity: 0.1 }}
        />
      </MapContainer>
    </div>
  );
}

export default EventMapPreview;
