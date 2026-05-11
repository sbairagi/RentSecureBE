from rest_framework import serializers
from ..models import Renter, RentRecord


class RenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Renter
        fields = '__all__'

    def validate(self, data):
        user = self.context['request'].user
        unit = data.get('unit') or getattr(self.instance, 'unit', None)
        if unit and unit.owner != user:
            raise serializers.ValidationError("You do not own the selected unit.")
        return data

    def update(self, instance, validated_data):
        unit = validated_data.get('unit')
        if unit and unit.owner != self.context['request'].user:
            raise serializers.ValidationError("You do not own the selected unit.")
        return super().update(instance, validated_data)


class RenterRentRecordSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(source='rent_due_date')
    amount = serializers.DecimalField(source='amount_paid', max_digits=10, decimal_places=2)
    invoice_url = serializers.SerializerMethodField()

    class Meta:
        model = RentRecord
        fields = ['due_date', 'amount', 'late_fee', 'payment_status', 'invoice_url']

    def get_invoice_url(self, obj):
        if obj.payment_status == "PAID":
            return obj.invoice_pdf.url or ""
        return ""
