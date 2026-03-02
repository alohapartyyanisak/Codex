# Document Change: offline-v1 -> offline-v2

This file summarizes what changed from `offline-v1` to `offline-v2`.

## 1. Scope Shift
- `offline-v1`: single Kaggle source (`salvatorerastelli/spotify-and-youtube`).
- `offline-v2`: dual-source merge:
  - baseline: `salvatorerastelli/spotify-and-youtube`
  - expansion: `solomonameh/spotify-music-dataset`

## 2. Code Structure Changes
- New v2 entrypoint:
  - `recommendation_app/offline-v2/code/application_v2.py`
- New v2 data pipeline:
  - `recommendation_app/offline-v2/code/data_upgrade_v2.py`
- New v2 recommender core and adapter:
  - `recommendation_app/offline-v2/code/recommender_v2_core.py`
  - `recommendation_app/offline-v2/code/recommender_v2_adapter.py`
- Resolver and metrics tooling:
  - `recommendation_app/offline-v2/code/youtube_live_resolver.py`
  - `recommendation_app/offline-v2/code/resolver_quota_metrics.py`
  - `recommendation_app/offline-v2/code/resolver_examples_v2.py`

## 3. Data and Merge Logic Updates
- Added canonical merge behavior across two Kaggle datasets.
- Added owner/credits-aware record handling for collaborations.
- Added persistent merged-data cache (fingerprinted by source CSV metadata) to speed startup.
- Added explicit dedupe safeguards to avoid repeated songs in recommendations/playlists by:
  - same Spotify track identity
  - same YouTube video identity

## 4. YouTube Resolver Updates
- Added local resolver cache with TTL behavior.
- Added budget and quota guardrails for API usage.
- Added fallback HTML search-page resolver path.
- Added confidence labeling and diagnostics support.

## 5. UI and Debug View Updates
- Added `Direct YouTube` debug column.
- Added `YouTube Resolve Cache` debug column.
- Added `Cache Expires In` debug column.
- Added per-row YouTube confidence in modern debug table.

## 6. Performance Updates
- Startup optimization:
  - prefer local Kaggle cache path before download calls.
  - load merged dataset from local merge-cache when fingerprint unchanged.
- Removed expensive per-row live resolver calls from debug table rendering.
- Reduced resolver fan-out in quota metrics script for quicker/cheaper diagnostics.

## 7. Data Science Deliverables Added
- EDA notebook:
  - `recommendation_app/offline-v2/ds/combined_dataset_eda.ipynb`

## 8. Validation Completed (v2)
- Normal, edge, extreme, and strange test matrices executed.
- Duplicate-link playlist audit passed (`spotify_dup=0`, `youtube_dup=0` in tested runs).
- Duration-target optimization still meets constraints after dedupe.
