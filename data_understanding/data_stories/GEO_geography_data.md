# Geography / location data — what we actually have (and don't)

**As-of 2026-08-30 · READ-ONLY · queried live.** Answer to "do we get location / coordinate / geography data?"

## Short answer
**Yes for postal/administrative geography; NO for lat/long coordinates.** There are no latitude/longitude,
geohash, or point/geo columns on the org or customer dimensions — so map-pin plotting would need an external
geocode of the addresses. But addresses, city, region/state, postal code, and country ARE present.

## What EXISTS

### 1. Organization / DC geography — `inventory_organization_scd1` (real, populated)
Columns: `address_line_1..4`, `town_or_city`, `region_1` (county), `region_2` (state/province), `region_3`,
`postal_code`, `country`. Real examples (queried):

| org | name | address | city | region_2 | postal | country |
|---|---|---|---|---|---|---|
| 2012 | Olive Branch | 12385 Crossroads Dr | Olive Branch | MS | 38654 | US |
| 1019 | Grenada (plant) | 2817 American Way | Grenada | MS | 38901 | US |
| 1080 | Byhalia | 85 Wingo Rd - N | Byhalia | MS | 38611 | US |
| 1006 | Cookeville | 1400 Salem Rd | Cookeville | TN | 38506 | US |
| 2093 | 3PL Canada Geodis | 537 Kingston Rd E | Ajax | (blank) | L1Z 1W3 | CA |
| 2120 | Mexico | Carretera Mexico-Qro | Estado De Mexico | Estado De Mexico | 54730 | MX |

→ Enough to map the network by city/state/country, compute distances (after geocoding), cluster by region,
and analyze US-South DC concentration (most DCs in MS/TN). `country` also drives US/CA/MX segmentation.

### 2. Customer geography — `dg5_customer_scd1` (via the hierarchy, not addresses)
No street address, but the hierarchy encodes geography: **mkedg1 = geography** (DOM domestic, CAN Canada,
LAG Latin America, EME, ANZ, INT…) and mkedg0 = 3rd-Party vs Intercompany. So customer geography is at the
region/channel level, not a mappable point.

### 3. Country-of-origin (sourcing geography) — `items_scd1.country_of_origin` (real)
Where items are MADE. Distribution (top): **US 108,491 + USA 36,168; CN 82,661 + CHN 6,397; VN 14,331;
TW 7,801; MX 5,775; DE 5,599 + DEU 5,081; TH 5,263; PK 3,065; HN 2,064**. This is the sourcing-risk /
import-lane geography (feeds LG logistics + B1 sourcing risk).
> ⚠️ **Data-quality note:** COO is NOT normalized — US vs USA, CN vs CHN, DE vs DEU are duplicated codes.
> Any COO geography analysis must canonicalize these first (a real cleaning rule).

### 4. Org role as pseudo-geography — `forecasted_organization` ('1' US Dist / '2' Service / '3' MEX Dist /
'4' MEX Floorcare) + the org-role topology in `O_location_persona.md`.

## What is MISSING
- **No lat/long / coordinates / geohash** anywhere on org or customer dims — no native point geometry.
- **No customer street addresses / ship-to coordinates** — customer geography stops at mkedg1 region.
- **COO codes not standardized** (US/USA, CN/CHN…) — needs a canonical country map.
- No explicit distance/lane/transit-time table (transit is inferred from movement timestamps in LG).

## So, can we do geography/mapping?
- **Regional / country / state-level analysis: YES, now** (group by country, region_2, mkedg1) — e.g.
  inventory by state, US-vs-CA-vs-MX split, sourcing by COO.
- **Point-on-map / distance / drive-time: needs a geocode step** (addresses → lat/long via an external
  geocoder), which would be a derived table in `sandbox_operations.po_management`, never a prod write.
- **Ties to scenarios:** DC network map (N/O), import-lane risk by COO (LG/B1), US/CA/MX plan split
  (P1 20 Global vs 20 Mexico), customer-region demand (P3 mkedg1).
