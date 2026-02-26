from django.shortcuts import render
from . import services

def dashboard(request):
    return render(request, "ui/dashboard.html", {
        "registration_status": services.final_registration_status
    })