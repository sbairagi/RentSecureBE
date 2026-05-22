from rest_framework import serializers

from ..models import (
    RentAgreementDraft,
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


class RentAgreementDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentAgreementDraft
        fields = '__all__'
        read_only_fields = ['user', 'generated_at']

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
