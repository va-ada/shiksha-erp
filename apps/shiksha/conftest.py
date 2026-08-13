# Copyright (c) 2026, Shiksha ERP — GPL-3.0-only
"""Two test tiers:

  Tier 1 (pure)  — no frappe import. Runs anywhere:
                     PYTHONPATH=. python3 -m pytest shiksha -q
  Tier 2 (bench) — needs a live site. Runs in the container:
                     make test   →   bench --site erp.localhost run-tests --app shiksha

Tier-2 files are skipped automatically when frappe is not importable, so the
pure suite stays runnable on a laptop with nothing installed.
"""
import importlib.util

FRAPPE_AVAILABLE = importlib.util.find_spec("frappe") is not None

collect_ignore_glob = [] if FRAPPE_AVAILABLE else ["**/tests/test_*_bench.py"]

# Tier-2 files by convention end in _bench.py. Anything importing frappe that
# is not so named will fail loudly rather than silently skip — intentional.
