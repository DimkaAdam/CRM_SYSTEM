from rest_framework import serializers
from .models import Client,Deals,PipeLine,Company


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'company', 'name', 'email', 'phone','created_at','client_type']


class DealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deals
        fields = '__all__'

    def get_total_amount(self, obj):
        return obj.received_quantity * obj.buyer_price


class PipeLineSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = PipeLine
        fields = ["id", "stage", "company", "company_name"]
