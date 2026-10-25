"""Runs jobs/nightly.yaml through the router. `python scheduler.py` runs them all now."""
import os

import app

HERE = os.path.dirname(os.path.abspath(__file__))


def load_jobs(path=os.path.join(HERE, "jobs", "nightly.yaml")):
    jobs, job = [], None
    for raw in open(path):
        line = raw.strip()
        if line.startswith("- name:"):
            job = {"name": line.split(":", 1)[1].strip()}
            jobs.append(job)
        elif job is not None and ":" in line and not line.startswith("#"):
            key, value = line.split(":", 1)
            job[key.strip()] = value.strip()
    return jobs


def run_all():
    results = []
    for job in load_jobs():
        status, _ = app.dispatch(job["url"])
        results.append((job["name"], status))
    return results


if __name__ == "__main__":
    for name, status in run_all():
        print(name, status)
