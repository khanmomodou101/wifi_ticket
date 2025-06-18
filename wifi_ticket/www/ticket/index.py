import frappe

def get_context(context):
    context.no_cache = True
    settings = frappe.get_doc("Wifi Settings")
    wifi_plans = frappe.get_all("Wifi Plan", {"enabled": 1}, ["*"])
    context.plans = wifi_plans
    context.settings = settings
    