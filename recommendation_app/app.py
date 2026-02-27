from __future__ import annotations

import re
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

try:
    from recommendation_app.recommender import (
        MOOD_ADJUSTMENTS,
        build_duration_playlist,
        format_compact_number,
        prepare_music_data,
        recommend_tracks,
    )
except ModuleNotFoundError:
    from recommender import (
        MOOD_ADJUSTMENTS,
        build_duration_playlist,
        format_compact_number,
        prepare_music_data,
        recommend_tracks,
    )


DEFAULT_DATASET_ID = "salvatorerastelli/spotify-and-youtube"
PLAYLIST_TOLERANCE_MINUTES = 3
MAX_SEED_SELECTIONS = 5
PERSONALITY_PROFILES = {
    "Party Starter": {
        "description": "High-energy, dance-forward tracks for an outgoing vibe.",
        "targets": {
            "danceability": 0.82,
            "energy": 0.86,
            "valence": 0.72,
            "acousticness": 0.20,
            "tempo_scaled": 0.78,
            "popularity_norm": 0.75,
        },
    },
    "Late Night Chill": {
        "description": "Smooth, lower-intensity tracks for relaxed listening.",
        "targets": {
            "danceability": 0.55,
            "energy": 0.35,
            "valence": 0.45,
            "acousticness": 0.70,
            "tempo_scaled": 0.35,
            "popularity_norm": 0.50,
        },
    },
    "Focus Flow": {
        "description": "Steady, less-vocal-friendly atmosphere for concentration.",
        "targets": {
            "danceability": 0.50,
            "energy": 0.48,
            "valence": 0.50,
            "acousticness": 0.42,
            "instrumentalness": 0.45,
            "tempo_scaled": 0.50,
            "popularity_norm": 0.45,
        },
    },
    "Uplift Me": {
        "description": "Positive mood, melodic energy, and feel-good momentum.",
        "targets": {
            "danceability": 0.68,
            "energy": 0.70,
            "valence": 0.86,
            "acousticness": 0.32,
            "tempo_scaled": 0.62,
            "popularity_norm": 0.62,
        },
    },
    "Underground Explorer": {
        "description": "Lower-popularity picks with strong character and momentum.",
        "targets": {
            "danceability": 0.58,
            "energy": 0.58,
            "valence": 0.45,
            "acousticness": 0.46,
            "tempo_scaled": 0.52,
            "popularity_norm": 0.20,
        },
    },
}
QUICK_VIBE_DEFAULTS = {
    "Party Starter": {"mood": "High Energy", "spotify_weight_pct": 55, "discovery_hits_pct": 85},
    "Late Night Chill": {"mood": "Chill", "spotify_weight_pct": 60, "discovery_hits_pct": 45},
    "Focus Flow": {"mood": "Balanced", "spotify_weight_pct": 50, "discovery_hits_pct": 55},
    "Uplift Me": {"mood": "Uplifting", "spotify_weight_pct": 55, "discovery_hits_pct": 70},
    "Underground Explorer": {"mood": "Dark", "spotify_weight_pct": 50, "discovery_hits_pct": 20},
}


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
          --bg: #070707;
          --panel: #111111;
          --panel-2: #171717;
          --gold: #d4af37;
          --gold-soft: #f1d98a;
          --text: #f5f5f5;
          --muted: #b8b8b8;
          --border: rgba(212, 175, 55, 0.35);
        }
        .stApp {
          background:
            radial-gradient(1300px 600px at 100% -20%, rgba(212,175,55,0.20), transparent 70%),
            radial-gradient(1000px 500px at -20% 120%, rgba(212,175,55,0.10), transparent 65%),
            var(--bg);
          color: var(--text);
        }
        h1, h2, h3, h4, p, span, div, label {
          color: var(--text) !important;
        }
        .hero {
          border: 1px solid var(--border);
          border-radius: 18px;
          padding: 22px;
          background: linear-gradient(160deg, rgba(212,175,55,0.15), rgba(0,0,0,0.55));
          box-shadow: 0 14px 30px rgba(0,0,0,0.45);
          margin-bottom: 18px;
        }
        .hero h1 {
          margin: 0;
          font-size: 2rem;
          letter-spacing: 0.3px;
        }
        .hero p {
          margin: 8px 0 0 0;
          color: var(--muted) !important;
        }
        .metric-card {
          border: 1px solid var(--border);
          border-radius: 14px;
          background: linear-gradient(150deg, rgba(212,175,55,0.12), rgba(17,17,17,0.95));
          padding: 10px 12px;
          margin-bottom: 12px;
        }
        .metric-label {
          font-size: 0.8rem;
          color: var(--muted) !important;
          margin-bottom: 3px;
        }
        .metric-value {
          color: var(--gold-soft) !important;
          font-size: 1.1rem;
          font-weight: 700;
        }
        .track-card {
          border: 1px solid rgba(212,175,55,0.30);
          border-radius: 16px;
          padding: 12px 14px;
          background: linear-gradient(160deg, rgba(212,175,55,0.08), rgba(23,23,23,0.98));
          min-height: 210px;
          box-shadow: 0 10px 25px rgba(0,0,0,0.35);
          margin-bottom: 14px;
        }
        .track-rank {
          font-size: 0.72rem;
          color: var(--gold-soft) !important;
          text-transform: uppercase;
          letter-spacing: 1.1px;
        }
        .track-title {
          font-size: 1.05rem;
          font-weight: 700;
          line-height: 1.25;
          margin-top: 5px;
          margin-bottom: 2px;
        }
        .track-artist {
          color: var(--muted) !important;
          margin-bottom: 10px;
        }
        .score-row {
          font-size: 0.86rem;
          color: var(--muted) !important;
          margin-top: 2px;
        }
        .pill {
          display: inline-block;
          border: 1px solid var(--border);
          border-radius: 999px;
          padding: 2px 8px;
          font-size: 0.72rem;
          color: var(--gold-soft) !important;
          margin-right: 5px;
          margin-top: 8px;
        }
        .action-title {
          font-size: 1.45rem;
          font-weight: 800;
          color: var(--gold-soft) !important;
          letter-spacing: 0.2px;
          margin-top: 6px;
          margin-bottom: 8px;
        }
        [data-testid="stSidebar"] {
          background: linear-gradient(180deg, #0c0c0c, #131313);
          border-right: 1px solid var(--border);
        }
        .stButton button, .stDownloadButton button {
          background: linear-gradient(180deg, #d4af37, #9b7a1d) !important;
          border: none !important;
          color: #101010 !important;
          border-radius: 10px !important;
          font-weight: 700 !important;
        }
        .stSelectbox div[data-baseweb="select"] > div,
        .stTextInput div[data-baseweb="input"] > div {
          background-color: var(--panel-2);
          border: 1px solid var(--border);
        }
        div[data-baseweb="popover"] ul,
        div[data-baseweb="select"] ul {
          background: var(--panel-2) !important;
          border: 1px solid rgba(212, 175, 55, 0.55) !important;
        }
        div[data-baseweb="popover"] li,
        div[data-baseweb="select"] li,
        div[data-baseweb="popover"] li span,
        div[data-baseweb="select"] li span {
          background: var(--panel-2) !important;
          color: var(--text) !important;
        }
        div[data-baseweb="popover"] li:hover,
        div[data-baseweb="select"] li:hover {
          background: #1f1f1f !important;
          color: var(--gold-soft) !important;
        }
        div[data-baseweb="popover"] li[aria-selected="true"],
        div[data-baseweb="select"] li[aria-selected="true"] {
          background: #232323 !important;
          color: var(--gold-soft) !important;
        }
        .platform-link {
          display: block;
          width: 100%;
          text-align: center;
          background: var(--panel-2);
          border: 1px solid var(--border);
          color: var(--text) !important;
          border-radius: 10px;
          text-decoration: none !important;
          padding: 8px 10px;
          font-weight: 600;
          margin-bottom: 6px;
        }
        .platform-link:hover {
          background: #1c1c1c;
          border: 1px solid rgba(212, 175, 55, 0.65);
          color: var(--gold-soft) !important;
        }
        [data-testid="stFileUploaderDropzone"] {
          background-color: var(--panel-2) !important;
          border: 1px dashed rgba(212, 175, 55, 0.55) !important;
          border-radius: 14px !important;
        }
        [data-testid="stFileUploaderDropzone"] > div {
          background-color: var(--panel-2) !important;
        }
        [data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stFileUploaderDropzone"] small,
        [data-testid="stFileUploaderDropzone"] span {
          color: var(--text) !important;
        }
        [data-testid="stFileUploaderDropzone"] button,
        [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] {
          background: linear-gradient(180deg, #d4af37, #9b7a1d) !important;
          border: none !important;
          color: #101010 !important;
          border-radius: 10px !important;
          font-weight: 700 !important;
        }
        [data-testid="stFileUploaderDropzone"] button:hover,
        [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"]:hover {
          filter: brightness(1.03);
        }
        [data-testid="stDataFrame"] {
          border: 1px solid var(--border);
          border-radius: 14px;
          overflow: hidden;
          background: #000000;
          box-shadow: 0 8px 22px rgba(0,0,0,0.35);
          --gdg-bg-cell: #000000;
          --gdg-bg-cell-medium: #000000;
          --gdg-bg-header: #000000;
          --gdg-bg-header-has-focus: #000000;
          --gdg-text-dark: #f5f5f5;
          --gdg-text-medium: #e9e9e9;
          --gdg-text-light: #bfbfbf;
          --gdg-accent-color: #ffffff;
          --gdg-horizontal-border-color: rgba(212, 175, 55, 0.18);
          --gdg-vertical-border-color: rgba(212, 175, 55, 0.10);
        }
        [data-testid="stDataFrame"] canvas {
          background: #000000 !important;
        }
        [data-testid="stDataFrame"] [role="columnheader"] {
          background: #000000 !important;
          color: #f5f5f5 !important;
          font-weight: 700 !important;
          border-bottom: 1px solid rgba(212, 175, 55, 0.45) !important;
        }
        [data-testid="stDataFrame"] [role="gridcell"] {
          background: #000000 !important;
          color: #f5f5f5 !important;
          border-bottom: 1px solid rgba(212, 175, 55, 0.14) !important;
          border-right: 1px solid rgba(212, 175, 55, 0.08) !important;
        }
        [data-testid="stDataFrame"] [role="row"]:nth-child(even) [role="gridcell"] {
          background: #000000 !important;
        }
        [data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"] {
          background: #0a0a0a !important;
        }
        [data-testid="stDataFrame"] [role="row"]:first-child [role="gridcell"] {
          border-top: 1px solid rgba(255, 77, 77, 0.55) !important;
        }
        [data-testid="stDataFrame"] div[role="progressbar"] > div {
          background: #ffffff !important;
        }
        .modern-debug-wrap {
          border: 1px solid rgba(212, 175, 55, 0.35);
          border-radius: 16px;
          overflow-x: auto;
          background: linear-gradient(160deg, rgba(212,175,55,0.08), rgba(8,8,8,0.98));
          box-shadow: 0 12px 28px rgba(0, 0, 0, 0.35);
        }
        .modern-debug-table {
          width: 100%;
          min-width: 1120px;
          border-collapse: collapse;
          color: #f5f5f5;
          font-size: 0.96rem;
        }
        .modern-debug-table thead th {
          text-align: left;
          position: sticky;
          top: 0;
          background: linear-gradient(180deg, rgba(212,175,55,0.30), rgba(30,24,10,0.95));
          color: #f5f5f5;
          border-bottom: 1px solid rgba(212, 175, 55, 0.45);
          padding: 12px 14px;
          letter-spacing: 0.2px;
          font-weight: 700;
          white-space: nowrap;
        }
        .modern-debug-table tbody td {
          padding: 12px 14px;
          border-bottom: 1px solid rgba(212, 175, 55, 0.12);
          vertical-align: middle;
        }
        .modern-debug-table tbody tr:nth-child(even) {
          background: rgba(255, 255, 255, 0.02);
        }
        .modern-debug-table tbody tr:hover {
          background: rgba(255, 77, 77, 0.10);
        }
        .debug-rank {
          color: #f1d98a;
          font-weight: 700;
          text-align: right;
          width: 56px;
        }
        .debug-track {
          color: #ffffff;
          font-weight: 600;
          max-width: 440px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .debug-subtle {
          color: #d9d9d9;
          white-space: nowrap;
        }
        .debug-score-cell {
          min-width: 190px;
        }
        .debug-score-wrap {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .debug-score-track {
          flex: 1;
          height: 8px;
          background: rgba(255, 255, 255, 0.16);
          border-radius: 999px;
          overflow: hidden;
          border: 1px solid rgba(255, 255, 255, 0.18);
        }
        .debug-score-fill {
          height: 100%;
          background: linear-gradient(90deg, #ff4d4d, #d4af37);
        }
        .debug-score-value {
          font-variant-numeric: tabular-nums;
          color: #ffffff;
          min-width: 42px;
          text-align: right;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def resolve_dataset_csv(dataset_path: Path) -> Path:
    csv_files = sorted(dataset_path.rglob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found under: {dataset_path}")
    if len(csv_files) == 1:
        return csv_files[0]

    for candidate in csv_files:
        name = candidate.name.lower()
        if "spotify" in name and "youtube" in name:
            return candidate
    return max(csv_files, key=lambda file_path: file_path.stat().st_size)


@st.cache_data(show_spinner=False)
def load_from_kagglehub(dataset_id: str) -> tuple[pd.DataFrame, str, str]:
    try:
        import kagglehub
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError("kagglehub is not installed. Run: pip install kagglehub") from exc

    dataset_path = Path(kagglehub.dataset_download(dataset_id))
    csv_path = resolve_dataset_csv(dataset_path)
    return pd.read_csv(csv_path), str(csv_path), str(dataset_path)


@st.cache_data(show_spinner=False)
def prepare_music_data_cached(raw_df: pd.DataFrame) -> pd.DataFrame:
    return prepare_music_data(raw_df)


@st.cache_data(show_spinner=False)
def recommend_tracks_cached(
    data: pd.DataFrame,
    seed_weight_items: tuple[tuple[str, float], ...],
    mood: str,
    spotify_weight: float,
    discovery_mode: float,
    top_k: int,
    exclude_seed_tracks: bool,
    preferred_artist_weight_items: tuple[tuple[str, float], ...],
) -> pd.DataFrame:
    seed_weights = {str(name): float(weight) for name, weight in seed_weight_items}
    preferred_artist_weights = {str(name): float(weight) for name, weight in preferred_artist_weight_items}
    return recommend_tracks(
        data=data,
        seed_display_name=seed_weights,
        mood=mood,
        spotify_weight=spotify_weight,
        discovery_mode=discovery_mode,
        top_k=top_k,
        exclude_seed_tracks=exclude_seed_tracks,
        preferred_artist_weights=preferred_artist_weights,
    )


@st.cache_data(show_spinner=False)
def build_duration_playlist_cached(
    recommendations: pd.DataFrame,
    target_minutes: int,
    tolerance_minutes: int,
    candidate_limit: int,
    max_tracks: int,
) -> pd.DataFrame:
    return build_duration_playlist(
        recommendations=recommendations,
        target_minutes=target_minutes,
        tolerance_minutes=tolerance_minutes,
        candidate_limit=candidate_limit,
        max_tracks=max_tracks,
    )


@st.cache_data(show_spinner=False)
def get_seed_ui_options(data: pd.DataFrame) -> tuple[list[str], list[str], list[str], list[str]]:
    song_options = sorted(data["display_name"].astype(str).unique().tolist())
    artist_options = sorted(data["artist"].astype(str).unique().tolist())
    quick_top_songs = top_song_seed_options(data, top_n=8)
    quick_top_artists = top_artist_seed_options(data, top_n=8)["artist"].astype(str).tolist()
    return song_options, artist_options, quick_top_songs, quick_top_artists


def read_source(uploaded_file: Any, dataset_id: str) -> tuple[pd.DataFrame, str, str]:
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file), uploaded_file.name, "uploaded_file"
    return load_from_kagglehub(dataset_id)


def render_metric_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{escape(str(label))}</div>
          <div class="metric-value">{escape(str(value))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_track_duration(duration_ms: object) -> str:
    try:
        seconds = int(round(float(duration_ms) / 1000))
    except (TypeError, ValueError):
        return "0m 00s"
    minutes, sec = divmod(max(0, seconds), 60)
    return f"{minutes}m {sec:02d}s"


def format_total_duration(total_minutes: float) -> str:
    rounded_total = int(round(float(total_minutes)))
    hours, mins = divmod(max(0, rounded_total), 60)
    return f"{hours}hr {mins}mins (total {rounded_total} mins)"


def format_hours_minutes(total_minutes: float) -> str:
    rounded_total = int(round(float(total_minutes)))
    hours, mins = divmod(max(0, rounded_total), 60)
    return f"{hours}hr {mins}mins"


def extract_spotify_track_id(url: object) -> str | None:
    match = re.search(r"open\.spotify\.com/track/([A-Za-z0-9]+)", str(url or ""))
    return match.group(1) if match else None


def extract_youtube_video_id(url: object) -> str | None:
    text = str(url or "").strip()
    if not text:
        return None

    parsed = urlparse(text)
    host = parsed.netloc.lower()
    path_parts = [part for part in parsed.path.split("/") if part]

    if "youtu.be" in host and path_parts:
        return path_parts[0]
    if "youtube.com" in host and parsed.path == "/watch":
        return parse_qs(parsed.query).get("v", [None])[0]
    if "youtube.com" in host and path_parts and path_parts[0] in {"shorts", "embed"}:
        return path_parts[1] if len(path_parts) > 1 else None

    fallback = re.search(r"[?&]v=([A-Za-z0-9_-]{6,})", text)
    return fallback.group(1) if fallback else None


def normalize_youtube_watch_url(url: object) -> str | None:
    video_id = extract_youtube_video_id(url)
    return f"https://www.youtube.com/watch?v={video_id}" if video_id else None


def render_platform_link(label: str, url: str) -> None:
    st.markdown(
        f'<a class="platform-link" href="{url}" target="_blank" rel="noopener noreferrer">{label}</a>',
        unsafe_allow_html=True,
    )


def render_track_links(spotify_url: object, youtube_url: object) -> None:
    cols = st.columns(2)
    spotify_text = str(spotify_url or "").strip()
    youtube_text = str(youtube_url or "").strip()

    with cols[0]:
        if spotify_text:
            render_platform_link("Spotify", spotify_text)
    with cols[1]:
        if youtube_text:
            render_platform_link("YouTube", youtube_text)


def render_modern_debug_table(playlist: pd.DataFrame) -> None:
    if playlist.empty:
        st.caption("No debug rows to display.")
        return

    safe_playlist = playlist.copy()
    for numeric_col in ("recommendation_score", "similarity_score", "platform_score", "discovery_score", "momentum_score"):
        safe_playlist[numeric_col] = pd.to_numeric(safe_playlist[numeric_col], errors="coerce").fillna(0.0)

    def score_cell(value: float) -> str:
        clipped = float(np.clip(value, 0.0, 1.0))
        pct = clipped * 100
        return (
            '<td class="debug-score-cell"><div class="debug-score-wrap">'
            f'<div class="debug-score-track"><div class="debug-score-fill" style="width:{pct:.1f}%"></div></div>'
            f'<span class="debug-score-value">{clipped:.3f}</span>'
            "</div></td>"
        )

    rows_html: list[str] = []
    for idx, row in safe_playlist.reset_index(drop=True).iterrows():
        rows_html.append(
            "<tr>"
            f'<td class="debug-rank">{idx + 1}</td>'
            f'<td class="debug-subtle">{escape(str(row.get("artist", "")))}</td>'
            f'<td class="debug-track">{escape(str(row.get("track", "")))}</td>'
            f'<td class="debug-subtle">{escape(format_track_duration(row.get("duration_ms", 0)))}</td>'
            f"{score_cell(float(row.get('recommendation_score', 0.0)))}"
            f"{score_cell(float(row.get('momentum_score', 0.0)))}"
            f'<td class="debug-subtle">{escape(format_compact_number(float(row.get("views", 0) or 0)))}</td>'
            f'<td class="debug-subtle">{escape(format_compact_number(float(row.get("stream", 0) or 0)))}</td>'
            "</tr>"
        )

    st.markdown(
        (
            '<div class="modern-debug-wrap"><table class="modern-debug-table">'
            "<thead><tr>"
            "<th>Rank</th><th>Artist</th><th>Track</th><th>Duration</th><th>Match</th><th>Momentum</th><th>Views</th><th>Streams</th>"
            "</tr></thead>"
            f"<tbody>{''.join(rows_html)}</tbody></table></div>"
        ),
        unsafe_allow_html=True,
    )


def top_artist_seed_options(data: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    artist_rank = data.groupby("artist", as_index=False).agg(
        artist_streams=("stream", "sum"),
        artist_views=("views", "sum"),
        artist_momentum=("momentum_score", "mean"),
    )
    artist_rank["artist_score"] = (
        np.log1p(artist_rank["artist_streams"]) + np.log1p(artist_rank["artist_views"]) + 2.0 * artist_rank["artist_momentum"]
    )

    best_track_per_artist = data.sort_values(["momentum_score", "views", "stream"], ascending=False).drop_duplicates(
        subset=["artist"], keep="first"
    )
    options = artist_rank.merge(best_track_per_artist[["artist", "display_name"]], on="artist", how="left")
    options = options.sort_values(["artist_score", "artist"], ascending=[False, True]).head(top_n)
    return options.reset_index(drop=True)


def top_song_seed_options(data: pd.DataFrame, top_n: int = 5) -> list[str]:
    top_songs = data.sort_values(["momentum_score", "views", "stream"], ascending=False).head(top_n)
    return top_songs["display_name"].tolist()


def render_toggle_chips(
    labels: list[str],
    selected_values: list[str],
    key_prefix: str,
    min_chips: int = 5,
    chips_per_row: int = 3,
) -> str | None:
    if not labels:
        return None

    chip_count = max(min_chips, min(len(labels), 8))
    options = labels[:chip_count]
    clicked = None

    for row_start in range(0, len(options), chips_per_row):
        row_labels = options[row_start : row_start + chips_per_row]
        columns = st.columns(len(row_labels))
        for offset, label in enumerate(row_labels):
            idx = row_start + offset
            chip_label = f"✓ {label}" if label in selected_values else label
            if columns[offset].button(chip_label, key=f"{key_prefix}_{idx}_{label}", use_container_width=True):
                clicked = label
    return clicked


def best_track_for_artist(data: pd.DataFrame, artist_name: str) -> str | None:
    artist_rows = data.loc[data["artist"] == artist_name].copy()

    artist_key = re.sub(r"[^a-z0-9 ]+", " ", str(artist_name).lower()).strip()
    featured_rows = data.head(0).copy()
    if artist_key and "featured_artist_norms" in data.columns:
        featured_mask = data["featured_artist_norms"].fillna("").astype(str).str.contains(
            rf"(^|\|){re.escape(artist_key)}(\||$)",
            regex=True,
        )
        featured_rows = data.loc[featured_mask].copy()

    candidate_rows = pd.concat([artist_rows, featured_rows], ignore_index=False)
    candidate_rows = candidate_rows.drop_duplicates(subset=["display_name"], keep="first")
    if candidate_rows.empty:
        return None

    best = candidate_rows.sort_values(["momentum_score", "views", "stream"], ascending=False).iloc[0]
    return str(best["display_name"])


def personality_seed_option(data: pd.DataFrame, profile_name: str) -> tuple[str, str]:
    profile = PERSONALITY_PROFILES[profile_name]
    targets = profile["targets"]
    score = pd.Series(np.zeros(len(data), dtype=float), index=data.index)

    for feature, target_value in targets.items():
        if feature not in data.columns:
            continue
        score += np.abs(pd.to_numeric(data[feature], errors="coerce").fillna(0.0) - float(target_value))

    best = (
        data.assign(personality_distance=score)
        .sort_values(["personality_distance", "momentum_score", "views", "stream"], ascending=[True, False, False, False])
        .iloc[0]
    )
    return str(best["display_name"]), str(profile["description"])


def _default_seed_track(data: pd.DataFrame) -> str:
    return str(data.sort_values(["momentum_score", "views", "stream"], ascending=False).iloc[0]["display_name"])


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output


def _init_seed_selection_state(data: pd.DataFrame) -> None:
    if "selected_seed_artists" not in st.session_state:
        st.session_state["selected_seed_artists"] = []
    if "selected_seed_songs" not in st.session_state:
        st.session_state["selected_seed_songs"] = []

    valid_artists = set(data["artist"].astype(str))
    valid_songs = set(data["display_name"].astype(str))

    st.session_state["selected_seed_artists"] = [
        artist
        for artist in _dedupe_preserve_order([str(item) for item in st.session_state["selected_seed_artists"]])
        if artist in valid_artists
    ]
    st.session_state["selected_seed_songs"] = [
        song
        for song in _dedupe_preserve_order([str(item) for item in st.session_state["selected_seed_songs"]])
        if song in valid_songs
    ]


def _current_combined_seed_count() -> int:
    return len(st.session_state.get("selected_seed_artists", [])) + len(st.session_state.get("selected_seed_songs", []))


def _toggle_seed_selection(list_key: str, value: str, max_total: int = MAX_SEED_SELECTIONS) -> None:
    selected = list(st.session_state.get(list_key, []))
    if value in selected:
        selected = [item for item in selected if item != value]
        st.session_state[list_key] = selected
        return

    if _current_combined_seed_count() >= max_total:
        st.warning(f"You can select at most {max_total} picks total across songs and artists.")
        return

    selected.append(value)
    st.session_state[list_key] = _dedupe_preserve_order(selected)


def _add_seed_selection(list_key: str, value: str, max_total: int = MAX_SEED_SELECTIONS) -> None:
    selected = list(st.session_state.get(list_key, []))
    if value in selected:
        return
    if _current_combined_seed_count() >= max_total:
        st.warning(f"You can select at most {max_total} picks total across songs and artists.")
        return
    selected.append(value)
    st.session_state[list_key] = _dedupe_preserve_order(selected)


def _render_final_pick_box() -> None:
    selected_artists = list(st.session_state.get("selected_seed_artists", []))
    selected_songs = list(st.session_state.get("selected_seed_songs", []))
    all_labels = [f"Artist: {name}" for name in selected_artists] + [f"Song: {name}" for name in selected_songs]

    retained_labels = st.multiselect(
        "Final Pick Box",
        options=all_labels,
        default=all_labels,
        placeholder="Selected songs/artists appear here (remove with x).",
    )
    retained_set = set(retained_labels)
    st.session_state["selected_seed_artists"] = [
        name for name in selected_artists if f"Artist: {name}" in retained_set
    ]
    st.session_state["selected_seed_songs"] = [
        name for name in selected_songs if f"Song: {name}" in retained_set
    ]

    final_count = _current_combined_seed_count()
    st.caption(f"Final Picks ({final_count}/{MAX_SEED_SELECTIONS})")


def _build_seed_weights_from_state(data: pd.DataFrame) -> dict[str, float]:
    selected_artists = list(st.session_state.get("selected_seed_artists", []))
    selected_songs = list(st.session_state.get("selected_seed_songs", []))
    total_selected = len(selected_artists) + len(selected_songs)

    if total_selected == 0:
        fallback_seed = _default_seed_track(data)
        st.info(f"No picks selected. Using default starter: {fallback_seed}")
        return {fallback_seed: 1.0}

    artist_share = len(selected_artists) / total_selected
    song_share = len(selected_songs) / total_selected
    st.caption(f"Blend mix: Artists ({artist_share:.0%}) + Songs ({song_share:.0%})")

    unit_weight = 1.0 / total_selected
    seed_weights: dict[str, float] = {}
    for artist_name in selected_artists:
        artist_seed = best_track_for_artist(data, artist_name)
        if artist_seed:
            seed_weights[artist_seed] = seed_weights.get(artist_seed, 0.0) + unit_weight
    for song_name in selected_songs:
        seed_weights[song_name] = seed_weights.get(song_name, 0.0) + unit_weight

    total_weight = float(sum(seed_weights.values()))
    if total_weight <= 0:
        return {_default_seed_track(data): 1.0}
    return {name: weight / total_weight for name, weight in seed_weights.items()}


def _build_preferred_artist_weights(data: pd.DataFrame) -> dict[str, float]:
    artist_counts: dict[str, float] = {}

    for artist_name in st.session_state.get("selected_seed_artists", []):
        key = str(artist_name).strip()
        if key:
            artist_counts[key] = artist_counts.get(key, 0.0) + 1.0

    selected_songs = [str(song).strip() for song in st.session_state.get("selected_seed_songs", []) if str(song).strip()]
    if selected_songs:
        song_artist_lookup = (
            data.loc[data["display_name"].isin(selected_songs), ["display_name", "artist"]]
            .drop_duplicates(subset=["display_name"], keep="first")
            .set_index("display_name")["artist"]
            .to_dict()
        )
        for song_name in selected_songs:
            artist_name = str(song_artist_lookup.get(song_name, "")).strip()
            if artist_name:
                artist_counts[artist_name] = artist_counts.get(artist_name, 0.0) + 1.0

    total = float(sum(artist_counts.values()))
    if total <= 0:
        return {}
    return {artist: (count / total) for artist, count in artist_counts.items()}


def render_seed_experience(data: pd.DataFrame) -> tuple[dict[str, float], dict[str, Any]]:
    _init_seed_selection_state(data)
    song_options, artist_options, quick_top_songs, quick_top_artists = get_seed_ui_options(data)

    st.markdown('<div class="action-title">Choose your move</div>', unsafe_allow_html=True)
    experience_options = ["Quick Mode", "Self Mix"]
    if "experience_mode" not in st.session_state or st.session_state["experience_mode"] not in experience_options:
        st.session_state["experience_mode"] = "Self Mix"
    experience_mode = st.radio(
        "Mix Mode",
        options=experience_options,
        key="experience_mode",
        horizontal=True,
        label_visibility="collapsed",
    )

    if experience_mode == "Quick Mode":
        vibe_options = list(PERSONALITY_PROFILES.keys())
        selected_vibe = st.radio(
            "Vibe Options",
            options=vibe_options,
            key="selected_vibe_option",
            horizontal=True,
        )
        vibe_seed, vibe_description = personality_seed_option(data, selected_vibe)
        st.caption(vibe_description)
        st.success(f"Vibe starter: {vibe_seed}")
        return {vibe_seed: 1.0}, {
            "experience_mode": "Quick Mode",
            "quick_vibe": selected_vibe,
        }

    start_mode_options = ["Pick Songs", "Pick Artists", "Surprise Me"]
    if "start_mode" not in st.session_state or st.session_state["start_mode"] not in start_mode_options:
        st.session_state["start_mode"] = "Pick Songs"
    start_mode = st.radio(
        "How to Start",
        options=start_mode_options,
        key="start_mode",
        horizontal=True,
        label_visibility="collapsed",
    )

    if start_mode == "Pick Songs":
        st.caption("Choose songs (search enabled). Max 5 total picks combined with artists.")
        song_limit = max(0, MAX_SEED_SELECTIONS - len(st.session_state["selected_seed_artists"]))
        if "song_picker_nonce" not in st.session_state:
            st.session_state["song_picker_nonce"] = 0
        song_picker_key = f"song_picker_ui_{st.session_state['song_picker_nonce']}"

        selected_songs = st.multiselect(
            "Song Picks",
            options=song_options,
            key=song_picker_key,
            placeholder="Search and select songs",
            max_selections=max(song_limit, 1),
            disabled=(song_limit == 0),
        )
        if song_limit == 0:
            st.caption("Song picks are locked because all 5 slots are already used by artist picks.")
        elif selected_songs:
            for song_name in _dedupe_preserve_order([str(item) for item in selected_songs]):
                _add_seed_selection("selected_seed_songs", song_name, MAX_SEED_SELECTIONS)
            st.session_state["song_picker_nonce"] += 1
            st.rerun()

        st.caption("Quick top songs")
        clicked_song = render_toggle_chips(
            quick_top_songs,
            selected_values=list(st.session_state["selected_seed_songs"]),
            key_prefix="quick_song_chip",
            min_chips=5,
        )
        if clicked_song:
            _toggle_seed_selection("selected_seed_songs", clicked_song, MAX_SEED_SELECTIONS)

        _render_final_pick_box()
        return _build_seed_weights_from_state(data), {"experience_mode": "Self Mix"}

    if start_mode == "Pick Artists":
        st.caption("Choose artists (search enabled). Max 5 total picks combined with songs.")
        artist_limit = max(0, MAX_SEED_SELECTIONS - len(st.session_state["selected_seed_songs"]))
        if "artist_picker_nonce" not in st.session_state:
            st.session_state["artist_picker_nonce"] = 0
        artist_picker_key = f"artist_picker_ui_{st.session_state['artist_picker_nonce']}"

        selected_artists = st.multiselect(
            "Artist Picks",
            options=artist_options,
            key=artist_picker_key,
            placeholder="Search and select artists",
            max_selections=max(artist_limit, 1),
            disabled=(artist_limit == 0),
        )
        if artist_limit == 0:
            st.caption("Artist picks are locked because all 5 slots are already used by song picks.")
        elif selected_artists:
            for artist_name in _dedupe_preserve_order([str(item) for item in selected_artists]):
                _add_seed_selection("selected_seed_artists", artist_name, MAX_SEED_SELECTIONS)
            st.session_state["artist_picker_nonce"] += 1
            st.rerun()

        st.caption("Quick top artists")
        clicked_artist = render_toggle_chips(
            quick_top_artists,
            selected_values=list(st.session_state["selected_seed_artists"]),
            key_prefix="quick_artist_chip",
            min_chips=5,
        )
        if clicked_artist:
            _toggle_seed_selection("selected_seed_artists", clicked_artist, MAX_SEED_SELECTIONS)

        _render_final_pick_box()
        return _build_seed_weights_from_state(data), {"experience_mode": "Self Mix"}

    if start_mode == "Surprise Me":
        if "surprise_counter" not in st.session_state:
            st.session_state["surprise_counter"] = 0

        if "surprise_seed_track" not in st.session_state:
            st.session_state["surprise_seed_track"] = ""

        if st.button("Spin Random Song", key="surprise_seed_button", use_container_width=False) or not st.session_state[
            "surprise_seed_track"
        ]:
            st.session_state["surprise_counter"] += 1
            candidates = data.sort_values(["momentum_score", "views", "stream"], ascending=False).head(250)
            picked_seed = candidates.sample(1, random_state=9000 + st.session_state["surprise_counter"]).iloc[0]["display_name"]
            st.session_state["surprise_seed_track"] = str(picked_seed)

        surprise_seed = str(st.session_state["surprise_seed_track"])
        st.success(f"Random starter: {surprise_seed}")
        st.caption("This mode uses one random song as the only starting point.")
        return {surprise_seed: 1.0}, {"experience_mode": "Self Mix"}
    return {_default_seed_track(data): 1.0}, {"experience_mode": "Self Mix"}


def main() -> None:
    st.set_page_config(page_title="DJ Mixing Station Studio", page_icon="🎵", layout="wide")
    apply_theme()

    st.markdown(
        """
        <div class="hero">
          <h1>DJ Mixing Station Studio</h1>
          <p>Shape your sound with smart mood controls and cross-platform signal blending.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Input")
        dataset_id = st.text_input("Kaggle Dataset", value=DEFAULT_DATASET_ID)
        uploaded_file = st.file_uploader("Or upload CSV", type=["csv"])

    try:
        raw_df, source_path, dataset_path = read_source(uploaded_file, dataset_id)
        data = prepare_music_data_cached(raw_df)
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    if dataset_path != "uploaded_file":
        st.caption(f"Path to dataset files: `{dataset_path}`")
        st.caption(f"CSV source: `{source_path}`")

    if data.empty:
        st.error("No usable rows found after cleaning the dataset.")
        st.stop()

    seed_weights, experience_state = render_seed_experience(data)

    with st.sidebar:
        st.header("Recommendation Controls")
        if experience_state.get("experience_mode") == "Quick Mode":
            selected_quick_vibe = str(experience_state.get("quick_vibe", "Focus Flow"))
            quick_defaults = QUICK_VIBE_DEFAULTS.get(selected_quick_vibe, QUICK_VIBE_DEFAULTS["Focus Flow"])
            if st.session_state.get("quick_vibe_applied") != selected_quick_vibe:
                st.session_state["quick_spotify_weight_pct"] = int(quick_defaults["spotify_weight_pct"])
                st.session_state["quick_discovery_hits_pct"] = int(quick_defaults["discovery_hits_pct"])
                st.session_state["quick_vibe_applied"] = selected_quick_vibe

            mood = str(quick_defaults["mood"])
            spotify_weight_pct = st.slider("Platform Bias", 0, 100, key="quick_spotify_weight_pct")
            youtube_weight_pct = 100 - spotify_weight_pct
            st.caption(f"Spotify ({spotify_weight_pct}%) <- -> YouTube ({youtube_weight_pct}%)")
            discovery_hits_pct = st.slider("Discovery Mode", 0, 100, key="quick_discovery_hits_pct")
            hidden_gems_pct = 100 - discovery_hits_pct
            st.caption(f"Hits ({discovery_hits_pct}%) <- -> Hidden Gems ({hidden_gems_pct}%)")
        else:
            self_mix_vibe = st.selectbox("Vibe Options", options=list(PERSONALITY_PROFILES.keys()), index=0, key="self_mix_vibe_option")
            mood = str(QUICK_VIBE_DEFAULTS.get(self_mix_vibe, QUICK_VIBE_DEFAULTS["Focus Flow"])["mood"])
            if "spotify_weight_pct" not in st.session_state:
                st.session_state["spotify_weight_pct"] = 65
            spotify_weight_pct = st.slider("Platform Bias", 0, 100, key="spotify_weight_pct")
            youtube_weight_pct = 100 - spotify_weight_pct
            st.caption(f"Spotify ({spotify_weight_pct}%) <- -> YouTube ({youtube_weight_pct}%)")
            if "discovery_hits_pct" not in st.session_state:
                st.session_state["discovery_hits_pct"] = 65
            discovery_hits_pct = st.slider("Discovery Mode", 0, 100, key="discovery_hits_pct")
            hidden_gems_pct = 100 - discovery_hits_pct
            st.caption(f"Hits ({discovery_hits_pct}%) <- -> Hidden Gems ({hidden_gems_pct}%)")

        target_minutes = st.slider("Total Playlist Minutes (±3 mins)", 30, 300, 120)
        lower_window = target_minutes - PLAYLIST_TOLERANCE_MINUTES
        upper_window = target_minutes + PLAYLIST_TOLERANCE_MINUTES
        st.caption(
            f"Playlist window: {lower_window} to {upper_window} mins "
            f"({format_hours_minutes(lower_window)} to {format_hours_minutes(upper_window)})"
        )

    seed_weight_items = tuple(sorted((str(name), float(weight)) for name, weight in seed_weights.items()))
    preferred_artist_weight_items: tuple[tuple[str, float], ...] = ()
    if experience_state.get("experience_mode") == "Self Mix":
        preferred_artist_weight_items = tuple(sorted(_build_preferred_artist_weights(data).items()))
    include_seed_tracks = discovery_hits_pct == 100

    recommendations = recommend_tracks_cached(
        data=data,
        seed_weight_items=seed_weight_items,
        mood=mood,
        spotify_weight=spotify_weight_pct / 100.0,
        discovery_mode=hidden_gems_pct / 100.0,
        top_k=180,
        exclude_seed_tracks=not include_seed_tracks,
        preferred_artist_weight_items=preferred_artist_weight_items,
    )
    playlist = build_duration_playlist_cached(
        recommendations=recommendations,
        target_minutes=target_minutes,
        tolerance_minutes=PLAYLIST_TOLERANCE_MINUTES,
        candidate_limit=180,
        max_tracks=50,
    )
    playlist["mood_tag"] = mood
    total_playlist_minutes = pd.to_numeric(playlist.get("duration_ms"), errors="coerce").fillna(0).sum() / 60_000
    left, mid, right = st.columns(3)
    with left:
        render_metric_card("Tracks Available", f"{len(data):,}")
    with mid:
        render_metric_card("Artists Available", f"{data['artist'].nunique():,}")
    with right:
        render_metric_card("Playlist Duration", format_total_duration(total_playlist_minutes))

    if playlist.empty:
        st.warning("No playlist could be generated for this duration target. Try different seed selections.")
        st.stop()
    if not (lower_window <= total_playlist_minutes <= upper_window):
        st.warning(
            f"No exact playlist found in {lower_window}-{upper_window} mins. "
            f"Showing closest match: {format_total_duration(total_playlist_minutes)}."
        )

    st.subheader("Playable Playlist")
    queue = playlist.copy().reset_index(drop=True)
    queue["position"] = queue.index + 1
    queue["duration_text"] = queue["duration_ms"].apply(format_track_duration)
    queue["spotify_url"] = queue.apply(
        lambda row: row.get("spotify_link") or row.get("url_spotify") or "",
        axis=1,
    )
    queue["youtube_url"] = queue.apply(
        lambda row: row.get("youtube_link") or row.get("url_youtube") or "",
        axis=1,
    )
    queue["queue_label"] = queue.apply(
        lambda row: f'{int(row["position"]):02d}. {row["artist"]} - {row["track"]} ({row["duration_text"]})',
        axis=1,
    )

    player_col, mode_col = st.columns([3, 2])
    with player_col:
        selected_label = st.selectbox("Now Playing", options=queue["queue_label"].tolist())
    with mode_col:
        playback_platform = st.radio("Playback", options=["Auto", "Spotify", "YouTube"], horizontal=True)

    selected_row = queue.loc[queue["queue_label"] == selected_label].iloc[0]
    selected_spotify = str(selected_row["spotify_url"]).strip()
    selected_youtube = str(selected_row["youtube_url"]).strip()
    selected_youtube_watch = normalize_youtube_watch_url(selected_youtube)
    selected_spotify_track_id = extract_spotify_track_id(selected_spotify)

    st.markdown(
        f'**{selected_row["artist"]} - {selected_row["track"]}** · {selected_row["duration_text"]} '
        f'· Momentum {selected_row["momentum_score"]:.3f}'
    )
    render_track_links(selected_spotify, selected_youtube)

    if playback_platform == "YouTube":
        if selected_youtube_watch:
            st.video(selected_youtube_watch)
        elif selected_youtube:
            st.info("No direct YouTube video ID available for embed. Use the YouTube button.")
    elif playback_platform == "Spotify":
        if selected_spotify_track_id:
            embed_url = f"https://open.spotify.com/embed/track/{selected_spotify_track_id}?utm_source=generator"
            components.html(
                f'<iframe src="{embed_url}" width="100%" height="152" frameborder="0" '
                'allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>',
                height=170,
            )
        elif selected_spotify:
            st.info("No direct Spotify track ID available for embed. Use the Spotify button.")
    else:
        if selected_youtube_watch:
            st.video(selected_youtube_watch)
        elif selected_spotify_track_id:
            embed_url = f"https://open.spotify.com/embed/track/{selected_spotify_track_id}?utm_source=generator"
            components.html(
                f'<iframe src="{embed_url}" width="100%" height="152" frameborder="0" '
                'allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>',
                height=170,
            )

    youtube_ids = []
    for url in queue["youtube_url"].tolist():
        video_id = extract_youtube_video_id(url)
        if video_id and video_id not in youtube_ids:
            youtube_ids.append(video_id)

    if len(youtube_ids) >= 2:
        temp_youtube_playlist = "https://www.youtube.com/watch_videos?video_ids=" + ",".join(youtube_ids[:50])
        render_platform_link("Open Temporary YouTube Playlist", temp_youtube_playlist)
    else:
        st.caption("Temporary YouTube playlist link requires at least 2 direct video IDs.")

    st.subheader("Recommendation Debug View")
    render_modern_debug_table(playlist)


if __name__ == "__main__":
    main()
