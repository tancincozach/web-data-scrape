from bs4 import BeautifulSoup

class DomExtractorService:
    def parse(self, html_content: str, parser_type: str = "html.parser"):
        """Parse the fetched content using BeautifulSoup."""
        try:
            return BeautifulSoup(html_content, parser_type)
        except Exception as e:
            print(f"Error parsing content: {e}")
            return None

    def get_recursive_elements_in_class(self, soup: BeautifulSoup, class_name: str):
        """Recursively extract elements with a specified class."""
        try:
            if not isinstance(soup, BeautifulSoup):
                print(f"Expected BeautifulSoup object, got {type(soup)}.")
                return []

            elements = soup.find_all(class_=class_name)
            if not elements:
                print(f"No elements found with class '{class_name}'.")
                return []

            extracted_data = [self._extract_recursive(element) for element in elements]
            return extracted_data
        except Exception as e:
            print(f"Error extracting elements by class '{class_name}': {e}")
            return []

    def _extract_recursive(self, element):
        """Helper function to extract tag, text, attributes, and children recursively."""
        return {
            'tag': element.name,
            'text': element.get_text(strip=True),
            'attributes': dict(element.attrs),
            'children': [self._extract_recursive(child) for child in element.find_all(recursive=False)]
        }

    def get_selected_elements_on_container(self, soup: BeautifulSoup, container_class_name: str, white_list_elements=None):
        """
        Get information from elements of a specific class, filtered by a whitelist.

        :param soup: Parsed HTML document.
        :param container_class_name: Class name of the container that holds the product elements.
        :param white_list_elements: List of allowed class names for filtering elements (optional).
        :return: A list of dictionaries containing class names and their corresponding text values.
        """
        if white_list_elements is None:
            white_list_elements = []

        elements = self.get_recursive_elements_in_class(soup, container_class_name)
        result = []

        print(f"Found {len(elements)} elements in the container class '{container_class_name}'.")

        for element in elements:
            element_data = {}

            # Collect data based on the whitelist
            for white_class in white_list_elements:
                matching_child = next(
                    (child for child in element.get('children', [])
                     if white_class in child.get('attributes', {}).get('class', [])),
                    None
                )
                if matching_child:
                    element_data[white_class] = matching_child.get('text', 'Not found')

            if element_data:  # Only add if we found relevant data
                result.append(element_data)

        if not result:
            print("No products found with the specified class name and whitelist.")

        return result
    
    def get_all_elements_in_class(self, soup, class_name):
        """Get all elements of a specified class."""
        return self.get_recursive_elements_in_class(soup, class_name)

    def get_selected_elements_in_class(self, soup, class_name, white_list):
        """Get selected elements based on the provided white list."""
        return self.get_selected_elements_on_container(soup, class_name, white_list)
    
    def get_total_pages(self, soup, has_pagination, pagination_class):
        """Calculate total pages based on pagination structure."""
        if has_pagination == 'true' and pagination_class:
            pagination_elements = soup.find_all(class_=pagination_class)
            return len(pagination_elements) if pagination_elements else 1
        return 1