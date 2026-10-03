"""Overdue-task and approval-reminder notifications.

Two things page people here, per the process-flow spec: a task that has
slipped past its due date (escalating up the hierarchy chain the longer it
stays open), and an approval that has sat pending too long. Both land as
Notification Log entries (the bell icon) and a ToDo, and both are also
readable directly for the dashboard's own Notifications card.
"""

import frappe
from frappe.utils import today, getdate, date_diff

OPEN_TASK_STATUSES = ("Open", "Working", "Pending Review")
APPROVAL_REMINDER_AFTER_DAYS = 2


def _project_for_task(task):
    """KV Project doc backing a Task, via its Activity, if any."""
    if not task.custom_activity:
        return None

    project_name = frappe.db.get_value("Activity", task.custom_activity, "project")
    if not project_name:
        return None

    return frappe.db.get_value(
        "KV Project",
        project_name,
        ["name", "project_manager", "project_coordinator", "project_director"],
        as_dict=True,
    )


def _recipients_for_overdue(task, days_overdue, project):
    """Assignee always; escalate up the chain the longer it slips."""
    recipients = set()

    owner = task.custom_activity_owner or task.owner
    if owner:
        recipients.add(owner)

    if not project:
        return recipients

    if days_overdue >= 3:
        for field in ("project_manager", "project_coordinator"):
            if project.get(field):
                recipients.add(project[field])

    if days_overdue >= 7:
        if project.get("project_director"):
            recipients.add(project["project_director"])
        else:
            for u in frappe.get_all(
                "Has Role", filters={"role": "Project Director", "parenttype": "User"},
                fields=["parent as name"],
            ):
                recipients.add(u.name)

    return recipients


def _already_notified_today(for_user, subject):
    return frappe.db.exists(
        "Notification Log",
        {"for_user": for_user, "subject": subject, "creation": [">=", today()]},
    )


def _push(for_user, subject, doctype, name):
    if not for_user or _already_notified_today(for_user, subject):
        return

    frappe.get_doc({
        "doctype": "Notification Log",
        "for_user": for_user,
        "subject": subject,
        "type": "Alert",
        "document_type": doctype,
        "document_name": name,
    }).insert(ignore_permissions=True)

    if not frappe.db.exists(
        "ToDo", {"allocated_to": for_user, "reference_type": doctype,
                 "reference_name": name, "status": "Open"}
    ):
        frappe.get_doc({
            "doctype": "ToDo",
            "allocated_to": for_user,
            "reference_type": doctype,
            "reference_name": name,
            "description": subject,
            "priority": "High",
        }).insert(ignore_permissions=True)

    from krushi_vikas.whatsapp import send_whatsapp

    send_whatsapp(for_user, subject)


def run_daily_checks():
    """Scheduler entry point: overdue tasks + aging approvals."""
    notify_overdue_tasks()
    notify_aging_approvals()


def notify_overdue_tasks():
    tasks = frappe.get_all(
        "Task",
        filters={"status": ["in", OPEN_TASK_STATUSES], "exp_end_date": ["<", today()]},
        fields=["name", "subject", "exp_end_date", "custom_activity",
                "custom_activity_owner", "owner"],
    )

    for t in tasks:
        days_overdue = date_diff(today(), t.exp_end_date)
        project = _project_for_task(t)
        subject = frappe._("Overdue ({0} day(s)): {1}").format(days_overdue, t.subject)

        for user in _recipients_for_overdue(t, days_overdue, project):
            _push(user, subject, "Task", t.name)


def notify_aging_approvals():
    from krushi_vikas.approvals import APPROVABLE, PENDING

    for doctype in APPROVABLE:
        if not frappe.db.table_exists(doctype):
            continue

        rows = frappe.get_all(
            doctype,
            filters={"approval_status": PENDING},
            fields=["name", "pending_approver", "pending_approver_role", "modified", "project_name"],
        )

        for row in rows:
            days_pending = date_diff(today(), getdate(row.modified))
            if days_pending < APPROVAL_REMINDER_AFTER_DAYS:
                continue

            subject = frappe._("Approval pending {0} day(s): {1}").format(
                days_pending, row.project_name or row.name
            )

            recipients = []
            if row.pending_approver:
                recipients = [row.pending_approver]
            elif row.pending_approver_role:
                recipients = [
                    u.name
                    for u in frappe.get_all(
                        "Has Role",
                        filters={"role": row.pending_approver_role, "parenttype": "User"},
                        fields=["parent as name"],
                    )
                ]

            for user in recipients:
                _push(user, subject, doctype, row.name)


def notify_feedback_survey_submitted(doc, method=None):
    """Notify Project Manager and Coordinator via Notification Log, ToDo, and WhatsApp when a Feedback Survey is submitted."""
    if not doc.get("project"):
        return

    proj = frappe.db.get_value(
        "KV Project",
        doc.project,
        ["name", "project_manager", "project_coordinator", "project_director"],
        as_dict=True,
    )
    if not proj:
        return

    village = doc.get("village") or "Village"
    field_officer = doc.get("field_officer") or doc.owner or "Field Officer"
    subject = frappe._("Feedback Survey Submitted: {0} ({1}) by {2}").format(
        village, doc.name, field_officer
    )

    recipients = set()
    for field in ("project_manager", "project_coordinator"):
        if proj.get(field):
            recipients.add(proj[field])

    for user in recipients:
        _push(user, subject, "Feedback Survey", doc.name)


@frappe.whitelist()
def get_notifications(user=None, limit=20):
    """Feed for the dashboard's Notifications card: unread bell items."""
    user = user or frappe.session.user

    rows = frappe.get_all(
        "Notification Log",
        filters={"for_user": user, "read": 0},
        fields=["name", "subject", "document_type", "document_name", "creation"],
        order_by="creation desc",
        limit_page_length=limit,
    )

    return rows


@frappe.whitelist()
def get_overdue_tasks(user=None):
    """Overdue tasks this person owns — for the dashboard's own count."""
    user = user or frappe.session.user

    tasks = frappe.get_all(
        "Task",
        filters={
            "status": ["in", OPEN_TASK_STATUSES],
            "exp_end_date": ["<", today()],
            "custom_activity_owner": user,
        },
        fields=["name", "subject", "exp_end_date", "custom_activity"],
        order_by="exp_end_date asc",
    )

    for t in tasks:
        t["days_overdue"] = date_diff(today(), t["exp_end_date"])

    return tasks
