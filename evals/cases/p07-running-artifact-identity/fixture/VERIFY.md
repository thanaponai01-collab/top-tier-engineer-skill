## Service identity
- path: app.py, doctor.py, config.json
- test: `python -c "print('identity check follows doctor')"`
- oracle: app.py, config.json
- fail-signal: running artifact identity mismatch
- fail-proof: old process was healthy but carried a different source/config identity

## Run
- doctor: `python doctor.py`
- blind spots: The basic health response does not identify source or runtime contract.
