from rest_framework import serializers
from .models import Property, Caretaker, Renter, RentRecord, PropertyTaxRecord, PropertyImage, PropertyDocument
from .utils import enforce_limit, update_usage_count



class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = '__all__'

    def validate(self, data):
        enforce_limit(self.context['request'].user, 'max_properties')
        return data

    def create(self, validated_data):
        instance = super().create(validated_data)
        update_usage_count(self.context['request'].user, 'max_properties', Property)
        return instance

class CaretakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caretaker
        fields = '__all__'

    def validate(self, data):
        enforce_limit(self.context['request'].user, 'max_caretakers')
        return data

    def create(self, validated_data):
        instance = super().create(validated_data)
        update_usage_count(self.context['request'].user, 'max_caretakers', Property)
        return instance

class RenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Renter
        fields = '__all__'

    def validate(self, data):
        enforce_limit(self.context['request'].user, 'max_renters')
        return data

    def create(self, validated_data):
        instance = super().create(validated_data)
        update_usage_count(self.context['request'].user, 'max_renters', Property)
        return instance

class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = '__all__'

    def validate(self, data):
        enforce_limit(self.context['request'].user, 'max_property_images')
        return data

    def create(self, validated_data):
        instance = super().create(validated_data)
        update_usage_count(self.context['request'].user, 'max_property_images', Property)
        return instance

class PropertyDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyDocument
        fields = '__all__'

    def validate(self, data):
        enforce_limit(self.context['request'].user, 'max_document_uploads')
        return data

    def create(self, validated_data):
        instance = super().create(validated_data)
        update_usage_count(self.context['request'].user, 'max_document_uploads', Property)
        return instance
    
    

class RentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentRecord
        fields = '__all__'


class PropertyTaxRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyTaxRecord
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'verified_by')