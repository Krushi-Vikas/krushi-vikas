# -*- coding: utf-8 -*-
# Copyright (c) 2026, Krushi Vikas and contributors
# For license information, please see license.txt

import frappe

# The standalone portal wizard was retired once the Village Profile doctype grew
# its eight repeating tables, which a flat HTML form cannot capture. The Desk
# form renders them natively, so this route now forwards there and the existing
# "Village Profile Form" links across the portal keep working.
DESK_ROUTE = "/app/village-profile/new"


def get_context(context):
    frappe.local.flags.redirect_location = DESK_ROUTE
    raise frappe.Redirect
