import type { Feature, FeatureCollection, MultiPolygon, Polygon } from "geojson";

export type DistrictProperties = {
  id: string;
  name: string;
  osm_id: number;
  center: { lat: number; lon: number };
  traffic: number;
  pop_density: number;
  competitors: number;
  income_area: number;
  rent_cost: number;
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