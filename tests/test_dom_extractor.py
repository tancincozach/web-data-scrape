from app.services.dom_extractor_service import DomExtractorService


def count_nodes(data):
    return 1 + sum(count_nodes(child) for child in data.get("children", []))


def test_extracts_nested_tree_without_duplicating_descendants():
    html = """
    <div class="item" id="root">
      <span class="name">Alpha</span>
      <div class="child"><span class="name">Beta</span></div>
    </div>
    """
    service = DomExtractorService()
    data = service.get_elements(service.parse(html), "item")

    assert len(data) == 1
    root = data[0]
    assert root["tag"] == "div"
    assert root["attributes"]["id"] == "root"
    assert [child["tag"] for child in root["children"]] == ["span", "div"]
    assert root["children"][0]["text"] == "Alpha"
    assert root["children"][1]["children"][0]["text"] == "Beta"
    # Root + span + div + span. The old recursive=True implementation would
    # duplicate the nested span and grow with depth.
    assert count_nodes(root) == 4


def test_deep_tree_stays_linear():
    depth = 20
    html = (
        '<div class="item">'
        + ("<div>" * depth)
        + "leaf"
        + ("</div>" * depth)
        + "</div>"
    )
    service = DomExtractorService(max_depth=50, max_nodes=10_000)
    data = service.get_elements(service.parse(html), "item")

    assert len(data) == 1
    assert count_nodes(data[0]) == depth + 1


def test_non_recursive_extraction_excludes_children():
    html = '<div class="item"><span>child</span></div>'
    service = DomExtractorService()
    data = service.get_elements(service.parse(html), "item", recursive=False)

    assert data[0]["children"] == []
    assert count_nodes(data[0]) == 1


def test_node_cap_marks_truncation():
    depth = 10
    html = (
        '<div class="item">'
        + ("<div>" * depth)
        + "leaf"
        + ("</div>" * depth)
        + "</div>"
    )
    service = DomExtractorService(max_depth=50, max_nodes=5)
    data = service.get_elements(service.parse(html), "item")

    assert len(data) == 1
    assert count_nodes(data[0]) <= 5
    assert any(node.get("truncated") for node in [data[0], *flatten(data[0])])


def test_depth_cap_marks_truncation():
    html = '<div class="item"><div><div><span>deep</span></div></div></div>'
    service = DomExtractorService(max_depth=1, max_nodes=100)
    data = service.get_elements(service.parse(html), "item")

    assert data[0]["children"]
    assert data[0]["children"][0]["truncated"] is True


def test_multiple_class_names_and_limit():
    html = '<div class="a">A1</div>' '<div class="b">B1</div>' '<div class="a">A2</div>'
    service = DomExtractorService()
    data = service.get_elements(service.parse(html), ["a", "b"])

    assert [item["text"] for item in data] == ["A1", "A2", "B1"]


def test_max_elements_caps_total_matches():
    html = "".join(f'<div class="item">{index}</div>' for index in range(10))
    service = DomExtractorService(max_elements=3)

    data = service.get_elements(service.parse(html), "item")

    assert len(data) == 3


def test_filtered_elements_reads_the_tree():
    html = """
    <div class="container">
      <div class="title">Title</div>
      <div class="body">Body</div>
    </div>
    """
    service = DomExtractorService()
    result = service.get_filtered_elements(
        service.parse(html),
        "container",
        whitelist_classes=["title", "body"],
    )

    assert result == [{"title": "Title", "body": "Body"}]


def flatten(data):
    for child in data.get("children", []):
        yield child
        yield from flatten(child)
