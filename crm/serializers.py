from rest_framework import serializers
from .models import Client,Deals,PipeLine,Company


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'company', 'name', 'email', 'phone','created_at','client_type']


class DealSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    buyer_name = serializers.CharField(source='buyer.name', read_only=True)
    transport_company_name = serializers.CharField(source='transport_company.name', read_only=True)
    total_amount = serializers.SerializerMethodField()

    scale_ticket_sent = serializers.BooleanField(read_only=True)
    scale_ticket_relative_path = serializers.SerializerMethodField()

    class Meta:
        model = Deals
        fields = [
            'id', 'date',
            'supplier', 'supplier_name',
            'buyer', 'buyer_name',
            'grade',
            'shipped_quantity', 'shipped_pallets',
            'received_quantity', 'received_pallets',
            'supplier_price', 'buyer_price',
            'total_amount',
            'transport_cost', 'transport_company', 'transport_company_name',
            'scale_ticket',
            'scale_ticket_sent',
            'scale_ticket_relative_path',
        ]

    def get_total_amount(self, obj):
        if obj.received_quantity and obj.buyer_price:
            return round(obj.received_quantity * obj.buyer_price, 2)
        return 0.0

    def get_scale_ticket_relative_path(self, obj):
        # использует твой уже существующий helper в модели Deals
        try:
            return obj.get_scale_ticket_relative_path() or ""
        except AttributeError:
            return ""

class PipeLineSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = PipeLine
        fields = ["id", "stage", "company", "company_name"]
