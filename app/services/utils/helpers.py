def replace_values_to_space_to_lower_case(text, replacements):
    for old_value in replacements:
        text = text.replace(old_value, ' ')
    return text.lower()

def replace_values_to_dash_to_lower_case(text, replacements):
    for old_value in replacements:
        text = text.replace(old_value, '-')
    return text.lower()

def translate_deutsch_to_readable(text):
    # Expanded translation table for common German special characters
    translation_table = str.maketrans({
        'ä': 'ae',
        'ö': 'oe',
        'ü': 'ue',
        'Ä': 'Ae',
        'Ö': 'Oe',
        'Ü': 'Ue',
        'ß': 'ss'
    })
    return text.translate(translation_table)