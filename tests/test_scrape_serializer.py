from django.http import QueryDict

from app.scrape.serializers import ScrapeRequestSerializer


def test_repeated_class_name_values_are_collected():
    query = QueryDict("url=https://example.com&class_name=alpha&class_name=beta")

    serializer = ScrapeRequestSerializer(data=query)

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["url"] == "https://example.com"
    assert serializer.validated_data["class_name"] == ["alpha", "beta"]


def test_missing_parameters_are_rejected():
    serializer = ScrapeRequestSerializer(data=QueryDict())

    assert serializer.is_valid() is False
    assert "url" in serializer.errors
    assert "class_name" in serializer.errors


def test_empty_class_name_is_rejected():
    query = QueryDict("url=https://example.com&class_name=")

    serializer = ScrapeRequestSerializer(data=query)

    assert serializer.is_valid() is False
    assert "class_name" in serializer.errors


def test_too_many_class_names_are_rejected():
    query = QueryDict(mutable=True)
    query["url"] = "https://example.com"
    query.setlist("class_name", [f"item-{index}" for index in range(51)])

    serializer = ScrapeRequestSerializer(data=query)

    assert serializer.is_valid() is False
    assert "class_name" in serializer.errors


def test_overlong_class_name_is_rejected():
    query = QueryDict("url=https://example.com&class_name=" + ("x" * 201))

    serializer = ScrapeRequestSerializer(data=query)

    assert serializer.is_valid() is False
    assert "class_name" in serializer.errors


def test_invalid_url_is_rejected():
    query = QueryDict("url=not-a-url&class_name=item")

    serializer = ScrapeRequestSerializer(data=query)

    assert serializer.is_valid() is False
    assert "url" in serializer.errors
