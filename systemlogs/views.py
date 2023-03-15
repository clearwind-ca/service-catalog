from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from web.helpers import process_query_params

from .models import SystemLog


@login_required
@process_query_params
def log_list(request):
    sources = SystemLog.objects.filter().order_by("created")
    get = request.GET

    paginator = Paginator(sources, per_page=get["per_page"])
    page_number = get["page"]
    page_obj = paginator.get_page(page_number)

    context = {
        "logs": page_obj,
    }
    return render(request, "log-list.html", context)
