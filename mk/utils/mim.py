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

