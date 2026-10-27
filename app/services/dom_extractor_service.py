from bs4 import BeautifulSoup

from .exceptions import ParseError


class DomExtractorService:
    def __init__(
        self,
        max_depth: int = 50,
        max_nodes: int = 10_000,
        max_elements: int = 1_000,
    ):
        if max_depth < 0:
            raise ValueError("max_depth must be non-negative.")
        if max_nodes < 1:
            raise ValueError("max_nodes must be positive.")
        if max_elements < 1:
            raise ValueError("max_elements must be positive.")
        self.max_depth = max_depth
        self.max_nodes = max_nodes
        self.max_elements = max_elements

    def parse(self, html_content: str, parser_type: str = "html.parser"):
        """Parse HTML content using BeautifulSoup.

        :raises ParseError: if the content cannot be parsed.
        """
        try:
            return BeautifulSoup(html_content, parser_type)
        except Exception as exc:
            raise ParseError("Unable to parse the fetched HTML.") from exc

    def _extract_element_data(
        self, element, max_depth, max_nodes, state, include_children
    ):
        """Build a nested representation of one element.

        Children are read with ``recursive=False`` so every node is emitted
        once. The previous implementation used ``recursive=True`` here, which
        re-expanded each descendant's entire subtree and grew exponentially
        with document depth.
        """
        state["count"] += 1
        data = {
            "tag": element.name,
            "text": element.get_text(strip=True),
            "attributes": dict(element.attrs),
            "children": [],
        }

        if not include_children:
            return data

        if max_depth <= 0 or state["count"] >= max_nodes:
            data["truncated"] = True
            state["truncated"] = True
            return data

        truncated_here = False
        for child in element.find_all(recursive=False):
            if state["count"] >= max_nodes:
                truncated_here = True
                state["truncated"] = True
                break
            data["children"].append(
                self._extract_element_data(
                    child,
                    max_depth - 1,
                    max_nodes,
                    state,
                    include_children=True,
                )
            )

        if truncated_here:
            data["truncated"] = True
        return data

    def get_elements(self, soup, class_names, recursive=True, limit=None):
        """Fetch elements by class names and extract their data.

        ``recursive=True`` returns the full descendant tree. ``recursive=False``
        returns only the matched element itself.
        """
        class_names = [class_names] if isinstance(class_names, str) else class_names
        class_names = [name for name in class_names if name]

        elements = []
        for class_name in class_names:
            remaining = self.max_elements - len(elements)
            if remaining <= 0:
                break
            match_limit = min(limit, remaining) if limit else remaining
            for element in soup.find_all(class_=class_name, limit=match_limit):
                state = {"count": 0, "truncated": False}
                elements.append(
                    self._extract_element_data(
                        element,
                        self.max_depth,
                        self.max_nodes,
                        state,
                        include_children=recursive,
                    )
                )
        return elements

    def get_filtered_elements(self, soup, container_class, whitelist_classes=None):
        """Extract whitelisted elements inside a specific container."""
        whitelist_classes = whitelist_classes or []
        container_elements = self.get_elements(soup, container_class)

        def search_for_whitelisted(element, data):
            for child in element.get("children", []):
                child_classes = child.get("attributes", {}).get("class", [])
                if isinstance(child_classes, str):
                    child_classes = child_classes.split()

                for whitelist in whitelist_classes:
                    if whitelist in child_classes:
                        data[whitelist] = child.get("text", "Not found")
                search_for_whitelisted(child, data)

        result = []
        for element in container_elements:
            element_data = {}
            search_for_whitelisted(element, element_data)
            if element_data:
                result.append(element_data)

        return result
