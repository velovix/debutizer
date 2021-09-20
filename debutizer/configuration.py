from pathlib import Path
from typing import Dict

import yaml

from .errors import CommandError
from .translate import make_translator

tr = make_translator("general")


class Configuration:
    @staticmethod
    def from_file(path: Path):
        config_text = path.read_text()
        fields = yaml.load(config_text, Loader=yaml.SafeLoader)

        if fields["type"] == GitConfiguration.type:
            return GitConfiguration(fields)
        else:
            error = tr("unknown-type").format(type=fields["type"])
            raise CommandError(error)


class GitConfiguration:
    type = "git"

    def __init__(self, fields: Dict[str, str]):
        self.repository_url = fields["repository_url"]
        self.revision = fields["revision"]
