"""Local cache for Yoto library data using HA Store."""

from __future__ import annotations

import logging
import time as time_mod

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from yoto_api import Card, Chapter, Track

_LOGGER = logging.getLogger(__name__)

CACHE_VERSION = 1
CACHE_KEY_PREFIX = "yoto.library"


class YotoLibraryCache:
    """Local cache for Yoto library data using HA Store."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize cache with HA storage."""
        self._store = Store(hass, CACHE_VERSION, f"{CACHE_KEY_PREFIX}.{entry_id}")
        self._data: dict | None = None

    async def async_load(self) -> dict[str, Card] | None:
        """Load cached library from disk.

        Returns a dict of card_id -> Card, or None if no cache exists.
        """
        try:
            raw = await self._store.async_load()
            if raw is None:
                _LOGGER.debug("No cached library found on disk")
                return None
            library = _deserialize_library(raw.get("library", {}))
            timestamp = raw.get("timestamp")
            _LOGGER.debug(
                "Loaded cached library with %d cards (saved at %s)",
                len(library),
                timestamp,
            )
            return library
        except Exception:
            _LOGGER.warning(
                "Failed to load library cache, starting fresh", exc_info=True
            )
            return None

    async def async_save(self, library: dict[str, Card]) -> None:
        """Save library to disk cache."""
        try:
            data = {
                "timestamp": time_mod.time(),
                "library": _serialize_library(library),
            }
            await self._store.async_save(data)
            _LOGGER.debug("Saved library cache with %d cards", len(library))
        except Exception:
            _LOGGER.warning("Failed to save library cache", exc_info=True)

    async def async_get_card(self, card_id: str) -> Card | None:
        """Get a single card from cache."""
        try:
            raw = await self._store.async_load()
            if raw is None:
                return None
            library_data = raw.get("library", {})
            card_data = library_data.get(card_id)
            if card_data is None:
                return None
            return _deserialize_card(card_data)
        except Exception:
            _LOGGER.warning(
                "Failed to load card %s from cache", card_id, exc_info=True
            )
            return None

    async def async_save_card_detail(self, card_id: str, card: Card) -> None:
        """Save individual card detail to cache.

        Updates the card entry in the existing cache without overwriting
        other cards.
        """
        try:
            raw = await self._store.async_load()
            if raw is None:
                raw = {"timestamp": time_mod.time(), "library": {}}
            raw["library"][card_id] = _serialize_card(card)
            raw["timestamp"] = time_mod.time()
            await self._store.async_save(raw)
            _LOGGER.debug("Saved card detail for %s to cache", card_id)
        except Exception:
            _LOGGER.warning(
                "Failed to save card detail %s to cache", card_id, exc_info=True
            )


def _serialize_library(library: dict[str, Card]) -> dict:
    """Convert a library dict of Card objects to JSON-serializable dicts."""
    result = {}
    for card_id, card in library.items():
        result[card_id] = _serialize_card(card)
    return result


def _serialize_card(card: Card) -> dict:
    """Convert a Card object to a JSON-serializable dict."""
    card_dict = {
        "id": card.id,
        "title": card.title,
        "description": card.description,
        "category": card.category,
        "author": card.author,
        "cover_image_large": card.cover_image_large,
        "series_title": card.series_title,
        "series_order": card.series_order,
        "chapters": None,
    }
    if card.chapters:
        card_dict["chapters"] = {}
        for chapter_key, chapter in card.chapters.items():
            card_dict["chapters"][chapter_key] = _serialize_chapter(chapter)
    return card_dict


def _serialize_chapter(chapter: Chapter) -> dict:
    """Convert a Chapter object to a JSON-serializable dict."""
    chapter_dict = {
        "icon": chapter.icon,
        "title": chapter.title,
        "duration": chapter.duration,
        "key": chapter.key,
        "tracks": None,
    }
    if chapter.tracks:
        chapter_dict["tracks"] = {}
        for track_key, track in chapter.tracks.items():
            chapter_dict["tracks"][track_key] = _serialize_track(track)
    return chapter_dict


def _serialize_track(track: Track) -> dict:
    """Convert a Track object to a JSON-serializable dict."""
    return {
        "icon": track.icon,
        "title": track.title,
        "duration": track.duration,
        "key": track.key,
        "format": track.format,
        "channels": track.channels,
        "trackUrl": track.trackUrl,
        "type": track.type,
    }


def _deserialize_library(data: dict) -> dict[str, Card]:
    """Convert dicts back to a library dict of Card objects."""
    library = {}
    for card_id, card_data in data.items():
        library[card_id] = _deserialize_card(card_data)
    return library


def _deserialize_card(data: dict) -> Card:
    """Convert a dict back to a Card object."""
    card = Card(
        id=data.get("id"),
        title=data.get("title"),
        description=data.get("description"),
        category=data.get("category"),
        author=data.get("author"),
        cover_image_large=data.get("cover_image_large"),
        series_title=data.get("series_title"),
        series_order=data.get("series_order"),
    )
    chapters_data = data.get("chapters")
    if chapters_data:
        card.chapters = {}
        for chapter_key, chapter_data in chapters_data.items():
            card.chapters[chapter_key] = _deserialize_chapter(chapter_data)
    return card


def _deserialize_chapter(data: dict) -> Chapter:
    """Convert a dict back to a Chapter object."""
    chapter = Chapter(
        icon=data.get("icon"),
        title=data.get("title"),
        duration=data.get("duration"),
        key=data.get("key"),
    )
    tracks_data = data.get("tracks")
    if tracks_data:
        chapter.tracks = {}
        for track_key, track_data in tracks_data.items():
            chapter.tracks[track_key] = _deserialize_track(track_data)
    return chapter


def _deserialize_track(data: dict) -> Track:
    """Convert a dict back to a Track object."""
    return Track(
        icon=data.get("icon"),
        title=data.get("title"),
        duration=data.get("duration"),
        key=data.get("key"),
        format=data.get("format"),
        channels=data.get("channels"),
        trackUrl=data.get("trackUrl"),
        type=data.get("type"),
    )
