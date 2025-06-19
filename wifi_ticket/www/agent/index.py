import frappe

def get_context(context):
    context.no_cache = True
    
    settings = frappe.get_doc("Wifi Settings")
    wifi_plans = frappe.get_all("Wifi Plan", {"enabled": 1}, ["name", "price", "duration"], order_by="price asc")
    plans = []
    for plan in wifi_plans:
        count = frappe.db.count("Raw Code", {"status": "Unused", "profile": plan.name})
        plans.append({
            "name": plan.name,
            "price": plan.price,
            "duration": plan.duration,
            "count": count
        })
    context.plans = plans
    context.settings = settings