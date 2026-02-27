# DJ Mixing Station Studio (offline-v1)

## Short Story
DJ Mixing Station Studio is a local-first music recommendation app that blends Spotify and YouTube signals with mood controls.

The main data source is the Kaggle dataset:
- [salvatorerastelli/spotify-and-youtube](https://www.kaggle.com/datasets/salvatorerastelli/spotify-and-youtube)

At runtime, the app can:
1. Download and use the Kaggle dataset through `kagglehub`
2. Accept a user-uploaded CSV as fallback

This makes it easy to run the app offline-first after initial data setup, while still supporting custom datasets.

## Core App Files
- `recommendation_app/app.py`: Streamlit UI and interaction flow
- `recommendation_app/recommender.py`: data prep, scoring logic, ranking, and playlist duration optimizer

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

Run Streamlit:

```bash
streamlit run recommendation_app/app.py --server.fileWatcherType none
```

Open in browser (default):
- `http://localhost:8501`

If Kaggle credentials are not set, upload a compatible CSV directly in the app.

## More details here:
[Your Taste, Your Vibe: How DJ Mixing Station Studio Reimagines Recommendations](https://medium.com/@yanisakk26/your-taste-your-vibe-how-dj-mixing-station-studio-reimagines-recommendations-20a62dd59351)
