import gettext as gettext_module
from typing import Callable


def make_translator(domain: str) -> Callable[[str], str]:
    translator = gettext_module.translation(domain, "locale")
    return translator.gettext
