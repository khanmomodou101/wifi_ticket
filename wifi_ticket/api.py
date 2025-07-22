import frappe
from erpnext.accounts.report.gross_profit.gross_profit import execute

@frappe.whitelist()
def execute_report():
    filters = {
        "company": "King Baker Foods",
        "from_date": "2025-07-01",
        "to_date": "2025-07-18",
        "group_by" : "Invoice",
        
    }
    filters = frappe._dict(filters)
    columns, data = execute(filters)
    
    # Process the data to get one entry per invoice
    processed_data = []
    current_invoice = None
    
    for row in data:
        if row.get("indent") == 0:  # Invoice header row
            current_invoice = {
                "invoice": row.get("sales_invoice"),
                "customer": row.get("customer"),
                "posting_date": row.get("posting_date"),
                "selling_amount": row.get("selling_amount"),
                "buying_amount": row.get("buying_amount"),
                "gross_profit": row.get("gross_profit"),
                "gross_profit_percent": row.get("gross_profit_%"),
                "currency": row.get("currency"),
                "item_count": 0,
                "items": []
            }
        elif row.get("indent") == 1 and current_invoice:  # Item detail row
            # Only include items with negative or zero gross profit
            gross_profit = row.get("gross_profit", 0)
            if gross_profit < 0:
                current_invoice["item_count"] = current_invoice.get("item_count", 0) + 1
                if "items" not in current_invoice:
                    current_invoice["items"] = []
                current_invoice["items"].append({
                    "item_code": row.get("item_code"),
                    "item_name": row.get("item_name"),
                    "item_group": row.get("item_group"),
                    "qty": row.get("qty"),
                    "selling_rate": row.get("avg._selling_rate"),
                    "valuation_rate": row.get("valuation_rate"),
                    "selling_amount": row.get("selling_amount"),
                    "buying_amount": row.get("buying_amount"),
                    "gross_profit": row.get("gross_profit"),
                    "gross_profit_percent": row.get("gross_profit_%")
                })
            
            # If this is the last item for this invoice, add to processed data only if it has negative items
            if current_invoice.get("invoice") != "Total" and current_invoice.get("item_count", 0) > 0:
                processed_data.append(current_invoice)
                current_invoice = None
    
    return processed_data

@frappe.whitelist()
def affected_invoice(invoice_no):
    """
    Get data for a specific invoice with negative gross profit items
    """
    if not invoice_no:
        return {"error": "Invoice number is required"}
    
    filters = {
        "company": "King Baker Foods",
        "from_date": "2025-01-01",  # Wide date range to ensure we find the invoice
        "to_date": "2025-12-31",
        "group_by": "Invoice",
        "sales_invoice": invoice_no  # Filter by specific invoice
    }
    filters = frappe._dict(filters)
    columns, data = execute(filters)
    
    # Process the data to get the specific invoice
    current_invoice = None
    
    for row in data:
        if row.get("indent") == 0:  # Invoice header row
            current_invoice = {
                "invoice": row.get("sales_invoice"),
                "customer": row.get("customer"),
                "posting_date": row.get("posting_date"),
                "selling_amount": row.get("selling_amount"),
                "buying_amount": row.get("buying_amount"),
                "gross_profit": row.get("gross_profit"),
                "gross_profit_percent": row.get("gross_profit_%"),
                "currency": row.get("currency"),
                "item_count": 0,
                "items": []
            }
        elif row.get("indent") == 1 and current_invoice:  # Item detail row
            # Only include items with negative gross profit
            gross_profit = row.get("gross_profit", 0)
            if gross_profit < 0:
                current_invoice["item_count"] = current_invoice.get("item_count", 0) + 1
                if "items" not in current_invoice:
                    current_invoice["items"] = []
                current_invoice["items"].append({
                    "item_code": row.get("item_code"),
                    "item_name": row.get("item_name"),
                    "item_group": row.get("item_group"),
                    "qty": row.get("qty"),
                    "selling_rate": row.get("avg._selling_rate"),
                    "valuation_rate": row.get("valuation_rate"),
                    "selling_amount": row.get("selling_amount"),
                    "buying_amount": row.get("buying_amount"),
                    "gross_profit": row.get("gross_profit"),
                    "gross_profit_percent": row.get("gross_profit_%")
                })
    
    if current_invoice and current_invoice.get("item_count", 0) > 0:
        return current_invoice
    elif current_invoice:
        return {"message": f"Invoice {invoice_no} found but has no negative gross profit items"}
    else:
        return {"error": f"Invoice {invoice_no} not found"}