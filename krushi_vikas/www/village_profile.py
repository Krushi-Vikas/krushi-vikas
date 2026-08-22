# -*- coding: utf-8 -*-
# Copyright (c) 2026, Krushi Vikas and contributors
# For license information, please see license.txt

import frappe
from krushi_vikas.api import get_village_profile_options

def get_context(context):
    context.no_cache = 1
    context.show_sidebar = False
    context.options = get_village_profile_options()
    context.today_date = frappe.utils.today()
    return context
