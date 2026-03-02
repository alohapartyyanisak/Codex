# DJ Mixing Station Studio (offline-v2)

## Short Story
DJ Mixing Station Studio is a local-first music recommendation app that blends Spotify and YouTube signals with mood controls.

The v2 build uses two Kaggle datasets and merges them:
- baseline: `salvatorerastelli/spotify-and-youtube`
- expansion: `solomonameh/spotify-music-dataset`

At runtime, the app can:
1. Download/use both Kaggle datasets through `kagglehub` and merge them.
2. Accept a user-uploaded CSV as fallback.

## Core v2 Files
- `recommendation_app/offline-v2/code/application_v2.py`: Streamlit UI entrypoint (v2)
- `recommendation_app/offline-v2/code/data_upgrade_v2.py`: dual-source Kaggle merge pipeline
- `recommendation_app/offline-v2/code/recommender_v2_core.py`: core scoring and playlist engine
- `recommendation_app/offline-v2/code/recommender_v2_adapter.py`: v2 prep/scoring adapter
- `recommendation_app/offline-v2/code/youtube_live_resolver.py`: YouTube resolver + cache/quota logic
- `recommendation_app/offline-v2/code/resolver_quota_metrics.py`: resolver monitoring metrics

## How To Run
From repo root:

```bash
pip install -r requirements.txt
```

If you prefer minimal install for app only:

```bash
pip install kagglehub streamlit pandas numpy
```

Set Kaggle credentials (required for automatic dataset download):

```bash
export KAGGLE_USERNAME=<your_kaggle_username>
export KAGGLE_KEY=<your_kaggle_key>
```

Optional YouTube resolver key:

```bash
export YOUTUBE_API_KEY=<your_youtube_api_key>
```

Run Streamlit (v2):

```bash
streamlit run recommendation_app/offline-v2/code/application_v2.py --server.port 8504 --server.fileWatcherType none
```

Open in browser:
- `http://localhost:8504`

If Kaggle credentials are not set, upload a compatible CSV directly in the app.

## Debug and Analysis Outputs
- EDA notebook:
  - `recommendation_app/offline-v2/ds/combined_dataset_eda.ipynb`
- Exported CSVs:
  - `recommendation_app/offline-v2/ds/combined_dataset_raw.csv`
  - `recommendation_app/offline-v2/ds/combined_dataset_prepared.csv`
- Change log from v1 to v2:
  - `recommendation_app/offline-v2/doc/document_change.md`
