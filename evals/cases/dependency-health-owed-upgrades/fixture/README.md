# tripbook

Turns a trip file (YAML) into a printable itinerary with local times and costs in your currency.

    pip install -r requirements.txt
    python -m tripbook render trips/bangkok.yaml > itinerary.html
    python -m tripbook rates EUR

The web preview runs in Docker:

    docker build -t tripbook .
    docker run -p 8000:8000 tripbook

Dependencies: edit `requirements.in`, then `pip-compile requirements.in` to refresh
`requirements.txt`. Tests: `python -m unittest discover tests`.
