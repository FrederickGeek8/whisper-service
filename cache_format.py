import json
from pathlib import Path
from typing import Dict, List, Literal, TypedDict, Union, cast

INPUT_FORMATS = {".flac", ".mp3", ".wav", ".opus"}
OUTPUT_FORMATS = {"txt", "vtt", "srt", "tsv", "json", "all"}
output_t = Literal["txt", "vtt", "srt", "tsv", "json", "all"]

CACHE_DIR = Path(__file__).parent
CACHE_FILE = CACHE_DIR / "transcription_cache.json"
CONFIG_FILE = CACHE_DIR / "transcription_config.json"


class CacheItem(TypedDict):
    sha256: str


class TrackedDir(TypedDict):
    output_root: str


class CachedDir(TrackedDir):
    cache: Dict[str, CacheItem]


class ConfigFile(TypedDict):
    version: int
    output_format: output_t
    temperature: float
    directories: Dict[str, TrackedDir]
    glossary: List[str]


class CacheFile(ConfigFile):
    directories: Dict[str, CachedDir]


class PlanItem(TypedDict):
    input_root: str
    output_root: str
    relative_path: str


def elevate_tracked_dir(tracked_dir: TrackedDir) -> CachedDir:
    temp = dict(tracked_dir)
    temp["cache"] = {}

    return cast(CachedDir, temp)


def elevate_tracked_obj(tracked_dir: ConfigFile) -> CacheFile:
    temp = dict(tracked_dir)
    for directory in tracked_dir["directories"]:
        temp["directories"][directory] = elevate_tracked_dir(  # type: ignore
            tracked_dir["directories"][directory]
        )

    return cast(CacheFile, temp)


def update_cache(cache: CacheFile, cache_path: Union[str, Path] = CACHE_FILE):
    with open(cache_path, "wt", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
