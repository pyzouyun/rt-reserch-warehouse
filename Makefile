.PHONY: up down ui etl import-mosaiq pgadmin logs test test-api web-build package-windows legacy-vendor legacy-wheelhouse legacy-runtime legacy-staging package-legacy-windows

up:
	docker compose up -d postgres orthanc

ui:
	docker compose up -d postgres orthanc api web

down:
	docker compose down

etl:
	docker compose --profile etl run --rm etl python -m etl.run_etl

import-mosaiq:
	docker compose --profile etl run --rm etl python -m etl.import_mosaiq_csv /app/data_templates

pgadmin:
	docker compose --profile tools up -d pgadmin

logs:
	docker compose logs -f

test:
	pytest tests -q

test-api:
	$${PYTHON:-python} -m pytest api/tests -q

web-build:
	cd web && npm install && npm run build

package-windows:
	powershell -ExecutionPolicy Bypass -File scripts/windows/build-windows-package.ps1

legacy-vendor:
	powershell -ExecutionPolicy Bypass -File legacy/download-vendor.ps1

legacy-wheelhouse:
	powershell -ExecutionPolicy Bypass -File legacy/download-wheelhouse.ps1

legacy-runtime:
	powershell -ExecutionPolicy Bypass -File legacy/prepare-runtime.ps1

legacy-staging:
	powershell -ExecutionPolicy Bypass -File legacy/build-legacy-package.ps1

package-legacy-windows:
	powershell -ExecutionPolicy Bypass -File legacy/build-installer.ps1
