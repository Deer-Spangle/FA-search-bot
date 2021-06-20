from pathlib import Path

import tomlkit

toml_path = Path(__file__).parent.parent / "pyproject.toml"
with open(toml_path) as pyproject:
    file_contents = pyproject.read()

__VERSION__ = tomlkit.parse(file_contents)['tool']['poetry']['version']
