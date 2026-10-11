import { describe, expect, it } from 'vitest';
import { MAP_MAX_ZOOM, OSM_TILE_MAX_ZOOM } from '../lib/map-config';

describe('map source zoom limits', () => {
  it('keeps map navigation within the fallback raster source zoom range', () => {
    expect(OSM_TILE_MAX_ZOOM).toBe(19);
    expect(MAP_MAX_ZOOM).toBe(OSM_TILE_MAX_ZOOM);
  });
});
