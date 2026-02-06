
import re

pattern_str = r"educational\s*background"
text = "--- Educational Background ---"

combined_pattern = f"(?:^|\\n)\\s*(?:[-*=_]+\\s*)?(?:\\d+\\.|[IVX]+\\.)?\\s*{pattern_str}\\s*(?:[:\\-–._]*\\s*)?(?:\\n|$)"

print(f"Pattern: {combined_pattern}")
print(f"Text: '{text}'")

match = re.search(combined_pattern, text, re.IGNORECASE)
print(f"Match: {match}")

if match:
    print("Found!")
else:
    print("Not found.")
