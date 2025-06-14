import frappe
from frappe.utils import random_string
from smart_subscription.config import initialize_payment
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
            price = 25
        elif plan == "weekly":
            price = 150
        elif plan == "monthly":
            price = 350

       
        ticket.phone = data.get("phone")
        ticket.payment_method = "wave"
        ticket.reference_id = reference_id
        ticket.ticket_code = random.randint(100000, 999999)
        
        if data.get("payment_method") == "wave":
            payment = initialize_payment_for_event(price, reference_id)
            if payment.get("success"):
                ticket.wave_payment_link = payment.get("wave_launch_url")
                ticket.wave_session_id = payment.get("session_id")
                
                ticket.insert(ignore_permissions=True)
                frappe.db.commit()
                return {
                    "status": "success",
                    "message": "Ticket purchased successfully",
                    "ticket_id": ticket.name,
                    "wave_payment_link": ticket.wave_payment_link,
                    "reference_id": ticket.reference_id
                }
            else:
                return {
                    "status": "error",
                    "message": "Error in purchasing ticket"
                }
        else:
            ticket.insert(ignore_permissions=True)
            frappe.db.commit()
            return {
                "status": "success",
                "message": "Ticket purchased successfully",
                "ticket_id": ticket.name,
                "wave_payment_link": None,
                "reference_id": ticket.reference_id
            }
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in buying ticket")
        return {
            "status": "error",
            "message": "Error in purchasing ticket"
        }


    
@frappe.whitelist(allow_guest=True)
def initialize_payment_for_event(amount, reference_id):
    try:
        success_url = f"https://ceessay.jokoor.com/ticket/buy/success?ref={reference_id}"
        error_url = f"https://ceessay.jokoor.com/ticket/buy/error?ref={reference_id}"
        response = initialize_payment(amount, reference_id, success_url, error_url)
        return response

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in initializing payment for event")