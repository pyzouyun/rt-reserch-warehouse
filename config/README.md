# Configuration

`orthanc.json` is a password-free reference template. The runnable Docker Compose setup injects Orthanc settings and users from `.env` through environment variables so credentials are not hardcoded in source files.

For production, place secrets in your deployment secret manager and keep this directory free of real credentials.
