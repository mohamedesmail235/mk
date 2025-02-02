frappe.ui.form.on("Customer", {
    territory:function (frm) {
        frm.set_df_property("custom_apply_new_territory_to_all_transactions", "hidden", 0);
    },
    custom_apply_new_territory_to_all_transactions:function (frm) {
        frappe.show_alert('Start Updating')
        frm.call({
            method:"mk.utils.mim.apply_new_territory_to_all_transactions",
            args:{
                customer:frm.doc.name,
                territory:frm.doc.territory
            },
            callback:function (res) {
                if(res.message){
                    frappe.show_alert('Updated')
                }
            }
        })
    }
})