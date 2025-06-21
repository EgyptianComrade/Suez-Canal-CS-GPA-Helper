import re
import json
from rich.console import Console

def parse_markdown_to_json():
    """
    Parses the 'meh.txt' markdown file to create a structured curriculum.json,
    including level, semester, and course type.
    """
    console = Console()
    try:
        with open('meh.txt', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        console.print("[bold red]Error: 'meh.txt' not found.[/bold red]")
        return

    curriculum = {}
    
    # --- State Variables ---
    current_level = "Unknown"
    current_semester = "Unknown"
    current_track = "General"
    is_elective_table = False

    # --- Regex for parsing headings ---
    course_code_pattern = re.compile(r'^[A-Z]{3}\d{3}$')
    level_track_pattern = re.compile(r'### \*\*(?P<level>\w+ Level)(?: – (?P<track>.+))?\*\*')
    semester_pattern = re.compile(r'#### \*\*(\d.. Semester)\*\*')
    elective_table_pattern = re.compile(r'#### \*\*Elective Courses')
    
    for line in content.split('\n'):
        line = line.strip()

        # --- Update State from Headings ---
        level_match = level_track_pattern.match(line)
        if level_match:
            current_level = level_match.group('level').strip()
            current_track = level_match.group('track').strip() if level_match.group('track') else "General"
            is_elective_table = False
            continue

        semester_match = semester_pattern.match(line)
        if semester_match:
            current_semester = semester_match.group(1).strip()
            is_elective_table = False
            continue
            
        if elective_table_pattern.match(line):
            is_elective_table = True
            continue

        # --- Parse Course Data from Table Rows ---
        if not line.startswith('|'):
            continue
            
        columns = [col.strip() for col in line.split('|')]
        if len(columns) < 4 or not columns[1]:
            continue

        code = columns[1].strip()
        if not course_code_pattern.match(code):
            continue

        course_type = "Elective" if is_elective_table else "General"
        
        # Main Course Tables (not elective section)
        if len(columns) > 8 and not is_elective_table:
            try:
                title = columns[2].strip()
                credit_hours = int(columns[5])
                prereqs_str = columns[-2]
            except (ValueError, IndexError):
                continue
        # Elective Tables
        elif len(columns) >= 4 and is_elective_table:
            try:
                title = columns[2].split('/')[0].strip()
                credit_hours = 3 # Electives are consistently 3 CH
                prereqs_str = columns[3]
            except (ValueError, IndexError):
                continue
        else:
            continue

        prerequisites = [p.strip() for p in prereqs_str.split(',') if p.strip() and p.strip() != '-']
        
        curriculum[code] = {
            "name": title,
            "credit_hours": credit_hours,
            "prerequisites": prerequisites,
            "level": current_level,
            "semester": current_semester,
            "track": current_track,
            "type": course_type
        }

    if curriculum:
        # Special manual corrections for parsing ambiguities
        if "CSD445" in curriculum:
             curriculum["CSD445"]["name"] = "Introduction to Machine Learning"
        if "BSD234" in curriculum:
             curriculum["BSD234"]["name"] = "Partial Differential Equations"
             curriculum["BSD234"]["credit_hours"] = 3
        
        output_file = 'curriculum.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(curriculum, f, indent=4, ensure_ascii=False)
        console.print(f"\n[bold green]Successfully parsed {len(curriculum)} courses with extra details![/bold green]")
        console.print(f"Curriculum data saved to [cyan]'{output_file}'[/cyan]")
    else:
        console.print("[bold red]Could not extract any curriculum data.[/bold red]")

if __name__ == "__main__":
    parse_markdown_to_json() 