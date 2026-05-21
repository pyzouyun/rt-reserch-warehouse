# RT Research Warehouse Legacy Runtime

This folder contains the Windows 7 SP1 / Windows 10 native packaging work for `v0.2.0-win7-legacy`.

The legacy build does not use Docker. It is designed to bundle native Windows runtimes:

- Python 3.8.10 x64
- PostgreSQL 10.23 x64 binaries
- Orthanc 1.11.3 x64 Windows runtime
- NSSM 2.24
- Prebuilt Web UI static files

The first implementation target is an offline installer created with Inno Setup.

## Important

Runtime binaries are not committed to source control. The packaging script expects them under:

```text
legacy/runtime/
```

See `legacy/vendor/README.md` for the source packages to collect, then unpack or install them into the `legacy/runtime/` layout described in `docs/legacy_windows_build.md`.
