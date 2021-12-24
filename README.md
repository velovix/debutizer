# Debutizer

Debutizer is a tool for managing APT packages, targeted at users who need to
manage a suite of potentially interdependent packages and want to do so with
minimal boilerplate and modern continuous integration tooling.

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
