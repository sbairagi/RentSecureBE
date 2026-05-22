from rest_framework import serializers

from .models import (
    Building,
    Caretaker,
    RentAgreementDraft,
    Renter,
    RentRecord,
    Unit,
    UnitDocument,
    UnitImage,
)


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = '__all__'
        read_only_fields = ['owner']

    def validate(self, data):
        user = self.context['request'].user

        # ✅ Sirf building ownership check — usage limit enforcement hata diya
        building = data.get('building') or getattr(self.instance, 'building', None)
        if building and building.owner != user:
            raise serializers.ValidationError("You do not own the selected building.")

        return data

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        building = validated_data.get('building')
        if building and building.owner != self.context['request'].user:
            raise serializers.ValidationError("You do not own the selected building.")
        return super().update(instance, validated_data)

class BuildingSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True, source='units')

    class Meta:
        model = Building
        fields = '__all__'
        read_only_fields = ['owner']

    def validate(self, data):
        self.context['request'].user
        # Ownership validation etc. if needed
        return data

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Prevent ownership transfer
        if 'owner' in validated_data:
            validated_data.pop('owner')
        return super().update(instance, validated_data)

class CaretakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caretaker
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

class UnitImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitImage
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

class UnitDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitDocument
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

class RentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

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

    def create(self, validated_data):
        return super().create(validated_data)

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

class RentAgreementDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentAgreementDraft
        fields = '__all__'
        read_only_fields = ['user', 'generated_at', 'file']

    def validate(self, data):
        request_user = self.context['request'].user

        renter = data.get('renter')
        unit = data.get('unit')

        if not renter or not unit:
            raise serializers.ValidationError("Both renter and unit are required.")

        if unit.owner != request_user:
            raise serializers.ValidationError("You do not own the selected unit.")

        if renter.unit != unit:
            raise serializers.ValidationError("Renter does not belong to the selected unit.")

        return data









# serializers.py

class RenterRentRecordSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(source='rent_due_date')
    amount = serializers.DecimalField(source='amount_paid', max_digits=10, decimal_places=2)
    invoice_url = serializers.SerializerMethodField()

    class Meta:
        model = RentRecord
        fields = ['due_date', 'amount', 'late_fee', 'payment_status', 'invoice_url']

    def get_invoice_url(self, obj):
        if obj.payment_status == "PAID":
            return obj.invoice_url or ""
        return ""
