from bs4 import BeautifulSoup

class DomExtractorService:
    def parse(self, html_content: str, parser_type: str = "html.parser"):
        """Parse HTML content using BeautifulSoup."""
        try:
            return BeautifulSoup(html_content, parser_type)
        except Exception as e:
            print(f"Error parsing content: {e}")
            return None

    def _extract_element_data(self, element, recursive=True):
        """Extract element data, optionally including non-recursive children."""
        return {
            'tag': element.name,
            'text': element.get_text(strip=True),
            'attributes': dict(element.attrs),
            'children': [self._extract_element_data(child) for child in element.find_all(recursive=recursive)]
        }

    def get_elements(self, soup, class_names, recursive=True, limit=None):
        """Fetch elements by class names and extract their data."""
        class_names = [class_names] if isinstance(class_names, str) else class_names
        elements = [el for cls in class_names for el in soup.find_all(class_=cls, limit=limit)]
        
        return [self._extract_element_data(el, recursive) for el in elements] if elements else []

    def get_filtered_elements(self, soup, container_class, whitelist_classes=None):
        """Extract whitelisted elements inside a specific container."""
        whitelist_classes = whitelist_classes or []
        container_elements = self.get_elements(soup, container_class)

        def search_for_whitelisted(el, data):
            for child in el.get('children', []):
                child_classes = child.get('attributes', {}).get('class', [])
                if isinstance(child_classes, str):
                    child_classes = child_classes.split()
                
                for whitelist in whitelist_classes:
                    if whitelist in child_classes:
                        data[whitelist] = child.get('text', 'Not found')
                search_for_whitelisted(child, data)

        result = []
        for el in container_elements:
            element_data = {}
            search_for_whitelisted(el, element_data)
            if element_data:
                result.append(element_data)
        
        return result

    def get_total_pages(self, soup, pagination_class=None):
        """Get total page count based on pagination elements."""
        if pagination_class:
            pagination_elements = soup.find_all(class_=pagination_class)
            return len(pagination_elements) if pagination_elements else 1
        return 1
