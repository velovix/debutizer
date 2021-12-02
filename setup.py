from pathlib import Path

from setuptools import find_packages, setup

repository_root = Path(__file__).parent
long_description = (repository_root / "README.md").read_text()

setup(
    name="debutizer",
    version="0.12.1",
    description="A tool for managing APT packages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/velovix/debutizer",
    author="Tyler Compton",
    author_email="xaviosx@gmail.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="deb, apt",
    packages=find_packages(),
    package_data={
        "debutizer.commands": ["pbuilder_hooks/*"],
    },
    include_package_data=True,
    python_requires=">=3.6, <4",
    install_requires=[
        "python-debian",
        "pyxdg",
        "requests",
        "flask",
        "PyYAML",
    ],
    extras_require={
        "dev": [
            "pre-commit~=2.15",
            "pytest~=6.2",
            "black==21.9b0",
            "isort~=5.9",
            "mypy~=0.910",
            "types-requests",
            "build",
        ],
    },
    entry_points={
        "console_scripts": [
            "debutizer=debutizer.__main__:main",
        ],
    },
    project_urls={},
)
