import json
import os
import warnings
from pathlib import Path
from typing import Optional

import whisper

from cache_format import (
    CACHE_FILE,
    CONFIG_FILE,
    INPUT_FORMATS,
    CacheFile,
    ConfigFile,
    elevate_tracked_dir,
    elevate_tracked_obj,
    update_cache,
)
from exceptions import CacheIncoherentError, confirm
from hashing import sha256sum
from plan import execute_plan


def build_cache(config_obj: ConfigFile, prev_cache: Optional[CacheFile]) -> CacheFile:
    """Add directories to the cache if they do not exist. Warn if the cache is inconsistent."""
    if prev_cache is None:
        return elevate_tracked_obj(config_obj)

    if config_obj["output_format"] != prev_cache["output_format"]:
        print("WARNING: Output format differs. Cache must be rebuilt.")
        raise CacheIncoherentError(reason="format")

    if config_obj["temperature"] != prev_cache["temperature"]:
        print(
            f"WARNING: Temperature differs. Cache contains "
            f'{prev_cache["temperature"]} but config contains {config_obj["temperature"]}. '
            f'Using new temperature of {config_obj["temperature"]}.'
        )
        prev_cache["temperature"] = config_obj["temperature"]

    if set(config_obj["glossary"]) != set(prev_cache["glossary"]):
        print(
            f"WARNING: Glossary differs. Cache contains "
            f'{prev_cache["glossary"]} but config contains {config_obj["glossary"]}. '
            f'Using new glossary of {config_obj["glossary"]}.'
        )
        prev_cache["glossary"] = config_obj["glossary"]

    # check the consistency of each configured directory
    # the _output root_ should not be different. if the output root exists
    # then the contents could be overwritten (if they are not cached)
    # if the directory _does not exist_, then the cache needs to be rebuilt

    # NOTE: This function should not be responsible for building the cache or
    # verifying the hash of the files. those functions should be delegated to
    # the function that is computing a "action plan" or the list of files to
    # be processed.

    # Update directories
    for input_root, config_dir in config_obj["directories"].items():
        input_root = str(Path(input_root).resolve())
        if input_root in prev_cache["directories"]:
            # input directory exists in cache
            cached_output = str(
                Path(prev_cache["directories"][input_root]["output_root"]).resolve()
            )
            config_output = str(Path(config_dir["output_root"]).resolve())
            if config_output != cached_output:
                print(
                    f"\nWARNING: Got incoherent output path. For input path {input_root}:"
                )
                print(f"\tCached output root: {cached_output}")
                print(f"\tNew config root: {config_output}")
                print(
                    "The new output directory will override the old directory and the cache will be overwritten."
                )
                prev_cache["directories"][input_root] = elevate_tracked_dir(config_dir)
        else:
            # input directory does not exist in cache -- should be added
            print(
                f"INFO: Detected new transcription input directory {input_root}. Adding to current set."
            )
            prev_cache["directories"][input_root] = elevate_tracked_dir(config_dir)

    return prev_cache


def main():
    # read config json
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config_ = json.load(f)
        config_ = ConfigFile(config_)

    # sanity check directory existence
    for input_path in config_["directories"]:
        root_ = Path(input_path)

        assert (
            root_.is_dir()
        ), f"Configured input directory {root_.resolve()} is not a directory."

    prev_cache_ = None
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            prev_cache_ = json.load(f)
            prev_cache_ = CacheFile(prev_cache_)

    try:
        cache_ = build_cache(config_, prev_cache_)
    except CacheIncoherentError as e:
        if e.reason == "format":
            if confirm("Erase cache and reprocess all input files?"):
                cache_ = elevate_tracked_obj(config_)
            else:
                exit(1)
        else:
            raise e

    # create a list of files to process
    plan = []
    for input_root, dir_dict in cache_["directories"].items():
        output_root = dir_dict["output_root"]

        for sub_root, _, files in os.walk(input_root):
            if len(files) == 0:
                continue

            for file in files:
                f_path = Path(sub_root) / file

                if f_path.suffix.lower() not in INPUT_FORMATS:
                    continue

                relative_key = str(f_path.relative_to(input_root))
                if relative_key in dir_dict["cache"]:
                    audio_output_path = Path(output_root) / relative_key
                    audio_output_parent = audio_output_path.parent
                    # get output files that start with file stem
                    possible_outputs = list(
                        audio_output_parent.glob(f"{f_path.stem}.*")
                    )
                    if (
                        len(possible_outputs) > 0
                        and sha256sum(f_path)
                        == dir_dict["cache"][relative_key]["sha256"]
                    ):
                        continue

                plan.append(
                    {
                        "input_root": input_root,
                        "output_root": output_root,
                        "relative_path": relative_key,
                    }
                )

    print(f"Planning complete. {len(plan)} directories to process.")

    whisper_model = whisper.load_model("tiny.en")
    new_cache = execute_plan(plan, cache_, whisper_model)

    update_cache(new_cache)


if __name__ == "__main__":
    warnings.filterwarnings(
        "ignore", message="FP16 is not supported on CPU; using FP32 instead"
    )
    main()
