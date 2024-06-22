import traceback
from pathlib import Path
from typing import List

import whisper
import whisper.utils
from tqdm import tqdm

from cache_format import CacheFile, PlanItem, update_cache
from hashing import sha256sum


def read_options(cache: CacheFile) -> dict:
    # TODO: I'm not planning on playing with this.. yet... no need.
    return {}


def execute_plan(
    plan: List[PlanItem], cache: CacheFile, model: whisper.Whisper
) -> CacheFile:
    pbar = tqdm(plan)
    for plan_item in pbar:
        input_path = plan_item["input_root"]
        output_path = plan_item["output_root"]
        audio_relative_path = plan_item["relative_path"]

        audio_path = Path(input_path) / audio_relative_path

        pbar.set_description_str(f"Processing {audio_path.name}")

        # 202424/PTT-20240613-WA0025.opus
        audio_output_path = Path(output_path) / audio_relative_path
        audio_output_parent = audio_output_path.parent.resolve()
        audio_output_parent.mkdir(exist_ok=True, parents=True)
        writer = whisper.utils.get_writer(
            cache["output_format"], str(audio_output_parent)
        )

        try:
            initial_prompt = None
            if "glossary" in cache and len(cache["glossary"]) > 0:
                glossary = ", ".join(map(lambda s: s.strip(), cache["glossary"]))
                initial_prompt = f"(Glossary: {glossary})"

            result = model.transcribe(
                str(audio_path.resolve()),
                temperature=cache["temperature"],
                initial_prompt=initial_prompt,
            )
            writer(result, str(audio_path.resolve()), read_options(cache))  # type: ignore # writer wants StringIO by typing...
        except Exception as e:
            traceback.print_exc()
            print(f"Skipping {audio_path} due to {type(e).__name__}: {str(e)}")

        # write cache sha256
        hashstr = sha256sum(audio_path)
        cache["directories"][plan_item["input_root"]]["cache"][audio_relative_path] = {
            "sha256": hashstr
        }

        update_cache(cache)

    return cache
