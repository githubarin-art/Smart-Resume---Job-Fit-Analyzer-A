from parsers.section_detector import _parse_experience

def test_experience_parsing_bug():
    # Simulation of the bug: A bullet point containing "engineer" splits the entry
    text_blocks = [
        {"text": "Software Engineer", "is_bold": True},
        {"text": "Google, 2020-Present", "is_bold": False},
        {"text": "• Developed backend services for 500+ engineers to use daily", "is_bold": False},
        {"text": "• Managed a team of 5 junior developers", "is_bold": False}
    ]
    
    entries = _parse_experience("", text_blocks)
    
    print(f"Entries found: {len(entries)}")
    for i, entry in enumerate(entries):
        print(f"Entry {i+1}: {entry.title} at {entry.company}")
        print(f"  Responsibilities: {len(entry.responsibilities)}")
        print(f"  Source: {entry.source_text}")

if __name__ == "__main__":
    test_experience_parsing_bug()
