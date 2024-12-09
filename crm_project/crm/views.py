from django.shortcuts import render
from .models import Client, Deals, Task, PipeLine


def index(request):
    return render(request, 'crm/index.html')

def client_list(request):
    clients = Client.objects.all()
    return render(request, 'crm/client_list.html', {'clients': clients})

def deal_list(request):
    deals = Deals.objects.all()
    return render(request, 'crm/deal_list.html', {'deals': deals})

def task_list(request):
    tasks = Task.objects.all()
    return render(request, 'crm/task_list.html', {'tasks': tasks})

def pipeline_list(request):
    pipelines = PipeLine.objects.all()
    return render(request, 'crm/pipeline_list.html', {'pipelines': pipelines})