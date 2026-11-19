"""
Vercel Blob persistence for the web app's SQLite file, tested with a FAKE Blob store.
Simulates two different Vercel servers: a run saved on one must appear in History on another.
"""

import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

import blob_db
import config


class FakeBlob:
    """Same function names as vercel.blob, but stores bytes in a dict."""
    class BlobNotFoundError(Exception):
        pass

    def __init__(self):
        self.files, self.puts = {}, 0

    async def get_blob(self, pathname, access):
        if pathname not in self.files:
            raise self.BlobNotFoundError(pathname)
        return SimpleNamespace(body=self.files[pathname])

    async def put_blob(self, pathname, body, access, allow_overwrite=False, **kw):
        if pathname in self.files and not allow_overwrite:
            raise RuntimeError("exists")
        self.files[pathname] = bytes(body)
        self.puts += 1


class BlobPersistence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.store = FakeBlob()
        self.patches = [mock.patch.object(config, "ON_VERCEL", True),
                        mock.patch.dict(os.environ, {"BLOB_READ_WRITE_TOKEN": "fake"})]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def _server(self, name):
        """A fresh 'Vercel server': its own empty /tmp database path."""
        return mock.patch.object(config, "DATABASE_PATH", os.path.join(self.tmp, f"{name}.db"))

    def test_disabled_locally(self):
        with mock.patch.object(config, "ON_VERCEL", False):
            self.assertFalse(blob_db.enabled())
            self.assertEqual(blob_db.pull(blob=self.store), "")

    def test_run_saved_on_one_server_shows_on_another(self):
        import index
        real_pull, real_push = blob_db.pull, blob_db.push
        with mock.patch.object(blob_db, "pull", lambda: real_pull(blob=self.store)), \
                mock.patch.object(blob_db, "push", lambda: real_push(blob=self.store)):
            label = [d for d in index.DEMO_COMPANIES if d.startswith("Vaultwise")][0]
            with self._server("a"), mock.patch.object(config, "FORCE_MOCK_LLM", True):
                index.app.test_client().post("/run", data={"source": "demo", "demo": label})
            self.assertEqual(self.store.puts, 1)
            with self._server("b"):
                page = index.app.test_client().get("/history").text
            self.assertIn("vaultwise", page.lower())
            self.assertIn("Vercel Blob", page)

    def test_storage_errors_never_break_a_run(self):
        class Broken(FakeBlob):
            async def get_blob(self, *a, **k):
                raise ConnectionError("down")
        with self._server("c"):
            self.assertIn("could not load", blob_db.pull(blob=Broken()))


if __name__ == "__main__":
    unittest.main()
