# Local verification quick start

This is a source package, not an installer for a model application. No account, API key, browser or paid inference is needed for local checks.

The packaging replay uses Python 3.12.3, jsonschema 4.10.3, attrs 23.2.0 and pyrsistent 0.20.0. rfc8785 0.1.4 is already vendored. These versions describe this replay, not initial historical test environments. The external dependencies and Python are not redistributed.

Use an existing approved environment with those dependencies, or obtain wheels separately and install offline:

```sh
python3 -m venv /path/to/local-environment
. /path/to/local-environment/bin/activate
python -m pip install --no-index --find-links /path/to/approved-wheels -r requirements-local-checks.txt
```

The two `/path/to/` locations are placeholders chosen by the operator. No installation or download is performed by the package verifier. From the extracted package root:

```sh
python -B tools/verify_package.py
(cd freezes/AD015-TEXTD2-R1-development && python -B -m unittest discover -s tests -p 'test_*.py' -v)
(cd freezes/A05-AD015-TEXTD2-R1-development && python -B -m unittest discover -s tests -p 'test_*.py' -v)
(cd freezes/AD015-TEXTD2-R2-development && python -B -m unittest discover -s tests -p 'test_*.py' -v)
(cd freezes/B046-AD015-TEXTD2-R2-development && python -B -m unittest discover -s tests -p 'test_*.py' -v)
(cd freezes/OP-PREFLIGHT-R2-development && python -B -m unittest discover -s tests -p 'test_*.py' -v)
python -B tools/verify_package.py
```

These suites exercise helpers and contracts using synthetic declared premises. They do not execute an analytical Pass A/B assessment. Do not run the schema builder against an immutable snapshot: it writes generated artifacts. No legacy aggregate command, PDF regression, held-out run or Join is part of this quick start.

The verifier checks the complete listed file set, sizes, SHA-256 values and exact-source map. Hashes detect changes relative to an expected digest; they do not authenticate the publisher or establish independently trusted pins. Obtain the archive digest through an independently trusted channel when authenticating a release.
