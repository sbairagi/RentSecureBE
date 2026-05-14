from rest_framework import serializers
from .unit_serializers import UnitSerializer
from ..models import Building


class BuildingSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True)

    class Meta:
        model = Building
        fields = '__all__'
        read_only_fields = ['owner']

    def validate(self, data):
        return data

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'owner' in validated_data:
            validated_data.pop('owner')
        return super().update(instance, validated_data)
