# Legacy Vendor Source Packages

Place offline source packages here while preparing the Win7/Win10 installer. These packages are not read directly by the build script. After download and checksum verification, unpack or install them into `legacy/runtime/`.

Expected files:

```text
python-3.8.10-amd64.exe
postgresql-10.23-1-windows-x64-binaries.zip
Orthanc-*.zip, or an unpacked folder containing Orthanc.exe
Orthanc-1.11.3-Release.exe
OrthancInstaller-Win64-*.exe
nssm-2.24.zip
innosetup-6.3.x.exe
```

Notes:

- Do not commit large third-party binaries unless the repository policy explicitly allows it.
- Verify SHA256 checksums and keep a checksum manifest beside the files.
- If Orthanc 1.11.3 x64 is not available or does not run on Win7 SP1, test an older official Windows installer and update `legacy/config/legacy.env.example`.
- The final runtime layout expected by `legacy/build-legacy-package.ps1` is documented in `docs/legacy_windows_build.md`.
