import frappe

@frappe.whitelist()
def apply_new_territory_to_all_transactions(customer,territory):
    customer_doc = frappe.get_doc("Customer", customer)
    doc_types = ["Sales Invoice"]
    counter = 0
    for doc_type in doc_types:
        data = frappe.db.get_all(doc_type, filters={"customer":customer,"docstatus":["!=",2]}, fields=["name", "territory"])
        if data:
            for d in data:
                doc_name = frappe.get_doc(doc_type, d.name)
                doc_name.db_set("territory", territory)
                frappe.db.commit()
                counter+=1
    if counter > 0:
        return "Updated territory"


def create_offline_qr_code():
    from mk.events.accounts.sales_invoice import create_qr_code
    invoices = frappe.db.get_all("Sales Invoice",filters={"docstatus":1},fields=["*"])# ,"name":"UPFPP-SINV-2025-00171"
    if invoices:
        print("===============Staring===============")
        for invoice in invoices:
            doc = frappe.get_doc("Sales Invoice",invoice.name)
            try:
                create_qr_code(doc,None)
                print("invoice=============="+str(invoice.name))
            except Exception as e:
                frappe.error_log(e)
        print("===============Finished===============")

