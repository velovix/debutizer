import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread


class LocalRepository:
    """Hosts an APT repository based on the contents in the artifacts dir. This allows
    Debutizer packages to download other Debutizer packages as dependencies.
    """

    def __init__(self, port: int, artifacts_dir: Path):
        self._artifacts_dir = artifacts_dir
        self._server = ThreadingHTTPServer(
            ("", port),
            functools.partial(SimpleHTTPRequestHandler, directory=artifacts_dir),
        )
        self._server.allow_reuse_address = True

        self._thread = Thread(
            name="Local Repository",
            target=self._server.serve_forever,
            daemon=True,
        )

    def start(self):
        self._thread.start()

    def close(self):
        self._server.shutdown()
