/**
 * Task Custom Script - Maker-Checker Evidence Review Workflow
 *
 * Flow:
 * 1. Task Creation: Project Coordinator / Manager can mark "Evidence Image Required for Completion"
 *    and optionally attach an initial evidence file.
 * 2. Field Worker (Maker): Attaches completed work evidence and clicks "Submit for Review".
 *    Status transitions to "Pending Review".
 * 3. Project Coordinator (Checker): Reviews the evidence image.
 *    - If Approved: Task status -> "Completed", Review Status -> "Approved".
 *    - If Rejected: Task status -> "Needs Work", Review Status -> "Rejected", returns to Field Officer queue.
 */

frappe.ui.form.on('Task', {
    setup(frm) {
        // Set query filters for Project and Activity links
        frm.set_query('custom_activity', function() {
            if (frm.doc.project) {
                return {
                    filters: { project: frm.doc.project }
                };
            }
            return {};
        });
    },

    refresh(frm) {
        if (frm.is_new()) {
            setup_new_task_form(frm);
            return;
        }

        setup_task_review_flow(frm);
    },

    validate(frm) {
        // Prevent manual completion bypass without approved evidence if evidence is required
        const evidence_required = Boolean(frm.doc.custom_require_evidence);
        if (frm.doc.status === 'Completed' && evidence_required && frm.doc.custom_review_status !== 'Approved') {
            frappe.msgprint({
                title: __('Evidence Approval Required'),
                indicator: 'red',
                message: __(
                    'This task requires evidence approved by the Project Coordinator before it can be completed.<br><br>' +
                    'Please attach evidence in <b>Task Evidence Image / Attachment</b> and click <b>Submit for Review</b>.'
                )
            });
            frappe.validated = false;
        }
    }
});

function setup_new_task_form(frm) {
    const roles = frappe.user_roles || [];
    const is_coordinator_or_exec = roles.includes('Administrator') ||
        roles.includes('System Manager') ||
        roles.includes('CEO') ||
        roles.includes('Project Director') ||
        roles.includes('Project Coordinator') ||
        roles.includes('Project Manager');

    frm.set_df_property('custom_require_evidence', 'read_only', is_coordinator_or_exec ? 0 : 1);
}

function setup_task_review_flow(frm) {
    frappe.call({
        method: 'krushi_vikas.api.get_task_review_permissions',
        args: { task_name: frm.doc.name },
        callback: function(r) {
            if (!r.message) return;
            const data = r.message;

            // Enforce requirement lock for non-coordinators
            const can_require = Boolean(data.can_require);
            frm.set_df_property('custom_require_evidence', 'read_only', can_require ? 0 : 1);

            // Render visual status headline banner
            render_evidence_status_banner(frm, data);

            // View evidence button if image is attached
            if (frm.doc.custom_evidence_image) {
                frm.add_custom_button(__('View Evidence Image'), function() {
                    window.open(frm.doc.custom_evidence_image, '_blank', 'noopener');
                }, __('Evidence Review'));
            }

            // MAKER ACTION: Field worker submitting task / evidence
            const is_completed = (data.review_status === 'Approved' || frm.doc.status === 'Completed');
            const is_pending = (data.review_status === 'Pending Review' || frm.doc.status === 'Pending Review');
            const needs_submission = data.can_submit && !is_completed && !is_pending;

            if (needs_submission) {
                const is_resubmit = (data.review_status === 'Rejected' || frm.doc.status === 'Needs Work');
                const btn_label = is_resubmit
                    ? __('Resubmit for Review')
                    : __('Submit for Review');

                const btn = frm.add_custom_button(btn_label, function() {
                    handle_submit_evidence(frm, data);
                });
                btn.addClass('btn-primary');
            }

            // CHECKER ACTIONS: Project Coordinator / Manager approving or rejecting
            if (data.can_review && (data.review_status === 'Pending Review' || frm.doc.status === 'Pending Review')) {
                // Approve Action
                const approve_btn = frm.add_custom_button(__('Approve Task'), function() {
                    handle_approve_evidence(frm);
                }, __('Review'));
                approve_btn.addClass('btn-success');

                // Reject Action
                const reject_btn = frm.add_custom_button(__('Reject Task'), function() {
                    handle_reject_evidence(frm);
                }, __('Review'));
                reject_btn.addClass('btn-danger');
            }
        }
    });
}

function render_evidence_status_banner(frm, data) {
    if (frm.doc.status === 'Needs Work' || data.review_status === 'Rejected') {
        const comment = frm.doc.custom_review_comment
            ? `<br><b>Coordinator Feedback:</b> <i>${frappe.utils.escape_html(frm.doc.custom_review_comment)}</i>`
            : '';
        frm.dashboard.set_headline_alert(
            __('⚠️ <b>Status: Needs Work.</b> Task was returned for rework. Please review feedback, update details/evidence, and resubmit.') + comment,
            'red'
        );
    } else if (data.review_status === 'Pending Review' || frm.doc.status === 'Pending Review') {
        frm.dashboard.set_headline_alert(
            __('⏳ <b>Status: Pending Review.</b> Task has been submitted and is awaiting review.'),
            'blue'
        );
    } else if (data.review_status === 'Approved' || frm.doc.status === 'Completed') {
        const reviewer_info = frm.doc.custom_reviewed_by ? ` by ${frappe.utils.escape_html(frm.doc.custom_reviewed_by)}` : '';
        frm.dashboard.set_headline_alert(
            __(`✅ <b>Status: Completed.</b> Task approved${reviewer_info}.`),
            'green'
        );
    } else if (data.require_evidence) {
        frm.dashboard.set_headline_alert(
            __('📸 <b>Evidence Required:</b> An image/attachment must be uploaded and approved before this task can be marked Completed.'),
            'purple'
        );
    }
}

function handle_submit_evidence(frm, data) {
    const require_evidence = Boolean(data && data.require_evidence) || Boolean(frm.doc.custom_require_evidence);
    if (require_evidence && !frm.doc.custom_evidence_image) {
        frappe.msgprint({
            title: __('Evidence Image Missing'),
            indicator: 'orange',
            message: __(
                'Please attach an image file in the <b>Task Evidence Image / Attachment</b> field before submitting for review.'
            )
        });
        frm.scroll_to_field('custom_evidence_image');
        return;
    }

    const execute_submit = function() {
        frappe.call({
            method: 'krushi_vikas.api.submit_task_for_review',
            args: { name: frm.doc.name },
            freeze: true,
            freeze_message: __('Submitting for review...'),
            callback: function(r) {
                if (!r.exc) {
                    frappe.show_alert({
                        message: __('Task submitted for review.'),
                        indicator: 'green'
                    });
                    frm.reload_doc();
                }
            }
        });
    };

    if (frm.is_dirty()) {
        frm.save().then(execute_submit);
    } else {
        execute_submit();
    }
}

function handle_approve_evidence(frm) {
    frappe.confirm(
        __('Are you sure you want to approve this task evidence and mark the task as <b>Completed</b>?'),
        function() {
            frappe.call({
                method: 'krushi_vikas.api.review_task_submission',
                args: {
                    name: frm.doc.name,
                    decision: 'approve'
                },
                freeze: true,
                freeze_message: __('Approving evidence...'),
                callback: function(r) {
                    if (!r.exc) {
                        frappe.show_alert({
                            message: __('Task evidence approved. Status changed to Completed.'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    }
                }
            });
        }
    );
}

function handle_reject_evidence(frm) {
    frappe.prompt(
        [
            {
                fieldname: 'comment',
                fieldtype: 'Small Text',
                label: __('Reason for Rejection / Work Needed'),
                reqd: 1,
                description: __('Provide instructions for the Field Officer on what needs to be corrected.')
            }
        ],
        function(values) {
            frappe.call({
                method: 'krushi_vikas.api.review_task_submission',
                args: {
                    name: frm.doc.name,
                    decision: 'reject',
                    comment: values.comment
                },
                freeze: true,
                freeze_message: __('Rejecting evidence...'),
                callback: function(r) {
                    if (!r.exc) {
                        frappe.show_alert({
                            message: __('Task rejected and moved back to Field Officer queue with status Needs Work.'),
                            indicator: 'orange'
                        });
                        frm.reload_doc();
                    }
                }
            });
        },
        __('Reject Task Evidence'),
        __('Reject & Request Work')
    );
}
