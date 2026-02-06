"""
Debug script to analyze PDF parsing for two-column resumes.
Upload a resume and see exactly what the parser extracts.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parsers.pdf_parser import parse_pdf
from parsers.section_detector import detect_sections, _find_section_boundaries
import glob

def debug_pdf_parsing(file_path: str):
    """Debug PDF parsing for a specific file."""
    print(f"\n{'='*60}")
    print(f"DEBUGGING: {os.path.basename(file_path)}")
    print(f"{'='*60}")
    
    # Parse PDF
    raw_text, text_blocks = parse_pdf(file_path)
    
    print(f"\n--- RAW TEXT (first 500 chars) ---")
    print(raw_text[:500])
    
    print(f"\n--- TEXT BLOCKS ({len(text_blocks)} total) ---")
    for i, block in enumerate(text_blocks[:30]):  # First 30 blocks
        text = block['text'][:50] + "..." if len(block['text']) > 50 else block['text']
        left = block.get('left', 0)
        column = "LEFT" if left < 200 else "RIGHT"
        print(f"  [{i:2d}] {column:5s} L={left:5.0f} | {text}")
    
    print(f"\n--- SECTION DETECTION ---")
    # Check section boundaries
    boundaries = _find_section_boundaries(text_blocks)
    print(f"Detected section boundaries: {boundaries}")
    
    # Look for section header keywords in blocks
    section_keywords = ['education', 'experience', 'skills', 'projects']
    print(f"\n--- BLOCKS CONTAINING SECTION KEYWORDS ---")
    for i, block in enumerate(text_blocks):
        text_lower = block['text'].lower()
        for keyword in section_keywords:
            if keyword in text_lower:
                left = block.get('left', 0)
                text_len = len(block['text'])
                print(f"  [{i}] '{block['text'][:60]}' (left={left:.0f}, len={text_len})")
    
    # Run full detection
    print(f"\n--- FULL SECTION DETECTION ---")
    sections = detect_sections(raw_text, text_blocks)
    print(f"Skills: {len(sections.get('skills', []))}")
    print(f"Experience: {len(sections.get('experience', []))}")
    print(f"Education: {len(sections.get('education', []))}")
    print(f"Projects: {len(sections.get('projects', []))}")
    
    if sections.get('experience'):
        print(f"\n  Experience entries:")
        for exp in sections['experience'][:3]:
            print(f"    - {getattr(exp, 'company', 'N/A')} | {getattr(exp, 'title', 'N/A')}")
    
    if sections.get('education'):
        print(f"\n  Education entries:")
        for edu in sections['education'][:3]:
            print(f"    - {getattr(edu, 'institution', 'N/A')} | {getattr(edu, 'degree', 'N/A')}")

if __name__ == "__main__":
    # Find PDF files in test_resumes or uploads folder
    search_paths = [
        "test_resumes/*.pdf",
        "uploads/*.pdf",
        "../test_resumes/*.pdf",
    ]
    
    pdf_files = []
    for pattern in search_paths:
        pdf_files.extend(glob.glob(pattern))
    
    if not pdf_files:
        print("No PDF files found. Creating a test with sample text blocks...")
        # Simulate two-column parsing
        sample_blocks = [
            {"text": "ANGELA WILKINSON", "left": 50, "top": 50},
            {"text": "EXPERIENCE", "left": 300, "top": 100},
            {"text": "SKILLS", "left": 50, "top": 200},
            {"text": "Problem Solving", "left": 50, "top": 220},
            {"text": "ADMINISTRATIVE ASSISTANT", "left": 300, "top": 120},
            {"text": "Redford & Sons, Boston, MA", "left": 300, "top": 140},
            {"text": "EDUCATION", "left": 50, "top": 350},
            {"text": "DEGREE NAME / MAJOR", "left": 50, "top": 370},
            {"text": "University, Location 2011 - 2015", "left": 50, "top": 390},
        ]
        
        print("\n--- SIMULATED TWO-COLUMN BLOCKS ---")
        for i, block in enumerate(sample_blocks):
            text = block['text']
            left = block.get('left', 0)
            column = "LEFT" if left < 200 else "RIGHT"
            print(f"  [{i:2d}] {column:5s} L={left:5.0f} | {text}")
        
        print("\n--- SECTION DETECTION ON SAMPLE ---")
        boundaries = _find_section_boundaries(sample_blocks)
        print(f"Boundaries: {boundaries}")
    else:
        for pdf_file in pdf_files[:2]:  # Debug first 2 PDFs
            debug_pdf_parsing(pdf_file)
