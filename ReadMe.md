kaitaiStructCompile.importer [![Unlicensed work](https://raw.githubusercontent.com/unlicense/unlicense.org/master/static/favicon.png)](https://unlicense.org/)
============================
[wheel](https://gitlab.com/kaitaiStructCompile.py/kaitaiStructCompile.importer/-/jobs/artifacts/master/raw/wheels/kaitaiStructCompile-0.CI-py3-none-any.whl?job=build)
[![PyPi Status](https://img.shields.io/pypi/v/kaitaiStructCompile.importer.svg)](https://pypi.python.org/pypi/kaitaiStructCompile.importer)
[![GitLab build status](https://gitlab.com/kaitaiStructCompile.py/kaitaiStructCompile.importer/badges/master/pipeline.svg)](https://gitlab.com/kaitaiStructCompile.py/kaitaiStructCompile.importer/commits/master)
[![Coveralls Coverage](https://img.shields.io/coveralls/KOLANICH/kaitaiStructCompile.importer.svg)](https://coveralls.io/r/KOLANICH/kaitaiStructCompile.importer)
[![GitLab coverage](https://gitlab.com/kaitaiStructCompile.py/kaitaiStructCompile.importer/badges/master/coverage.svg)](https://gitlab.com/kaitaiStructCompile.py/kaitaiStructCompile.importer/commits/master)
[![Libraries.io Status](https://img.shields.io/librariesio/github/KOLANICH/kaitaiStructCompile.importer.svg)](https://libraries.io/github/KOLANICH/kaitaiStructCompile.importer)

This is an importer allowing to import `ksy`s. Seamlessly compiles `ksy`s into python sources. Useful for playing in IPython shell.


Usage
-----

```python
import kaitaiStructCompile.importer
kaitaiStructCompile.importer._importer.searchDirs.append(Path("./dirWithKSYFiles")) # you can add a dir to search for KSY files.
kaitaiStructCompile.importer._importer.flags["readStoresPos"]=True # you can set compiler flags, for more details see the JSON schema
from kaitaiStructCompile.importer.test import Test
Test # kaitaiStructCompile.importer.test.Test
```
