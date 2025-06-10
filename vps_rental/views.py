from datetime import date

from django.shortcuts import render


def hello(request):
    return render(request, "index.html", {"current_date": date.today()})
