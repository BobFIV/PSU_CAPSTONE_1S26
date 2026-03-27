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
        from . import find_gatewayAE
        from .setup import application_name
        from .setup import originator
        from .setup import cse_url

        try:
            services.initialize_AE_only(application_name)
            status = services.final_registration_status  # read after call so updated value is used
            print("IN-CSE response:", status)
            if find_gatewayAE.retrieve_gatewayAE(originator,cse_url):
                print("found gateway AEs")
            else:
                print("no gatewayAgent AEs found")

        except Exception as e:
            print("Error registering:", e)


