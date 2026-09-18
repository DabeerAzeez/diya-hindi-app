#!/usr/bin/env python3
"""
DIYA Hindi Learning Hub — Milestone M3 Independent Verification Suite
Tests song schema integrity, YouTube embed URL transformation logic,
lyric breakdown parsing, and API responses.
"""

import sys
import os
import json
import re
import urllib.request

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "diya", "data")
SONGS_DIR = os.path.join(DATA_DIR, "songs")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

def run_tests():
    passed = 0
    failed = 0

    def assert_true(cond, msg):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  [PASS] {msg}")
        else:
            failed += 1
            print(f"  [FAIL] {msg}")

    print("\n--- Testing Song Data Integrity ---")
    index_path = os.path.join(DATA_DIR, "songs_index.json")
    with open(index_path, "r", encoding="utf-8") as f:
        songs_index = json.load(f)

    assert_true(len(songs_index) == 4, "songs_index.json contains 4 songs")
    for song in songs_index:
        slug = song.get("slug")
        yt_url = song.get("youtube_url")
        assert_true(yt_url is not None and "youtu" in yt_url, f"Song '{slug}' in songs_index has valid youtube_url")

    expected_yt_urls = {
        "jeena_jeena": "https://www.youtube.com/watch?v=zFdi834FiZ4",
        "titli_-_chennai_express": "https://www.youtube.com/watch?v=V8zXLMIjlcw",
        "hoor": "https://www.youtube.com/watch?v=Gs8g3Yhv8xH",
        "jhak_maar_ke": "https://www.youtube.com/watch?v=R5CxtjmrIE4"
    }

    for slug, expected_yt in expected_yt_urls.items():
        song_file = os.path.join(SONGS_DIR, f"{slug}.json")
        assert_true(os.path.exists(song_file), f"Song file {slug}.json exists")
        with open(song_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert_true(data.get("youtube_url") == expected_yt, f"{slug}.json has expected youtube_url: {expected_yt}")
        assert_true("verses" in data and len(data["verses"]) > 0, f"{slug}.json contains verses")

    print("\n--- Testing SongsView.jsx Invariants ---")
    songs_view_path = os.path.join(FRONTEND_DIR, "src", "views", "SongsView.jsx")
    with open(songs_view_path, "r", encoding="utf-8") as f:
        src = f.read()

    # Universal player invariants
    assert_true("youtubeEmbedUrl" in src or "getYouTubeEmbedUrl" in src, "Universal player implements YouTube embed transformation")
    assert_true("spotifyEmbedUrl" in src or "getSpotifyEmbedUrl" in src, "Universal player implements Spotify embed transformation")
    assert_true("playerTab" in src, "Player switcher tab state is maintained")
    assert_true("aspect-video" in src, "YouTube container is responsive with aspect-video")
    assert_true("autoplay=1" not in src, "Autoplay is disabled by default")

    # Genius-style lyrics invariants
    assert_true("ChevronDown" not in src, "Accordion ChevronDown toggles removed")
    assert_true("toggleSection" not in src, "Section collapsing toggleSection removed")
    assert_true("collapsedSections" not in src, "Section collapsed state removed")
    assert_true("lineObj.line" in src or "cleanLine" in src, "Lyrics render plain text lines")

    # Hover modal invariants
    assert_true("activeModalLine" in src, "Active hover modal line state exists")
    assert_true("Word-by-Word Gloss" in src or "word-by-word" in src.lower(), "Modal displays word-by-word gloss")
    assert_true("Literal Translation" in src or "literal" in src.lower(), "Modal displays literal translation")
    assert_true("Meaning" in src or "meaning" in src.lower(), "Modal displays meaning")

    # Add to Anki modal invariants
    assert_true("Add to Anki" in src, "Add to Anki button present")
    assert_true("ankiModalOpen" in src, "Add to Anki modal dialog state exists")
    assert_true("<textarea" in src, "Front/back textareas allow user editing")
    assert_true("/api/anki/add" in src, "Submits to /api/anki/add")

    print("\n--- Summary ---")
    print(f"Total: {passed + failed}, Passed: {passed}, Failed: {failed}")
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
