frappe.ui.form.on('KV Project', {
    onload(frm) {
        frm.set_query('theme', 'activities', () => ({ filters: { is_group: 1 } }));
        frm.set_query('sub_theme', 'activities', (doc, cdt, cdn) => {
            const row = locals[cdt][cdn];
            return { filters: { is_group: 0, parent_project_theme: row.theme || '' } };
        });
    },
    refresh(frm) {
        frm.trigger('calc_remaining');
        frm.trigger('render_theme_chips');
        if (frm.is_new()) {
            frm.add_custom_button(__('Use Template'), () => {
                frappe.db.get_list('KV Project Template', { fields: ['name'], limit_page_length: 0 }).then((templates) => {
                    if (!templates.length) {
                        return frappe.msgprint(__('No project templates have been created yet.'));
                    }
                    const d = new frappe.ui.Dialog({
                        title: __('Create Project from Template'),
                        fields: [
                            { fieldname: 'template', fieldtype: 'Link', options: 'KV Project Template', label: __('Template'), reqd: 1 },
                            { fieldname: 'project_name', fieldtype: 'Data', label: __('New Project Name'), reqd: 1 },
                            { fieldname: 'start_date', fieldtype: 'Date', label: __('Start Date'), default: frappe.datetime.get_today(), reqd: 1 },
                            { fieldname: 'project_coordinator', fieldtype: 'Link', options: 'User', label: __('Project Coordinator') },
                            { fieldname: 'project_manager', fieldtype: 'Link', options: 'User', label: __('Project Manager') },
                            { fieldname: 'project_director', fieldtype: 'Link', options: 'User', label: __('Project Director') }
                        ],
                        primary_action_label: __('Create'),
                        primary_action: (values) => {
                            frappe.call({
                                method: 'krushi_vikas.krushi_vikas.doctype.kv_project_template.kv_project_template.create_project_from_template',
                                args: values,
                                freeze: true,
                                freeze_message: __('Building project from template...'),
                                callback: (r) => {
                                    if (r.message) {
                                        d.hide();
                                        frappe.set_route('Form', 'KV Project', r.message);
                                    }
                                }
                            });
                        }
                    });
                    d.show();
                });
            });
        }
        if (!frm.is_new()) {
            frm.fields_dict.activities.grid.add_custom_button(__('New Task'), () => {
                const rows = frm.fields_dict.activities.grid.get_selected_children();
                if (!rows.length) return frappe.msgprint(__('Select an activity row first.'));
                const row = rows[0];
                if (!row.linked_activity) return frappe.msgprint(__('Save the project first.'));
                frappe.new_doc('Task', {
                    custom_activity: row.linked_activity,
                    custom_activity_owner: row.assignee,
                    status: 'Open'
                });
            });
            if (frm.doc.linked_baseline_survey) {
                frm.add_custom_button(__('Baseline Survey'), function() {
                    frappe.set_route('Form', 'Baseline Survey', frm.doc.linked_baseline_survey);
                }, __('Linked Forms'));
            }
            if (frm.doc.linked_field_tracking_form) {
                frm.add_custom_button(__('Field Tracking Form'), function() {
                    frappe.set_route('Form', 'Feedback Survey', frm.doc.linked_field_tracking_form);
                }, __('Linked Forms'));
            }
        }
    },
    budget(frm) {
        frm.trigger('calc_remaining');
    },
    actual_amount_spent(frm) {
        frm.trigger('calc_remaining');
    },
    calc_remaining(frm) {
        let b = flt(frm.doc.budget || 0);
        let s = flt(frm.doc.actual_amount_spent || 0);
        frm.set_value('remaining_funds', b - s);
    },
    render_theme_chips(frm) {
        const field = frm.get_field('themes_covered');
        if (!field || !field.$wrapper) return;

        const themes = (frm.doc.themes_covered || '').split(',').map((t) => t.trim()).filter(Boolean);
        let $chips = field.$wrapper.find('.kv-theme-chip-row');

        if (!$chips.length) {
            $chips = $('<div class="kv-theme-chip-row" style="margin-top:6px;display:flex;flex-wrap:wrap;gap:6px;"></div>');
            field.$wrapper.find('.control-value, .control-input-wrapper').first().after($chips);
        }

        $chips.empty();

        if (!themes.length) {
            $chips.append('<span style="font-size:11px;color:var(--text-muted);">Add Activities below to see themes appear here</span>');
            return;
        }

        themes.forEach((t) => {
            $chips.append(
                `<span style="padding:3px 10px;border-radius:999px;background:var(--control-bg);font-size:11px;font-weight:600;">${frappe.utils.escape_html(t)}</span>`
            );
        });
    }
});

frappe.ui.form.on('KV Project Activity', {
    theme(frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, 'sub_theme', '');
    }
});
