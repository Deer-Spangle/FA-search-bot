import tomlkit

with open('./pyproject.toml') as pyproject:
    file_contents = pyproject.read()

__VERSION__ = tomlkit.parse(file_contents)['tool']['poetry']['version']
