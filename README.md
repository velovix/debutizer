# Debutizer

Debutizer is a tool for managing APT packages, targeted at users who need to
manage a suite of potentially interdependent packages and want to do so with
minimal boilerplate and modern continuous integration tooling.

_________________

[![Lint Status](https://github.com/velovix/debutizer/workflows/Lint/badge.svg?branch=main)](https://github.com/velovix/debutizer/actions?query=workflow%3ALint)
[![Test Status](https://github.com/velovix/debutizer/workflows/Test/badge.svg?branch=main)](https://github.com/velovix/debutizer/actions?query=workflow%3ATest)
[![Docs Status](https://readthedocs.org/projects/debutizer/badge/?version=latest)](https://debutizer.readthedocs.io/en/latest/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://timothycrosley.github.io/isort/)

_________________

## Installation

### APT Repository (Recommended)

Naturally, Debutizer is available for installation as an APT repository, through
a PPA. If you're running on a Debian-based distribution, Debutizer can be
installed with the following commands:

```bash
sudo add-apt-repository ppa:velovix/debutizer
sudo apt update
sudo apt install debutizer
```

### PyPI

Debutizer is also available on PyPI and can be installed like any other Python
package. This is a good option for non-Debian Linux environments, but you will
need to install Debutizer's system dependencies yourself.

Pipx is the recommended way to install through PyPI, as it gives Debutizer its
own virtual environment to run in.

```
pipx install debutizer
```

You can check if Debutizer's system dependencies are available by running
`debutizer check`.

### From Source

Start by cloning the repository:

```bash
git clone https://github.com/velovix/debutizer
```

Then, assuming you have Python 3.6+ and Pip installed, run the following
command in the directory you cloned into:

```bash
pip3 install --constraint constraints.txt .
```

This will take care of installing Python dependencies through Pip, but system
dependencies will have to be installed manually. Use `debutizer check` to see
which, if any, system dependencies are missing.

## Development

If you find a bug or need a new feature from Debutizer, please feel free to
create an issue! If you're feeling especially generous and would like to send
a pull request, take a look at this section for how to get started.

### Dev Dependencies

Development dependencies can be installed using Pip with the `dev` extra
included. This should be done in a virtualenv.

```bash
pip3 install --constraint constraints.txt ".[dev]"
```

This project uses a `constraints.txt` file to pin dependencies. Since Debutizer
is often run as an APT package that uses distribution-supplied versions of our
Python dependencies, this pinning is mostly done for the benefit of keeping
development environments consistent.

If you need to update the pinned version for a given dependency, you can run
the following commands within your virtualenv.

```bash
pip3 update <dependency>
pip3 freeze --exclude debutizer --exclude python-debian > constraints.txt
```

### Linting

Debutizer makes use of a few linting tools to keep code style consistent and to
reduce bugs. The CI will run these for you and fail if there are issues, but
you may find it convenient to set up the pre-commit hooks as well.

```bash
pre-commit install
```

### Testing

Debutizer uses PyTest for automated testing. Unit tests can be run with the
following command:

```bash
pytest tests/unit
```

Unfortunately, because integration tests build packages with `pbuilder`,
running integration tests requires `sudo`. Using `sudo` with a virtualenv is
a bit tricky, but this unintuitive command will do it:

```bash
sudo $(which python) -m pytest tests
```
