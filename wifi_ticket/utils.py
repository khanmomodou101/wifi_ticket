import frappe

import requests




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


                