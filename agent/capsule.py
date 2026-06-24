"""pack a research result into a tiny portable "capsule" string you can paste anywhere.

a capsule is the whole structured result, json-encoded, gzipped, and base64'd behind a little
version header. it round-trips losslessly, so you can drop a research answer into a chat message
or a gist and someone else can decode it back into the original object. optionally render it as
a qr code if the `qrcode` extra is installed.

no required deps, fully offline, trivially testable.
"""

from __future__ import annotations

import base64
import gzip
import json
from typing import Any

_HEADER = "AICAP1:"


class CapsuleError(ValueError):
    """raised when a string isn't a valid capsule."""


def encode(obj: Any) -> str:
    """json -> gzip -> base64, with a version header. returns an ascii-safe capsule string."""
    raw = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    packed = gzip.compress(raw, compresslevel=9)
    return _HEADER + base64.urlsafe_b64encode(packed).decode("ascii")


def decode(capsule: str) -> Any:
    """reverse encode(). raises CapsuleError on anything that isn't a real capsule."""
    capsule = capsule.strip()
    if not capsule.startswith(_HEADER):
        raise CapsuleError("not a capsule (missing header)")
    body = capsule[len(_HEADER) :]
    try:
        packed = base64.urlsafe_b64decode(body.encode("ascii"))
        raw = gzip.decompress(packed)
        return json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - any failure means a bad capsule
        raise CapsuleError(f"could not decode capsule: {exc}") from exc


def to_qr(capsule: str, path: str) -> str:
    """write the capsule out as a qr png. needs `pip install qrcode[pil]`."""
    try:
        import qrcode
    except ImportError as exc:  # pragma: no cover - optional dep
        raise RuntimeError("pip install 'qrcode[pil]' to render capsules as qr codes") from exc
    img = qrcode.make(capsule)
    img.save(path)
    return path
