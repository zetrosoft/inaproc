import frappe

from inaproc.migrasi import update_item_defaults


def run_migration():
    print("Memulai proses pembaruan default warehouse untuk Item...")
    update_item_defaults.update_item_defaults()
    print("Proses pembaruan default warehouse untuk Item dari runner selesai.")
