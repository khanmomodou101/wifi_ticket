import frappe
import requests
import json
import base64
import uuid
from datetime import datetime
from frappe import _

config = frappe.get_site_config()
WAVE_API_KEY = config.get("wave", {}).get("api_key")

@frappe.whitelist()
def initialize_payment(amount, reference_id, success_url, error_url):
    try:
        # Fetch the Wave API key from configuration
        api_key = WAVE_API_KEY
        if not api_key:
            frappe.log_error("Wave API Key not configured", "Wave Payment Error")
            return {"success": False, "message": "Wave API Key not configured"}

        

        # Prepare the success and error redirect URLs
        

        # Generate a unique client reference for this transaction
        
        # Store the client reference for future verification
       

        # Prepare the request payload for Wave Checkout API
        checkout_data = {
            "amount": amount,
            "currency": "GMD",
            "error_url": error_url,
            "success_url": success_url,
            "client_reference": reference_id,

        }

        # Add optional phone number restriction if provided
        
        # Make API call to Wave to create checkout session
        url = "https://api.wave.com/v1/checkout/sessions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=checkout_data, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and response_data.get("id"):
            session_id = response_data["id"]
            wave_launch_url = response_data.get("wave_launch_url")

            # Store session info for status check
            frappe.cache().set_value(
                f"wave_session_{session_id}",
                {
                    "client_reference": reference_id,
                    "amount": amount,
                    "status": "open",
                    "created_at": frappe.utils.now(),
                },
                expires_in_sec=3600,
            )

            return {
                "success": True,
                "session_id": session_id,
                "wave_launch_url": wave_launch_url,
                "client_reference": reference_id,
                
            }
        else:
            error_msg = response_data
            frappe.log_error(
                frappe.get_traceback(),
                "Wave Checkout Session Creation Failed",
            )
            return {"success": False, "message": error_msg}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Wave Payment Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def check_payment_status(session_id):
    try:
        # Fetch the Wave API key from configuration
        api_key = WAVE_API_KEY
        if not api_key:
            frappe.log_error("Wave API Key not configured", "Wave Payment Status Error")
            return {"success": False, "message": "Wave API Key not configured"}

        # Make API call to check the status of the checkout session
        url = f"https://api.wave.com/v1/checkout/sessions/{session_id}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        response = requests.get(url, headers=headers)
        response_data = response.json()

        if response.status_code == 200:
            # Extract important details from response
            checkout_status = response_data.get("checkout_status")
            payment_status = response_data.get("payment_status")
            transaction_id = response_data.get("transaction_id")
            client_reference = response_data.get("client_reference")

            # Update the session cache with the latest status
            session_cache_key = f"wave_session_{session_id}"
            session_cache = frappe.cache().get_value(session_cache_key) or {}
            session_cache.update(
                {
                    "status": checkout_status,
                    "payment_status": payment_status,
                    "transaction_id": transaction_id,
                    "last_checked": frappe.utils.now(),
                }
            )
            frappe.cache().set_value(
                session_cache_key, session_cache, expires_in_sec=3600
            )

            # Map Wave status to our app's status format
            status_mapping = {
                "complete": {
                    "succeeded": "SUCCEEDED",
                    "processing": "IN_PROGRESS",
                    "cancelled": "FAILED",
                },
                "open": "IN_PROGRESS",
                "expired": "FAILED",
            }

            if checkout_status == "complete":
                status = status_mapping["complete"].get(payment_status, "FAILED")
            else:
                status = status_mapping.get(checkout_status, "FAILED")

            return {
                "success": True,
                "status": status,
                "checkout_status": checkout_status,
                "payment_status": payment_status,
                "transaction_id": transaction_id,
                "client_reference": client_reference,
            }
        else:
            error_msg = response_data.get("error", {}).get("message", "Unknown error")
            frappe.log_error(
                f"Wave Status Check Error: {json.dumps(response_data)}",
                "Wave Checkout Status Check Failed",
            )
            return {"success": False, "status": "FAILED", "message": error_msg}

    except Exception as e:
        frappe.log_error(
            f"Wave Payment Status Check Error: {str(e)}", "Wave Payment Status Error"
        )
        return {"success": False, "status": "FAILED", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def payment_success():
    """Handle success redirects from Wave payment"""
    try:
        # Get checkout session ID from request
        session_id = frappe.request.args.get("id")
        if not session_id:
            frappe.local.response["type"] = "redirect"
            frappe.local.response["location"] = (
                "/payment-error?reason=missing-session-id"
            )
            return

        # Verify the payment status with Wave
        payment_status = check_payment_status(session_id)

        if (
            payment_status.get("success")
            and payment_status.get("status") == "SUCCEEDED"
        ):
            # Payment successful, update your records
            # You can also emit an event or trigger follow-up processes here

            # Redirect user to the success page
            frappe.local.response["type"] = "redirect"
            frappe.local.response["location"] = "/payment-success"
        else:
            # Payment verification failed
            frappe.log_error(
                f"Wave Payment Verification Failed: {json.dumps(payment_status)}",
                "Wave Payment Verification Error",
            )
            frappe.local.response["type"] = "redirect"
            frappe.local.response["location"] = "/payment-failed"

    except Exception as e:
        frappe.log_error(
            f"Wave Payment Success Handler Error: {str(e)}", "Wave Payment Error"
        )
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/payment-error"


@frappe.whitelist(allow_guest=True)
def payment_error():
    """Handle error redirects from Wave payment"""
    try:
        # Log the error details
        error_data = dict(frappe.request.args)
        frappe.log_error(
            f"Wave Payment Error: {json.dumps(error_data)}",
            "Wave Payment Redirect Error",
        )

        # Redirect user to the payment failed page
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/payment-failed"

    except Exception as e:
        frappe.log_error(
            f"Wave Payment Error Handler Error: {str(e)}", "Wave Payment Error"
        )
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/payment-error"

