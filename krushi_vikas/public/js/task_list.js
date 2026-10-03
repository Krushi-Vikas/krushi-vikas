/**
 * Task List View Settings
 *
 * Configures status indicators and column additions for the standard Task list view.
 */

frappe.listview_settings['Task'] = {
    add_fields: [
        'status',
        'custom_review_status',
        'custom_require_evidence',
        'custom_evidence_image',
        'custom_assignee',
        'custom_assigned_to',
        'custom_activity_owner'
    ],

    get_indicator(doc) {
        if (doc.status === 'Completed') {
            return [__('Completed'), 'green', 'status,=,Completed'];
        } else if (doc.status === 'Pending Review' || doc.custom_review_status === 'Pending Review') {
            return [__('Pending Review'), 'orange', 'status,=,Pending Review'];
        } else if (doc.status === 'Needs Work' || doc.custom_review_status === 'Rejected') {
            return [__('Needs Work'), 'red', 'status,=,Needs Work'];
        } else if (doc.status === 'Working') {
            return [__('Working'), 'blue', 'status,=,Working'];
        } else if (doc.status === 'Open') {
            return [__('Open'), 'cyan', 'status,=,Open'];
        } else if (doc.status === 'Overdue') {
            return [__('Overdue'), 'red', 'status,=,Overdue'];
        } else if (doc.status === 'Cancelled') {
            return [__('Cancelled'), 'grey', 'status,=,Cancelled'];
        }
    }
};
