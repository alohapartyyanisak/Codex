from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

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


def read_source(uploaded_file: Any, dataset_id: str) -> tuple[pd.DataFrame, str, str]:
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file), uploaded_file.name, "uploaded_file"
    return load_from_kagglehub(dataset_id)


def render_metric_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
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


def main() -> None:
    st.set_page_config(page_title="Pulse Gold Recommender", page_icon="🎵", layout="wide")
    apply_theme()

    st.markdown(
        """
        <div class="hero">
          <h1>Pulse Gold Recommendation App</h1>
          <p>Content-driven track recommendations with mood shaping and Spotify/YouTube signal blending.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Input")
        dataset_id = st.text_input("Kaggle Dataset", value=DEFAULT_DATASET_ID)
        uploaded_file = st.file_uploader("Or upload CSV", type=["csv"])

        st.header("Recommendation Controls")
        mood = st.selectbox("Mood", options=list(MOOD_ADJUSTMENTS.keys()), index=0)
        spotify_weight_pct = st.slider("Platform Bias: Spotify <- -> YouTube", 0, 100, 65)
        discovery_pct = st.slider("Discovery Mode: Hits <- -> Hidden Gems", 0, 100, 35)
        target_minutes = st.slider("Total Playlist Minutes (±3 mins)", 30, 300, 120)
        lower_window = target_minutes - PLAYLIST_TOLERANCE_MINUTES
        upper_window = target_minutes + PLAYLIST_TOLERANCE_MINUTES
        st.caption(
            f"Playlist window: {lower_window} to {upper_window} mins "
            f"({format_hours_minutes(lower_window)} to {format_hours_minutes(upper_window)})"
        )

    try:
        raw_df, source_path, dataset_path = read_source(uploaded_file, dataset_id)
        data = prepare_music_data(raw_df)
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    if dataset_path != "uploaded_file":
        st.caption(f"Path to dataset files: `{dataset_path}`")
        st.caption(f"CSV source: `{source_path}`")

    if data.empty:
        st.error("No usable rows found after cleaning the dataset.")
        st.stop()

    seed_track = st.selectbox("Seed Track", options=sorted(data["display_name"].unique()))

    recommendations = recommend_tracks(
        data=data,
        seed_display_name=seed_track,
        mood=mood,
        spotify_weight=spotify_weight_pct / 100.0,
        discovery_mode=discovery_pct / 100.0,
        top_k=180,
    )
    playlist = build_duration_playlist(
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
        st.warning("No playlist could be generated for this duration target. Try a different seed track.")
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
    debug_cols = [
        "artist",
        "track",
        "duration_ms",
        "recommendation_score",
        "similarity_score",
        "platform_score",
        "discovery_score",
        "momentum_score",
        "views",
        "stream",
    ]
    st.dataframe(playlist[debug_cols], hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()
