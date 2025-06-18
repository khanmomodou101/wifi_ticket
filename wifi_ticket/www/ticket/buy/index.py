import frappe
from frappe.utils import random_string
from smart_subscription.config import initialize_payment
import random

def get_context(context):
    context.no_cache = True

    
    id = frappe.request.args.get("id")
    settings = frappe.get_doc("Wifi Settings")
    wifi_plans = frappe.get_all("Wifi Plan", {"enabled": 1}, ["*"])
    plan = frappe.get_doc("Wifi Plan", id)
    
    context.plans = wifi_plans
    context.settings = settings
    context.plan = plan
    
    

   

@frappe.whitelist(allow_guest=True)
def buy_ticket():
    try:
        data = frappe.form_dict
        
        ticket = frappe.new_doc("Wifi Ticket")
        reference_id = random_string(40)
        plan_id = data.get("plan")
        
        # Get the plan details from database
        plan = frappe.get_doc("Wifi Plan", plan_id)
        if not plan:
            return {
                "status": "error",
                "message": "Invalid plan selected"
            }
        
        price = plan.price

        # Get a random Raw Code document with status Unused and matching plan
        raw_codes = frappe.get_all("Raw Code", 
            {"profile": plan_id},
            ["name", "password"]
        )
        
        # If no codes found for this specific plan, try to get any unused code
        
        if not raw_codes:
            return {
                "status": "error",
                "message": "No unused WiFi codes available"
            }
        random_code = random.choice(raw_codes)
       
        ticket.phone = data.get("phone")
        ticket.payment_method = "wave"
        ticket.reference_id = reference_id
        ticket.ticket_code = random_code.password
        ticket.plan = plan_id
        
        payment = initialize_payment_for_event(price, reference_id)
        if payment.get("success"):
            ticket.wave_payment_link = payment.get("wave_launch_url")
            ticket.wave_session_id = payment.get("session_id")
            
            # Update Raw Code status to Used
            ticket.insert(ignore_permissions=True)
            frappe.delete_doc("Raw Code", random_code.name)
            
            
            frappe.db.commit()
            return {
                "status": "success",
                "message": "Ticket purchased successfully",
                "ticket_id": ticket.name,
                "wave_payment_link": ticket.wave_payment_link,
                "reference_id": ticket.reference_id
            }
        else:
            frappe.log_error(frappe.get_traceback(), "Error in purchasing ticket")
            return {
                "status": "error",
                "message": "Error in purchasing ticket"
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
        settings = frappe.get_doc("Wifi Settings")
        success_url = f"{settings.success_url}/ticket/buy/success?ref={reference_id}"
        error_url = f"{settings.error_url}/ticket/buy/error?ref={reference_id}"
        response = initialize_payment(amount, reference_id, success_url, error_url)
        return response

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in initializing payment for event")