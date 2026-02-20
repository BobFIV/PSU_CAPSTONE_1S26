from django.apps import AppConfig
import os

class UiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ui"

    def ready(self):
        #prevent double run in dev server
        if os.environ.get('RUN_MAIN') != "true":
            return
        
        from . import services
        from .setup import application_name

        try:
            services.initialize_AE_only(application_name)
            status = services.final_registration_status  # read after call so updated value is used
            print("IN-CSE response:", status)
        except Exception as e:
            print("Error registering container:", e)


