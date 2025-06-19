import frappe
import random
import requests
from frappe.utils import random_string




@frappe.whitelist()
def send_sms(phone, code):
    try:
        url = "https://jsms.royalsmb.com/api/method/jsms.africell.send_sms"
        
        # Format phone number
        if phone.startswith("+220"):
            phone = phone[4:]
        elif phone.startswith("220"):
            phone = phone[3:]
            
        message = f"""Thank you for choosing Ceesay Net!

Your WiFi code is: {code}

Please use this code to connect to our WiFi network.
If you have any issues, please contact our support.

Best regards,
Ceesay Net Team"""

        # Log the SMS attempt
        frappe.logger().debug(f"Attempting to send SMS to {phone} with WiFi code")
        
        response = requests.post(url, data={
            "sender_id": "Jokoorsms", 
            "phone_number": phone, 
            "message": message
        })
        
        # Log the response
        frappe.logger().debug(f"SMS API Response: {response.text}")
        
        if response.status_code != 200:
            frappe.log_error(
                f"SMS sending failed for phone {phone}. Status code: {response.status_code}, Response: {response.text}",
                "SMS Sending Error"
            )
            return False
            
        return response.text
        
    except Exception as e:
        frappe.log_error(
            f"Error sending SMS to phone {phone}: {str(e)}\nTraceback: {frappe.get_traceback()}",
            "SMS Sending Error"
        )
        return False


                
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
        ticket.payment_method = "cash"  # Changed to cash since we're not using wave
        ticket.reference_id = reference_id
        ticket.ticket_code = random_code.password
        ticket.payment_status = "Paid"  # Set as paid since we're not using wave
        
        # Update Raw Code status to Used
        raw_code_doc = frappe.get_doc("Raw Code", random_code.name)
        raw_code_doc.status = "Used"
        raw_code_doc.save(ignore_permissions=True)
        
        # Insert ticket
        ticket.insert(ignore_permissions=True)
        frappe.db.commit()
        
        # Send SMS with the code
        if ticket.phone:
            send_sms(ticket.phone, ticket.ticket_code)
        
        return {
            "status": "success",
            "message": "Ticket purchased successfully",
            "ticket_id": ticket.name,
            "reference_id": ticket.reference_id
        }
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in buying ticket")
        return {
            "status": "error",
            "message": "Error in purchasing ticket"
        }

@frappe.whitelist()
def create_agents():
    # List of agents with full names
    agents = [
        "Muhammed Keema",
        "Karamo Njie",
        "Musa",
        "Madi Ceesay",
        "Shiekh Omar",
        "Aminata",
        "Narr",
        "Mama Jah",
        "Fatoumatta Jawara",
        "Seedy Sillah",
        "Abdourahman",
        "Muhammed Boutique",
        "Manjai"
    ]

    # Loop and create users
    for idx, full_name in enumerate(agents):
        # Generate email
        email = f"ag{idx + 1:03}@ceesay.net"
        
        # Split first and last names
        parts = full_name.split()
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        # Check if user already exists
        if frappe.db.exists("User", email):
            frappe.msgprint(f"User {email} already exists")
            continue

        # Create user
        user = frappe.new_doc("User")
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.new_password = email
        user.insert(ignore_permissions=True)
    frappe.db.commit()
    return True