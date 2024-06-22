from hashlib import sha256
from pathlib import Path
from typing import Union


# Thank you to https://stackoverflow.com/a/44873382
def sha256sum(file_path: Union[str, Path]) -> str:
    h = sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(file_path, "rb", buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])

    return h.hexdigest()
