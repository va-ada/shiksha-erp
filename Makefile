COMPOSE := docker compose -f infra/compose.dev.yml --env-file infra/.env
SITE    := erp.localhost
BE      := $(COMPOSE) exec backend

.PHONY: up down logs shell create-site install-apps migrate test backup restore-check

up:
	$(COMPOSE) up -d

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
