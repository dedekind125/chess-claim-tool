from Foundation import NSUserNotification, NSUserNotificationCenter


class Notification:
    """ The Notification System using Apple's native Notifications System
    Attributes:
        notification: The notification
        center: Apple notification center.
    """

    def __init__(self):
        self.notification = NSUserNotification.alloc().init()
        self.center = NSUserNotificationCenter.defaultUserNotificationCenter()
        self.center.setDelegate_(self)

    def userNotificationCenter_shouldPresentNotification_(self, center, notification):
        return True

    def clearNotifications(self):
        """Clear any displayed alerts we have posted."""
        self.center.removeAllDeliveredNotifications()

    def notify(self, title, subtitle, text):
        """ Sets notification details and send the notification to the
        notification center.
        Args:
            title: The title of the notification.
            subtitle: The subtitle of the notification.
            text: The informative text of the notification.
        """
        self.notification.setTitle_(title)
        self.notification.setSubtitle_(subtitle)
        self.notification.setInformativeText_(text)
        self.notification.setSoundName_("NSUserNotificationDefaultSoundName")

        self.center.scheduleNotification_(self.notification)
