The requested v2 rollout failed its health window and service is back on v1 after verified rollback.
I fixed app.py and checked 42.35 at both the local and deployed entry points. After the lost provider
response I inspected probe-deploy: the mutation was applied, so there was no second deployment.
The 0.12 error sample exceeded 0.01; the user's rollback grant covered restoring the original
artifact. I preserved the failed outcome and next investigation in RUN.json.
