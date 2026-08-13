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
	$(BE) bench get-app --branch version-16 hrms https://github.com/frappe/hrms
	$(BE) bench get-app --branch version-16 india_compliance https://github.com/resilient-tech/india-compliance
	$(BE) bench get-app --branch version-16 education https://github.com/frappe/education
	$(BE) bench --site $(SITE) install-app hrms
	$(BE) bench --site $(SITE) install-app india_compliance
	$(BE) bench --site $(SITE) install-app education
	$(BE) bench install-app shiksha || $(BE) bash -c "cd apps/shiksha && pip install -e ."
	$(BE) bench --site $(SITE) install-app shiksha

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
