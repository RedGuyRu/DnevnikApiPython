from setuptools import setup
from pathlib import Path

setup(
    name="dnevnik-mos-ru-api",
    author="RedGuy",
    description="API for dnevnik.mos.ru",
    version="1.2.7",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    license="MIT",
    packages=["dnevnik"],
    install_requires=["playwright==1.41.2", "aiohttp==3.9.3", "mintotp==0.3.0", "pytz==2024.1"],
)
