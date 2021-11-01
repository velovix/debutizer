from pathlib import Path
from threading import Thread
from wsgiref import simple_server

import flask

# TODO: Consider using http.server instead of Flask when Python 3.6 is no
#       longer supported


class LocalRepository:
    """Hosts an APT repository based on the contents in the artifacts dir. This allows
    Debutizer packages to download other Debutizer packages as dependencies.
    """

    def __init__(self, port: int, artifacts_dir: Path):
        self._artifacts_dir = artifacts_dir
        self._app = flask.Flask(__name__)

        @self._app.route("/<path:path>")
        def static_files(path: str) -> flask.Response:
            return flask.send_from_directory(self._artifacts_dir, path)

        self._server = simple_server.make_server(
            "0.0.0.0",
            port,
            app=self._app,
            handler_class=simple_server.WSGIRequestHandler,
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
        self._server.server_close()
        self._thread.join()
