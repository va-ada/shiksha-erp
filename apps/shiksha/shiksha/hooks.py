app_name = "shiksha"
app_title = "Shiksha"
app_publisher = "Shiksha ERP"
app_description = "NEP-compliant Indian higher-education layer for ERPNext v16"
app_email = "admin@example.com"
app_license = "GPL-3.0-only"

# Apps this depends on (install order enforced by bench)
required_apps = ["erpnext", "education"]

# Document Events — wire validations without patching upstream apps (Architectural Rule 1)
doc_events = {
	"Program Enrollment": {
		"validate": "shiksha.academics.hooks.stamp_regulation",
	},
	"Course": {
		"validate": "shiksha.academics.hooks.validate_course_credits",
	},
}

# Scheduled jobs
scheduler_events = {
	"daily": [
		"shiksha.finance_ext.dues.send_due_reminders",
		"shiksha.academics.detention.refresh_shortage_alerts",
	],
}

fixtures = [
	{"dt": "Custom Field", "filters": [["module", "=", "Shiksha Academics"]]},
	{"dt": "Workflow", "filters": [["name", "like", "Shiksha%"]]},
]
