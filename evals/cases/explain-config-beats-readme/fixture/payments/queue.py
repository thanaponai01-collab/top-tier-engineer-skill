_jobs = []


def put(job):
    _jobs.append(job)


def get():
    return _jobs.pop(0)
