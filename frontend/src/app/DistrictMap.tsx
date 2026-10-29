"use client";

import { useMemo } from "react";
import L from "leaflet";
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";

import type { DistrictCollection, DistrictFeature } from "@/my_lib/districts";

type DistrictMapProps = {
  data: DistrictCollection;
  selectedId: string | null;
  scores: Record<string, number>;
  onSelect: (id: string) => void;
};

function districtStyle(
  feature: DistrictFeature,
  selectedId: string | null,
  scores: Record<string, number>,
): L.PathOptions {
  const { properties } = feature;
  const hasMetrics = properties.sample_count > 0 && [
    properties.traffic,
    properties.pop_density,
    properties.competitors,
    properties.avg_check,
    properties.peak_factor,
    properties.income_area,
    properties.rent_cost,
  ].every((value) => typeof value === "number" && Number.isFinite(value));
  const selected = hasMetrics && properties.id === selectedId;
  const score = scores[feature.properties.id];
  return {
    color: selected ? "var(--ink)" : "var(--surface)",
    weight: selected ? 2.5 : 1.5,
    opacity: 1,
    fillColor: hasMetrics ? "var(--accent)" : "var(--muted)",
    fillOpacity: !hasMetrics ? 0.06 : typeof score === "number" ? 0.12 + score * 0.055 : 0.16,
  };
}

export default function DistrictMap({ data, selectedId, scores, onSelect }: DistrictMapProps) {
  const bounds = useMemo(() => L.geoJSON(data).getBounds().pad(0.035), [data]);

  return (
    <MapContainer
      className="district-map"
      bounds={bounds}
      boundsOptions={{ padding: [18, 18] }}
      scrollWheelZoom
      zoomControl
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <GeoJSON
        key={`${selectedId ?? "none"}-${Object.values(scores).join("-")}`}
        data={data}
        style={(feature) => districtStyle(feature as DistrictFeature, selectedId, scores)}
        onEachFeature={(feature, layer) => {
          const district = feature as DistrictFeature;
          const hasMetrics = district.properties.sample_count > 0 && [
            district.properties.traffic,
            district.properties.pop_density,
            district.properties.competitors,
            district.properties.avg_check,
            district.properties.peak_factor,
            district.properties.income_area,
            district.properties.rent_cost,
          ].every((value) => typeof value === "number" && Number.isFinite(value));
          const score = scores[district.properties.id];
          layer.bindTooltip(
            !hasMetrics
              ? `${district.properties.name}: нет реальных данных`
              : typeof score === "number"
                ? `${district.properties.name}: ${score}/10`
                : district.properties.name,
            { sticky: true, className: "district-tooltip" },
          );
          if (hasMetrics) layer.on("click", () => onSelect(district.properties.id));
          if (hasMetrics && layer instanceof L.Path) {
            layer.on("mouseover", () => layer.setStyle({ weight: 3, fillOpacity: 0.45 }));
            layer.on("mouseout", () => layer.setStyle(districtStyle(district, selectedId, scores)));
          }
        }}
      />
    </MapContainer>
  );
}