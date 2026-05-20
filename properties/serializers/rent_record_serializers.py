from rest_framework import serializers
from ..models import RentRecord


class RentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']

    def validate(self, data):
        user = self.context['request'].user
        unit = data.get('unit') or getattr(self.instance, 'unit', None)
        renter = data.get('renter') or getattr(self.instance, 'renter', None)

        if not unit or unit.owner != user:
            raise serializers.ValidationError("You do not own the selected unit.")
        if not renter or renter.unit.owner != user:
            raise serializers.ValidationError("You do not own the selected renter.")
        if renter.unit.id != unit.id:
            raise serializers.ValidationError("Renter is not assigned to the selected unit.")
        if 'amount_paid' in data and data['amount_paid'] < 0:
            raise serializers.ValidationError("Amount paid cannot be negative.")

        rent_month = data.get('rent_month') or getattr(self.instance, 'rent_month', None)
        date_paid = data.get('date_paid') or getattr(self.instance, 'date_paid', None)
        if rent_month and date_paid and date_paid < rent_month:
            raise serializers.ValidationError("Date paid cannot be before the rent month.")
        return data

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if 'unit' in validated_data and validated_data['unit'].owner != user:
            raise serializers.ValidationError("You do not own the selected unit.")
        if 'renter' in validated_data and validated_data['renter'].unit.owner != user:
            raise serializers.ValidationError("You do not own the selected renter.")

        unit = validated_data.get('unit', instance.unit)
        renter = validated_data.get('renter', instance.renter)
        if renter.unit.id != unit.id:
            raise serializers.ValidationError("Renter must be part of the selected unit.")
        return super().update(instance, validated_data)

    def get_invoice_url(self, obj):
        if obj.payment_status == "PAID" and obj.invoice_pdf:
            return obj.invoice_pdf.url
        return ""
