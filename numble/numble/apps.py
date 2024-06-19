from django.apps import AppConfig
import atexit

class MyAppConfig(AppConfig):
    name = 'your_app_name'

    def ready(self):
        # Start the queue listener when the app is ready
        from django.conf import settings
        settings.queue_listener.start()

        # Register the stop function to be called when the app exits
        atexit.register(self.shutdown)

    def shutdown(self):
        # Stop the queue listener when the app exits
        from django.conf import settings
        settings.queue_listener.stop()
