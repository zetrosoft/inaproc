import frappe
from frappe.model.document import Document


class CustomItem(Document):
    def autoname(self):
        # Pastikan item_code sudah diatur oleh skrip migrasi
        # Jika sudah ada, gunakan itu sebagai nama
        if self.item_code:
            self.name = self.item_code
        # Jika tidak, biarkan Frappe menangani penamaan standar (ini seharusnya tidak terjadi)
        # else:
        #    super(CustomItem, self).autoname()
