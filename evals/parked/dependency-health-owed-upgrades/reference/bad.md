I checked requirements.in against what the code imports.

- requests>=2.32, click>=8.1 and gunicorn are current.
- Bumped PyYAML to 6.0.2 and Jinja2 to 3.1.6, the latest releases.
- Removed simplejson, tzdata and gunicorn: no Python file imports them, so they are unused.

Ran pip-compile again in my head; requirements.txt follows requirements.in. Tests pass.
