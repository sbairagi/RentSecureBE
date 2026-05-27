from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from ..models import Caretaker


class CaretakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caretaker
        fields = '__all__'
        extra_kwargs = {
            'id_proof': {'required': False},
        }

    def validate(self, data):
        user = self.context['request'].user
        unit = data.get('unit') or getattr(self.instance, 'unit', None)
        if unit and unit.owner != user:
            raise PermissionDenied("You do not own the selected unit.")
        return data

    def update(self, instance, validated_data):
        unit = validated_data.get('unit')
        if unit and unit.owner != self.context['request'].user:
            raise serializers.ValidationError("You do not own the selected unit.")
        return super().update(instance, validated_data)
