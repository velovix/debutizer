from pathlib import Path
from threading import Thread
from wsgiref import simple_server

import falcon


# TODO: Consider using http.server instead of Falcon when Python 3.6 is no
#       longer supported


class LocalRepository:
    """Hosts an APT repository based on the contents in the artifacts dir. This allows
    Debutizer packages to download other Debutizer packages as dependencies.
    """

    def __init__(self, port: int, artifacts_dir: Path):
        self._artifacts_dir = artifacts_dir
        self._app = falcon.App()

        self._app.add_static_route("/", str(self._artifacts_dir))

        self._server = simple_server.make_server(
            "0.0.0.0",
            port,
            app=self._app,
            handler_class=simple_server.WSGIRequestHandler,
        )

        self._thread = Thread(
            name="Local Repository",
            target=self._server.serve_forever,
            daemon=True,
        )

    def start(self):
        self._thread.start()

    def close(self):
        self._server.shutdown()
        self._thread.join()
