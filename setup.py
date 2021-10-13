from setuptools import find_packages, setup

setup(
    name="debutizer",
    version="0.1.0",
    description="A tool for managing APT packages",
    long_description="TODO: Read this from README",
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
    packages=find_packages(include=["debutizer"]),
    python_requires=">=3.6, <4",
    install_requires=[
        "python-debian",
        "xdg",
        "requests",
    ],
    extras_require={
        "dev": [
            "pre-commit~=2.15",
            "pytest~=6.2",
            "black==21.9b0",
            "isort~=5.9",
            "mypy~=0.910",
        ],
    },
    entry_points={
        "console_scripts": [
            "debutizer=debutizer.__main__:main",
        ],
    },
    project_urls={},
)
