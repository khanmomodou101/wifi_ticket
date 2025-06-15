import frappe
from frappe.utils import random_string
import random

def get_context(context):
    frappe.clear_cache()
    
    ticket_id = frappe.request.args.get("id")

@frappe.whitelist(allow_guest=True)
def buy_ticket():
    try:
        data = frappe.form_dict
        
        ticket = frappe.new_doc("Wifi Ticket")
        reference_id = random_string(40)
        plan = data.get("plan")
        price = 0
        if plan == "daily":
            price = 1
        elif plan == "weekly":
            price = 150
        elif plan == "monthly":
            price = 350

        # Get a random Raw Code document with status Unused
        raw_codes = frappe.get_all("Raw Code", 
            {"status": "Unused"},
            ["name", "password"]
        )
        if not raw_codes:
            return {
                "status": "error",
                "message": "No unused WiFi codes available"
            }
        random_code = random.choice(raw_codes)
       
        ticket.phone = data.get("phone")
        ticket.payment_method = "cash"
        ticket.reference_id = reference_id
        ticket.ticket_code = random_code.password
        ticket.payment_status = "Paid"
        ticket.agent = frappe.db.get_value("User", frappe.session.user, "full_name")
        
        # Update Raw Code status to Used
        raw_code_doc = frappe.get_doc("Raw Code", random_code.name)
        raw_code_doc.status = "Used"
        raw_code_doc.save(ignore_permissions=True)
        
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