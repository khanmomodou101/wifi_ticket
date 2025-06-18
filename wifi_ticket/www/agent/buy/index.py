import frappe
from frappe.utils import random_string
import random

def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/login"
        return
    frappe.clear_cache()
    
    ticket_id = frappe.request.args.get("id")
    agent_code = frappe.request.args.get("agent_code")
    plan = frappe.get_doc("Wifi Plan", ticket_id)
    context.plan = plan
    context.agent_code = agent_code

@frappe.whitelist(allow_guest=True)
def buy_ticket():
    try:
        data = frappe.form_dict

        agent_code = data.get("agent_code")
        if not frappe.db.exists("Agent", {"code": agent_code}):
            return {
                "status": "error",
                "message": "Invalid agent code. Please check and try again."
            }

        ticket = frappe.new_doc("Wifi Ticket")
        reference_id = random_string(40)
        plan = data.get("plan")

        # Get a single random unused Raw Code
        raw_code = frappe.db.sql("""
            SELECT name, password FROM `tabRaw Code`
            WHERE status='Unused'
            LIMIT 1
        """, as_dict=True)
        if not raw_code:
            return {
                "status": "error",
                "message": "No unused WiFi codes available"
            }
        raw_code = raw_code[0]

        ticket.phone = data.get("phone")
        ticket.payment_method = "cash"
        ticket.reference_id = reference_id
        ticket.ticket_code = raw_code["password"]
        ticket.payment_status = "Paid"
        ticket.agent = frappe.db.get_value("Agent", agent_code, "name")

        # Mark code as used (faster than get_doc + save)
        frappe.db.set_value("Raw Code", raw_code["name"], "status", "Used")

        # Insert ticket
        ticket.insert(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "WiFi code generated successfully",
            "ticket_id": ticket.name,
            "ticket_code": ticket.ticket_code,
            "reference_id": ticket.reference_id
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in generating WiFi code")
        return {
            "status": "error",
            "message": "Error in generating WiFi code"
        }
    

    
@frappe.whitelist(allow_guest=True)
def verify_agent_code(agent_code):
    if frappe.db.exists("Agent", {"code": agent_code}):
        return True
    else:
        return False