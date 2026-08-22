frappe.ui.form.on('Survey Response', {
	template(frm) {
		if (!frm.doc.template) return;
		frappe.call({
			method: 'krushi_vikas.api.get_template_questions',
			args: { template: frm.doc.template },
			callback(r) {
				if (r.message) {
					frm.clear_table('answers');
					r.message.forEach(q => {
						frm.add_child('answers', q);
					});
					frm.refresh_field('answers');
				}
			}
		});
	}
});
