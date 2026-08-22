import frappe

def run():
    frappe.session.user = "Administrator"
    
    # Check what modules user has access to
    user = frappe.get_user()
    user.build_permissions()
    print("Allowed modules count:", len(user.allow_modules))
    print("Krushi Vikas in allowed_modules:", "Krushi Vikas" in user.allow_modules)
    
    # Check Module Def for Krushi Vikas
    module_exists = frappe.db.exists("Module Def", "Krushi Vikas")
    print("Module Def exists:", module_exists)
    
    if not module_exists:
        # Create the Module Def
        module = frappe.new_doc("Module Def")
        module.module_name = "Krushi Vikas"
        module.app_name = "krushi_vikas"
        module.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Created Module Def: Krushi Vikas")
    else:
        mod = frappe.get_doc("Module Def", "Krushi Vikas")
        print(f"Module Def app_name: {mod.app_name}")
    
    # Now enable this module for Administrator user
    user_doc = frappe.get_doc("User", "Administrator")
    # Check if already in block list
    blocked = [b.module for b in user_doc.block_modules]
    print("Blocked modules:", blocked)
    
    # Remove Krushi Vikas from blocked if it's there
    user_doc.block_modules = [b for b in user_doc.block_modules if b.module != "Krushi Vikas"]
    user_doc.save(ignore_permissions=True)
    frappe.db.commit()
    
    # Clear user cache
    frappe.cache.delete_value("user_allowed_modules", user=frappe.session.user)
    frappe.cache.delete_value("user_perm_can_read", user=frappe.session.user)
    
    print("Done - cleared user module cache")
