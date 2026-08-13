COMPOSE := docker compose -f infra/compose.dev.yml --env-file infra/.env
SITE    := erp.localhost
BE      := $(COMPOSE) exec backend

.PHONY: up down logs shell configure create-site install-apps migrate test backup restore-check

up: ; $(COMPOSE) up -d
	@$(MAKE) configure

## Point bench at the containerised DB/Redis. Idempotent; required before new-site.
## (frappe_docker normally does this via a `configurator` service; we inline it.)
configure:
	$(BE) bash -c '\
		bench set-config -g db_host db && \
		bench set-config -gp db_port 3306 && \
		bench set-config -g redis_cache "redis://redis-cache:6379" && \
		bench set-config -g redis_queue "redis://redis-queue:6379" && \
		bench set-config -g redis_socketio "redis://redis-queue:6379" && \
		bench set-config -gp socketio_port 9000'

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100 backend

shell:
	$(BE) bash

## Phase 0.6–0.7 — one-time site creation + app installs
create-site:
	$(BE) bench new-site $(SITE) \
		--mariadb-root-password $$(grep DB_ROOT_PASSWORD infra/.env | cut -d= -f2) \
		--admin-password $$(grep ADMIN_PASSWORD infra/.env | cut -d= -f2) \
		--mariadb-user-host-login-scope=%
	$(BE) bench --site $(SITE) install-app erpnext

# ⚠️ KNOWN LIMITATION (Phase 0): apps fetched by `bench get-app` live inside the
# container's /apps, which is NOT a volume — they vanish if the container is
# recreated. Acceptable for dev. For production, bake all apps into a custom
# image via frappe_docker's layered build (`apps.json` + `build/custom`).
# Tracked as Phase 13.4 work.
install-apps:
	# shiksha is a volume mount, not a get-app clone — install it into the venv first,
	# otherwise `bench build` dies on ModuleNotFoundError while building OTHER apps.
	$(BE) bash -c "cd /home/frappe/frappe-bench && ./env/bin/pip install -q -e apps/shiksha"
	-$(BE) bench get-app --branch version-16 hrms https://github.com/frappe/hrms
	-$(BE) bench get-app --branch version-16 india_compliance https://github.com/resilient-tech/india-compliance
	-$(BE) bench get-app --branch version-16 education https://github.com/frappe/education
	# get-app's own pip step can silently no-op; ensure every app is importable
	$(BE) bash -c 'cd /home/frappe/frappe-bench && for a in hrms india_compliance education shiksha; do \
		./env/bin/python -c "import $$a" 2>/dev/null || ./env/bin/pip install -q -e apps/$$a; done'
	$(BE) bench --site $(SITE) install-app hrms
	$(BE) bench --site $(SITE) install-app india_compliance
	$(BE) bench --site $(SITE) install-app education
	$(BE) bench --site $(SITE) install-app shiksha
	@$(MAKE) restart

## Workers hold a stale sys.path after new apps land (HTTP 500), and nginx holds a
## stale upstream after the backend restarts (HTTP 502). Both must bounce, in order.
restart:
	$(COMPOSE) restart backend websocket scheduler queue-short queue-long
	@sleep 15
	$(COMPOSE) restart frontend
	@sleep 8
	@curl -s -o /dev/null -w "site: HTTP %{http_code}\n" -H "Host: $(SITE)" http://localhost:$${HTTP_PORT:-8080}/login

## Checkpoint verification
smoke:
	$(BE) bench --site $(SITE) execute shiksha.academics.smoke.run

pure-tests:
	cd apps/shiksha && PYTHONPATH=. python3 -m pytest shiksha -q

verify: pure-tests smoke

migrate:
	$(BE) bench --site $(SITE) migrate

test:
	$(BE) bench --site $(SITE) run-tests --app shiksha

backup:
	$(BE) bench --site $(SITE) backup --with-files

## Architectural Rule 1 guard — upstream apps must be pristine
upstream-pristine:
	$(BE) bash -c "cd apps/education && git diff --quiet" && echo "education: pristine"
	$(BE) bash -c "cd apps/erpnext && git diff --quiet" && echo "erpnext: pristine"
