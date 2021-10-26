# Debutizer

Debutizer is a tool for managing APT packages, targeted at users who need to
manage a suite of potentially interdependent packages and want to do so with
minimal boilerplate and modern continuous integration tooling.

## Installation

Naturally, Debutizer is available for installation as an APT repository. If
you're running on a Debian-based distribution, Debutizer can be installed with
the following commands:

```bash
curl -SsL https://raw.githubusercontent.com/velovix/debutizer/main/debutizer.key | apt-key add -
echo "deb http://apt.debutizer.dev $(lsb_release -s -c) main" > /etc/apt/sources.list.d/debutizer.list
apt update
apt install debutizer
```
