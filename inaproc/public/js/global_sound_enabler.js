
frappe.ready(function() {
    function playNotificationSound() {
        if (frappe.boot.user.all_defaults && frappe.boot.user.all_defaults["enable_notifications"] === 1) {
            frappe.play_notif_sound(); 
        }
    }

    frappe.realtime.on('notification', function(data) {
        if (data.user === frappe.session.user) {
            playNotificationSound();
        }
    });
});