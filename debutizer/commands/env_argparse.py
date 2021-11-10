import os
from argparse import ArgumentParser

from debutizer.errors import UnexpectedError


class EnvArgumentParser(ArgumentParser):
    """An argument parser that also accepts configuration using environment variables.
    Flags take precedence over environment variables.

    For a flag --my-cool-flag, the environment variable DEBUTIZER_MY_COOL_FLAG will be
    read.
    """

    def add_env_flag(self, *args, **kwargs):
        if len(args) != 1:
            raise UnexpectedError(
                "Environment arguments must have exactly one flag name"
            )

        flag_name = args[0]
        env_var_name = _flag_to_env_var(flag_name)
        env_var_value = os.environ.get(env_var_name)

        if env_var_value is not None:
            # Convert the environment variable as necessary
            if kwargs.get("action") == "store_true":
                default = True
            elif kwargs.get("type") is not None:
                type_callback = kwargs.get("type")
                default = type_callback(env_var_value)
            else:
                default = env_var_value

            kwargs["default"] = default

            # We got a value from the environment variable, so a flag no longer
            # needs to be provided
            kwargs["required"] = False

        self.add_argument(flag_name, **kwargs)


def _flag_to_env_var(flag_name: str) -> str:
    env_var_name = flag_name.strip("-").replace("-", "_").upper()

    return f"DEBUTIZER_{env_var_name}"
