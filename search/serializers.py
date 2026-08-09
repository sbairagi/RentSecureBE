from rest_framework import serializers


class SearchResultSerializer(serializers.Serializer):
    resource_type = serializers.CharField()
    id = serializers.IntegerField()
    title = serializers.CharField()
    subtitle = serializers.CharField(allow_blank=True, default="")
    status = serializers.CharField(allow_blank=True, default="")
    metadata = serializers.DictField(allow_empty=True, default=dict)
    last_updated = serializers.DateTimeField(allow_null=True)
    navigation_target = serializers.CharField()


class SearchSuggestionsSerializer(serializers.Serializer):
    query = serializers.CharField()
    suggestions = serializers.ListField(child=serializers.CharField())


class SearchResponseSerializer(serializers.Serializer):
    query = serializers.CharField()
    total_results = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    results = SearchResultSerializer(many=True)
    available_resource_types = serializers.ListField(child=serializers.CharField())
