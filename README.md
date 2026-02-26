# DJ Mixing Station (Offline v1)

A Streamlit music recommendation app using the Kaggle `spotify-and-youtube` dataset.

## Features
- Black / gold themed UI
- Start modes:
  - Song (search + quick picks)
  - Artist (search + quick picks)
  - Pick Vibe (single generated vibe seed)
  - Surprise Me (single random seed)
- Combined seed limit: up to 5 picks total (songs + artists)
- Final Pick Box for easy one-line removal
- Playlist generation by target total minutes (`±3` mins)
- Spotify / YouTube playback links and temporary YouTube playlist link
- Modern debug table view

## Run locally
```bash
pip install streamlit pandas numpy kagglehub
streamlit run recommendation_app/app.py --server.fileWatcherType none
```

## Dataset
Default KaggleHub dataset:
- `salvatorerastelli/spotify-and-youtube`

If needed, set Kaggle credentials before running.
