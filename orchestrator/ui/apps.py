from django.apps import AppConfig
import os

class UiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ui"

    def ready(self):
        print("DEBUG: apps.py ready() called")

        if os.environ.get('RUN_MAIN') != "true":
            print("DEBUG: blocked by RUN_MAIN guard, RUN_MAIN =", os.environ.get('RUN_MAIN'))
            return
        
        from . import services
        from .setup import application_name

        try:
            services.initialize_AE_only(application_name)
            status = services.final_registration_status
            print("IN-CSE response:", status)
        except Exception as e:
            print("Error registering container:", e)


