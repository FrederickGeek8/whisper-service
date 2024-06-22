# A (Basic, Local) Voice Transcription Service

This is a small Python script I wrote so that audio files that are placed in certain directories can be automatically transcribed **recursively** and **locally** by OpenAI Whisper models.

This can be good when you want to transcribe your WhatsApp Voice Notes that you've synced from your Android via [Syncthing](https://syncthing.net/) or when you've bought a [dedicated voice recorder device](https://learnandsupport.getolympus.com/support/dm-720) and you want to be able to transcribe your audio notes without selling all of your personal life to cloud service. This can also be useful if you plan to maintain a natural language index to search your notes with in the future!

Perhaps someday I will set up a cronjob or similar to automatically transcribe the notes that are specified in the configuration (see the [**Configuration**](#configuration) description below), but for now I manually run this script.

## Disclaimer

Take note of the MIT License, namely: _no liability_ and _no warranty_. I, in fact, _do not even like this code I wrote_!

Pull requests are accepted but I have no obligation to work on any Issues you may post. Be inspired by this code, have fun, and contribute if you want, but remember that [I ultimately owe you nothing](https://web.archive.org/web/20240105081542/https://www.softwaremaxims.com/blog/not-a-supplier).

## Usage & General Operation

### Prerequisities

This project was developed in Python 3.9, and only (externally) depends on the `openai-whisper` Python package. A conda `environment.yml` environment file has been provided and well as `requirements.txt`. The `requirements.txt` file contains just `openai-whisper` at version `20231117`, and the conda environment provided in `environment.yml` just installs Python 3.9 as well as what is in `requirements.txt`.

### Usage

The primary script in this repository is `transcribe_service.py` which is simply run with:

```bash
python transcribe_service.py
```

The script consumes a configuration file `transcription_config.json` and will produce a `transcription_cache.json` file so that it does not re-transcribe files unnecessarily (which is important if it is on a cronjob).

The script does the following:

1. Read in the configuration
2. Checks the existence of input directories
3. Loads the cache & _merges with the configuration file_ (doing minor consistency checks and adding new input directories).
4. Creates a processing plan such that each input audio file is transcribed if it (1) has not previously been transcribed (checked via output file existence) and (2) the input has not been modified (checked via `sha256`).
5. Processes each new audio file to an output folder such that _the relative path between the input root and the audio file is preserved in the output folder_.

### Configuration

The folders to be processed are configured in the `transcription_config.json` file. The structure is as follow:

```json
{
  "version": 1, // configuration version - currently unused
  "output_format": "txt", // compatible output format for whisper
  "temperature": 0, // whisper model temperature parameter
  "glossary": ["SuperSpecialWord", "grok"], // vocab "glossary" injected into a prompt
  // process each audio file in each input_root (recursively) into output_root
  "directories": {
    "/path/to/input_root": {
      "output_root": "/path/to/output_root"
    },
    "/path/to/input_root_2": {
      "output_root": "/path/to/output_root_2"
    }
  }
}
```

the most important configuration key is `directories` which defines what directories to process automatically. _Audio will be **recursively** searched for in each directory and processed as long as it seems as though it hasn't before._

The "seems" part of the above statement can be partially explained by the variant of `transcription_config.json` -- `transcription_cache.json`. The diffference is that for each input root folder, there is a "cache" of audio files that has a corresponding `sha256` hash attached. The means that if the underlying audio file changes, the transcription will be reprocessed.

```json
{
  "version": 1, // configuration version - currently unused
  "output_format": "txt", // compatible output format for whisper
  "temperature": 0, // whisper model temperature parameter
  "glossary": ["SuperSpecialWord", "grok"], // vocab "glossary" injected into a prompt
  // process each audio file in each input_root (recursively) into output_root
  "directories": {
    "/path/to/input_root": {
      "output_root": "/path/to/output_root",
      "cache": {
        "202421/PTT-20240525-WA0018.opus": {
          "sha256": "2d6c2027e0212b40d070d48e188dd33e48f7eaaf87816a8000cee6a397d3e0e6"
        },
        "202421/PTT-20240524-WA0007.opus": {
          "sha256": "0e3219be2eb612e44a124a5a2cc122287a9eea54bf552de54146cc49c44fbdd4"
        }
      }
    }
  }
}
```

a transcription will also be reprocessed if the output file is not detected any longer.

## Explanation of Files

### Important Files

- `transcribe_service.py` -- primary script. Read/resolves the config/cache and builds an "execution plan".
- `plan.py` the file that reads the plan from `transcribe_service` and executes the transcriptions according to the plan.

### Helpers

- `cache_format.py` -- defines the TypedDict's that are stored in the configuration and cache file.
- `exceptions.py` -- small file that just defines a rarely used custom exception and a CLI confirmation helper function
- `hashing.py` -- contains a helper function for computing `sha256` checksums of files.
