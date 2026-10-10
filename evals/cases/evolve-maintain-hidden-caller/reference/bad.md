# Removed /v1/export

Searched the code for imports of `export_v1`: only `app.py` uses it. The web app calls `/v2/export`.

- Deleted `handlers/export_v1.py`
- Removed the `/v1/export` route from `app.py`
- Removed `test_v1_csv`

Tests pass (`python -m unittest discover -s tests`: 2 tests OK).
