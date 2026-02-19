from django.apps import AppConfig
import os

class UiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ui"

    def ready(self):
        #prevent double run in dev server
        if os.environ.get('RUN_MAIN') != "true":
            return
        
        from .services import initialize_AE_only
        from .setup import application_name
        from .services import final_registration_status

        try:
            initialize_AE_only(application_name)
            status = final_registration_status
            print("IN-CSE response:", status)
        except Exception as e:
            print("Error registering container:", e)


