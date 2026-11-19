"""
Keeps the web app's SQLite database between Vercel requests, using Vercel Blob storage.

Why: on Vercel each request may run on a different short-lived server, and /tmp is
wiped when a server stops. So the SQLite file is:
  * downloaded from Blob storage before a run or the History page (pull), and
  * uploaded back after a run is saved (push).
The database is still plain SQLite (db.py is unchanged); Blob only stores the file.

It switches on only when a Blob store is connected to the Vercel project (Vercel then
sets BLOB_READ_WRITE_TOKEN). Locally nothing changes: outreach.db stays on disk.

Limitation: if two people finish a run at almost the same moment, the later upload
wins and one run can be missing from History. Fine for a demo / assignment.
"""

import asyncio
import os

import config

PATHNAME = "sprinto-outreach/outreach.db"


def enabled():
    return config.ON_VERCEL and bool(os.getenv("BLOB_READ_WRITE_TOKEN") or os.getenv("BLOB_STORE_ID"))


def _access():
    return os.getenv("BLOB_ACCESS", "private").strip().lower() or "private"


def pull(blob=None):
    """Download the saved database into DATABASE_PATH. Returns a status message."""
    if not enabled():
        return ""
    if blob is None:
        from vercel import blob
    try:
        result = asyncio.run(blob.get_blob(PATHNAME, access=_access()))
    except blob.BlobNotFoundError:
        return "no saved history yet"
    except Exception as e:                       # never break a run because of storage
        return f"could not load saved history ({type(e).__name__})"
    with open(config.DATABASE_PATH, "wb") as f:
        f.write(result.body)
    return "loaded"


def push(blob=None):
    """Upload DATABASE_PATH so the next request (on any server) sees this run."""
    if not enabled() or not os.path.exists(config.DATABASE_PATH):
        return ""
    if blob is None:
        from vercel import blob
    with open(config.DATABASE_PATH, "rb") as f:
        data = f.read()
    try:
        asyncio.run(blob.put_blob(PATHNAME, data, access=_access(), allow_overwrite=True,
                                  content_type="application/vnd.sqlite3",
                                  cache_control_max_age=60))
    except Exception as e:
        return f"could not save history ({type(e).__name__})"
    return "saved"
