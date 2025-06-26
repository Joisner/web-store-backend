import re
from typing import Optional

def generate_slug(text: str, separator: str = '-') -> str:
    """
    Generate a URL-friendly slug from a given text string.
    """
    if not text:
        return ""
    # Convert to lowercase
    slug = text.lower()
    # Remove accents and special characters (basic version)
    slug = re.sub(r'[àáâãäå]', 'a', slug)
    slug = re.sub(r'[èéêë]', 'e', slug)
    slug = re.sub(r'[ìíîï]', 'i', slug)
    slug = re.sub(r'[òóôõö]', 'o', slug)
    slug = re.sub(r'[ùúûü]', 'u', slug)
    slug = re.sub(r'[ýÿ]', 'y', slug)
    slug = re.sub(r'[ñ]', 'n', slug)
    slug = re.sub(r'[ç]', 'c', slug)
    # Replace non-alphanumeric characters (except separator) with the separator
    slug = re.sub(r'[^a-z0-9]+', separator, slug)
    # Remove leading/trailing separators
    slug = slug.strip(separator)
    # Optional: Ensure slug is not empty after processing
    if not slug: # e.g. if input was "---"
        # you might return a default or raise an error
        return "n-a" # or some other default
    return slug


# Example usage:
# print(generate_slug("Esto es una Cadena de Prueba!"))
# Output: esto-es-una-cadena-de-prueba
# print(generate_slug("  Múltiples   Espacios   & Ñandú "))
# Output: multiples-espacios-nandu

# Note: For more robust slugification, especially with multiple languages,
# consider using a library like `python-slugify`.
# `pip install python-slugify`
# from slugify import slugify
# def generate_slug_robust(text: str) -> str:
#     return slugify(text)
