import frappe
from frappe.utils.print_format import download_pdf
from frappe.utils.pdf import get_pdf
from smart_subscription.config import check_payment_status
from wifi_ticket.utils import send_sms

def get_context(context):
    # Clear cache before processing
    context.no_cache = True
    settings = frappe.get_doc("Wifi Settings")
    context.settings = settings
    ticket = None
    
    reference_id = frappe.request.args.get('ref')
    frappe.log_error(reference_id, "reference_id")
    if reference_id:
        try:
            if  frappe.db.exists('Wifi Ticket', {'reference_id': reference_id}):
            
                ticket = frappe.get_doc('Wifi Ticket', {'reference_id': reference_id})
            
            
            # Add logging to debug payment status
                frappe.logger().debug(f"Checking payment status for ticket: {ticket.name}")
                frappe.logger().debug(f"Wave session ID: {ticket.wave_session_id}")
                
                payment_status = check_payment_status(ticket.wave_session_id)
                frappe.logger().debug(f"Payment status response: {payment_status}")

                if payment_status.get("success") and payment_status.get("payment_status").lower() == "succeeded":
                    frappe.logger().debug(f"Setting payment status to Paid for ticket: {ticket.name}")
                    
                    # Update ticket status
                    ticket.db_set('payment_status', 'Paid')
                    frappe.db.commit()
                    
                    frappe.logger().debug("Payment status updated successfully")
                    
                    # Send SMS with WiFi code
                    try:
                        sms_response = send_sms(ticket.phone, ticket.ticket_code, settings.company_name)
                        frappe.logger().debug(f"SMS sending response: {sms_response}")
                    except Exception as e:
                        frappe.log_error(f"Error sending SMS: {str(e)}", "SMS Error")
                else:
                    frappe.log_error(f"Payment not successful. Status: {payment_status.get('payment_status')}")
                    frappe.logger().debug(f"Payment not successful. Status: {payment_status.get('payment_status')}")
        except Exception as e:
            frappe.log_error(f"{frappe.get_traceback()}", "Ticket Processing Error")
            ticket = None
    else:
        ticket = None

    context.ticket = ticket
    context.ticket_code = frappe.db.get_value("Wifi Ticket", {"reference_id": reference_id}, "ticket_code")
    context.reference_id = reference_id
    return context

@frappe.whitelist(allow_guest=True)
def download_ticket(ref):
    ticket = frappe.get_doc('Wifi Ticket', {'reference_id': ref})
    
    # Alternative method - directly use download_pdf with proper filename
    filename = f"ticket_{ref}.pdf"
    
    # Set the download filename before calling download_pdf
    frappe.local.response.filename = filename
    frappe.local.response.headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    
    # This will handle the PDF generation and response
    return download_pdf('Wifi Ticket', ticket.name)