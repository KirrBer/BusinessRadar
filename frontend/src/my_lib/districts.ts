import type { Feature, FeatureCollection, MultiPolygon, Polygon } from "geojson";

export type DistrictProperties = {
  id: string;
  name: string;
  osm_id: number;
  center: { lat: number; lon: number };
  sample_count: number;
  traffic: number | null;
  pop_density: number | null;
  competitors: number | null;
  avg_check: number | null;
  peak_factor: number | null;
  income_area: number | null;
  rent_cost: number | null;
};

export type DistrictFeature = Feature<Polygon | MultiPolygon, DistrictProperties>;

export type DistrictCollection = FeatureCollection<
  Polygon | MultiPolygon,
  DistrictProperties
> & {
  attribution: string;
  license: string;
  source: string;
};