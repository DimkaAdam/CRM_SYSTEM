from django.shortcuts import render, redirect
from .models import Client, Deals, Task, PipeLine

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from .serializers import ClientSerializer


def index(request):
    return render(request, 'crm/index.html')

def client_list(request):
    clients = Client.objects.all()

    supplier = clients.filter(type='suppliers')
    buyer = clients.filter(type = 'buyers')

    return render(request, 'crm/client_list.html', {
        'clients': clients,
        'suppliers': supplier,
        'buyers': buyer,
    })

def deal_list(request):
    deals = Deals.objects.all()
    return render(request, 'crm/deal_list.html', {'deals': deals})

def task_list(request):
    tasks = Task.objects.all()
    return render(request, 'crm/task_list.html', {'tasks': tasks})

def pipeline_list(request):
    pipelines = PipeLine.objects.all()
    return render(request, 'crm/pipeline_list.html', {'pipelines': pipelines})

class ClientCreateAPIView(APIView):
    def post(self, request):
        serializer = ClientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
