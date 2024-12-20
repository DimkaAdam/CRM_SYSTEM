from rest_framework import serializers
from .models import Client,Deals


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'company', 'name', 'email', 'phone','created_at','client_type']


class DealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deals
        fields = '__all__'