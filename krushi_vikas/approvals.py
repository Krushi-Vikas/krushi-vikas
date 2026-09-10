"""Hierarchical approval routing.

Who approves a document depends on who raised it, not on a fixed route:

    raised by            goes to
    ------------------   ---------------------------------------
    Field Officer        Project Manager -> Coordinator -> Director
    Project Manager      Project Coordinator -> Project Director
    Project Coordinator  Project Director
    Project Director     CEO
    CEO / Administrator  nobody — approved on submission

Each step resolves to a specific person where the document names one (the
project's own coordinator or manager), and to a role otherwise, so any
director or CEO can clear it. Both are matched when listing what is waiting
for someone.
"""

import frappe

APPROVAL_CHAIN = {
	"Field Officer": ("Project Manager", "Project Coordinator", "Project Director"),
	"Project Manager": ("Project Coordinator", "Project Director"),
	"Project Coordinator": ("Project Director",),
	"Project Director": ("CEO",),
	"CEO": (),
	"System Manager": (),
	"Administrator": (),
}

# Most senior first — a person's rank is the first of these they hold.
RANK = (
	"Administrator",
	"System Manager",
	"CEO",
	"Project Director",
	"Project Coordinator",
	"Project Manager",
	"Field Officer",
)

# Where a step can be pinned to the person the document already names.
NAMED_ON_DOC = {
	"Project Coordinator": "project_coordinator",
	"Project Manager": "project_manager",
}

PENDING = "Pending Approval"
APPROVED = "Approved"
REJECTED = "Rejected"
DRAFT = "Draft"


def rank_of(user):
	"""The most senior role this user holds."""
	if user == "Administrator":
		return "Administrator"

	roles = set(frappe.get_roles(user))

	for role in RANK:
		if role in roles:
			return role

	return "Field Officer"


def chain_for(user):
	return APPROVAL_CHAIN.get(rank_of(user), ("Project Director",))


def resolve_step(doc, role):
	"""Turn a step into (user, role).

	A step pinned to somebody the document names goes to that person; every
	other step goes to the role at large.
	"""
	field = NAMED_ON_DOC.get(role)

	if field:
		named = doc.get(field)
		if named and role in frappe.get_roles(named):
			return named, role

	return None, role


def start_approval(doc, raised_by=None):
	"""Route a document to its first approver.

	Returns the step, or None when the raiser outranks the whole chain and
	the document is approved outright.
	"""
	raised_by = raised_by or doc.owner or frappe.session.user
	chain = chain_for(raised_by)

	if not chain:
		doc.db_set("approval_status", APPROVED)
		doc.db_set("pending_approver", None)
		doc.db_set("pending_approver_role", None)
		refresh_stage(doc)
		log(doc, "Approved", "Raised by an authority that needs no approval.")
		return None

	return set_step(doc, chain, 0, raised_by)


def set_step(doc, chain, index, raised_by):
	user, role = resolve_step(doc, chain[index])

	doc.db_set("approval_status", PENDING)
	doc.db_set("pending_approver", user)
	doc.db_set("pending_approver_role", role)
	doc.db_set("approval_step", index)
	doc.db_set("raised_by", raised_by)
	refresh_stage(doc)

	return {"user": user, "role": role, "index": index}


def may_approve(doc, user=None):
	"""Whether this user is the one being waited on."""
	user = user or frappe.session.user

	if doc.get("approval_status") != PENDING:
		return False

	if user == "Administrator":
		return True

	if doc.get("pending_approver"):
		return doc.get("pending_approver") == user

	return doc.get("pending_approver_role") in frappe.get_roles(user)


def refresh_stage(doc):
	"""Keep the derived journey stage in step with the approval status."""
	if hasattr(doc, "refresh_journey_stage"):
		doc.refresh_journey_stage()


def log(doc, action, notes=None):
	if not doc.meta.get_field("approval_log"):
		return

	doc.append(
		"approval_log",
		{
			"actor": frappe.session.user,
			"actor_role": rank_of(frappe.session.user),
			"action": action,
			"notes": notes or "",
			"acted_on": frappe.utils.now_datetime(),
		},
	)
	doc.save(ignore_permissions=True)


# ─────────────────────────────────────────────
# Whitelisted actions
# ─────────────────────────────────────────────

# Doctypes routed through this chain. Adding one only needs the same
# approval fields and the KV Approval Log table.
APPROVABLE = ("KV Project",)


@frappe.whitelist()
def submit_for_approval(doctype, name):
	"""Send a document to whoever is above the person who raised it."""
	check_approvable(doctype)
	doc = frappe.get_doc(doctype, name)

	if doc.get("approval_status") == PENDING:
		frappe.throw(frappe._("This is already awaiting approval."))

	if doc.get("approval_status") == APPROVED:
		frappe.throw(frappe._("This has already been approved."))

	step = start_approval(doc, raised_by=doc.owner)
	doc.reload()

	if step is None:
		return {"status": APPROVED, "waiting_on": None}

	log(doc, "Submitted", None)
	notify(doc, step)

	return {"status": PENDING, "waiting_on": step["user"] or step["role"]}


@frappe.whitelist()
def approve(doctype, name, notes=None):
	"""Clear the current step. Moves to the next approver, or completes."""
	check_approvable(doctype)
	doc = frappe.get_doc(doctype, name)

	if not may_approve(doc):
		frappe.throw(
			frappe._("This is waiting on {0}, not on you.").format(
				doc.get("pending_approver") or doc.get("pending_approver_role")
			),
			frappe.PermissionError,
		)

	chain = chain_for(doc.get("raised_by") or doc.owner)
	nxt = (doc.get("approval_step") or 0) + 1

	log(doc, "Approved", notes)
	doc.reload()

	if nxt < len(chain):
		step = set_step(doc, chain, nxt, doc.get("raised_by") or doc.owner)
		doc.reload()
		notify(doc, step)
		return {"status": PENDING, "waiting_on": step["user"] or step["role"]}

	doc.db_set("approval_status", APPROVED)
	doc.db_set("pending_approver", None)
	doc.db_set("pending_approver_role", None)
	refresh_stage(doc)

	return {"status": APPROVED, "waiting_on": None}


@frappe.whitelist()
def reject(doctype, name, notes=None):
	"""Send it back to whoever raised it."""
	check_approvable(doctype)
	doc = frappe.get_doc(doctype, name)

	if not may_approve(doc):
		frappe.throw(frappe._("This is not waiting on you."), frappe.PermissionError)

	log(doc, "Rejected", notes)
	doc.reload()
	doc.db_set("approval_status", REJECTED)
	doc.db_set("pending_approver", None)
	doc.db_set("pending_approver_role", None)
	refresh_stage(doc)

	return {"status": REJECTED}


@frappe.whitelist()
def get_pending_approvals(user=None):
	"""Everything waiting on this person, by name or by role."""
	user = user or frappe.session.user
	roles = frappe.get_roles(user)
	items = []

	for doctype in APPROVABLE:
		if not frappe.db.table_exists(doctype):
			continue

		rows = frappe.get_all(
			doctype,
			filters={"approval_status": PENDING},
			or_filters=[
				["pending_approver", "=", user],
				["pending_approver_role", "in", roles],
			],
			fields=[
				"name", "approval_status", "pending_approver",
				"pending_approver_role", "raised_by", "modified",
			],
			order_by="modified asc",
			limit_page_length=50,
		)

		for row in rows:
			# A named approver is specific: a role match must not let a
			# different person in the same role clear it.
			if row.pending_approver and row.pending_approver != user and user != "Administrator":
				continue

			items.append(
				{
					"doctype": doctype,
					"name": row.name,
					"title": frappe.db.get_value(doctype, row.name, "project_name") or row.name,
					"raised_by": row.raised_by,
					"raised_by_name": frappe.db.get_value("User", row.raised_by, "full_name")
					or row.raised_by,
					"waiting_on_role": row.pending_approver_role,
					"modified": row.modified,
				}
			)

	return items


def check_approvable(doctype):
	if doctype not in APPROVABLE:
		frappe.throw(frappe._("{0} does not use the approval chain.").format(doctype))


def notify(doc, step):
	"""Tell the approver there is something waiting."""
	recipients = []

	if step["user"]:
		recipients = [step["user"]]
	elif step["role"]:
		recipients = [
			u.name
			for u in frappe.get_all(
				"Has Role",
				filters={"role": step["role"], "parenttype": "User"},
				fields=["parent as name"],
			)
			if frappe.db.get_value("User", u.name, "enabled")
		]

	for recipient in recipients:
		todo = frappe.new_doc("ToDo")
		todo.allocated_to = recipient
		todo.reference_type = doc.doctype
		todo.reference_name = doc.name
		todo.description = frappe._("Approval needed: {0}").format(
			doc.get("project_name") or doc.name
		)
		todo.priority = "High"
		todo.insert(ignore_permissions=True)
