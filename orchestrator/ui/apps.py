from django.apps import AppConfig
import os

class UiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ui"

    def ready(self):
        #prevent double run in dev server
        if os.environ.get('RUN_MAIN') != True:
            return
        
        from .services import create_starter_AE
        from . import services

        try:
            status = create_starter_AE()
            services.registration_status = "Successful Startup" #this shows that an AE was created
            print("IN-CSE response:", status)
        except Exception as e:
            print("Error registering container:", e)


