import pytest
from app.utils import generate_slug

@pytest.mark.parametrize(
    "input_string, expected_slug",
    [
        ("Hello World", "hello-world"),
        ("  Leading and Trailing Spaces  ", "leading-and-trailing-spaces"),
        ("Special Chars!@#$%^&*()_+", "special-chars"),
        ("Más Ñandúes y Pingüinos", "mas-nandues-y-pinguinos"),
        ("Multiple---Hyphens", "multiple-hyphens"),
        ("Ends with hyphen-", "ends-with-hyphen"),
        ("Número 123", "numero-123"),
        ("", "n-a"),  # Test case for empty string
        ("---", "n-a"), # Test case for only separators
        ("сложный тест юникода", "slozhnyi-test-iunikoda"), # Russian example
        ("これはユニコードのテストです", "koreha-yunikodo-no-tesuto-desu"), # Japanese example
        ("Ein Test mit Umlauten äöüß", "ein-test-mit-umlauten-aouss"), # German example
    ],
)
def test_generate_slug_various_inputs(input_string, expected_slug):
    assert generate_slug(input_string) == expected_slug

def test_generate_slug_custom_separator():
    assert generate_slug("Custom Separator Test", separator="_") == "custom_separator_test"

def test_generate_slug_long_string():
    long_text = "a" * 260 # Slug length is not explicitly limited by the function itself
    expected = "a" * 260
    # If there were a length limit, the test would need to reflect that.
    # For now, it just checks if it handles long strings without error.
    assert generate_slug(long_text) == expected

def test_generate_slug_no_alphanumeric():
    assert generate_slug("!@#$%^") == "n-a"
    assert generate_slug("!@#$ % ^") == "n-a"

# Consider adding tests for edge cases if specific behaviors are expected,
# e.g., very long strings with specific truncation rules, or specific handling of numbers.
# The current `generate_slug` is basic; more complex requirements would need more tests.
