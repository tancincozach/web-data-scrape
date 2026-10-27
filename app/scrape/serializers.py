from rest_framework import serializers


class QueryListField(serializers.ListField):
    """A ListField that reads repeated query-string values via ``getlist``."""

    def get_value(self, dictionary):
        if hasattr(dictionary, "getlist"):
            return dictionary.getlist(self.field_name)
        return super().get_value(dictionary)


class ScrapeRequestSerializer(serializers.Serializer):
    url = serializers.URLField(max_length=2048)
    class_name = QueryListField(
        child=serializers.CharField(max_length=200, allow_blank=False),
        allow_empty=False,
        max_length=50,
    )
