import json
import os
import re
from collections import defaultdict
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# --- Utility Functions ---
def clear_console():
    """Clears the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_grade_info(degree):
    """Converts a numerical degree to a letter grade and GPA points."""
    try:
        score = float(degree)
    except (ValueError, TypeError):
        return {'letter': 'N/A', 'points': 0.0}
    if score >= 96: return {'letter': 'A+', 'points': 4.0}
    if score >= 92: return {'letter': 'A', 'points': 3.7}
    if score >= 88: return {'letter': 'A-', 'points': 3.4}
    if score >= 84: return {'letter': 'B+', 'points': 3.2}
    if score >= 80: return {'letter': 'B', 'points': 3.0}
    if score >= 76: return {'letter': 'B-', 'points': 2.8}
    if score >= 72: return {'letter': 'C+', 'points': 2.6}
    if score >= 68: return {'letter': 'C', 'points': 2.4}
    if score >= 64: return {'letter': 'C-', 'points': 2.2}
    if score >= 60: return {'letter': 'D+', 'points': 2.0}
    if score >= 55: return {'letter': 'D', 'points': 1.5}
    if score >= 50: return {'letter': 'D-', 'points': 1.0}
    return {'letter': 'F', 'points': 0.0}

# --- Data Loading and Processing ---
def load_json_data(file_path):
    """Loads data from a JSON file."""
    if not os.path.exists(file_path):
        return None, f"Error: '{file_path}' not found."
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f), None
    except json.JSONDecodeError:
        return None, f"Error: Could not decode JSON in '{file_path}'."

def process_student_data(student_response, curriculum):
    """Processes student and curriculum data to build a complete academic profile."""
    start_year_match = re.search(r'^(\d{2})', student_response.get('StudentCode', ''))
    start_year = int(f"20{start_year_match.group(1)}") if start_year_match else 2020 # Fallback

    level_map = {"First": 1, "Second": 2, "Third": 3, "Fourth": 4}
    semesters = {}
    all_attempts = defaultdict(list)  # Track all attempts for each course code
    highest_level = 0

    for course in student_response.get('studentProgress', []):
        code = course.get('crscode', '|').split('|')[0]
        is_uni_course = code.startswith('UNI-')

        # Use curriculum data for consistency, but handle if UNI course is not in our curriculum file
        course_info = curriculum.get(code)
        if not course_info:
            if is_uni_course:
                course_info = {
                    'name': (course.get('crsName', '') + '|').split('|')[1] or (course.get('crsName', '') + '|').split('|')[0],
                    'credit_hours': float(course.get('creditv') or 0),
                    'level': 'University Req.',
                    'prerequisites': []
                }
            else:
                continue

        semester_id = course.get('yearsem')
        if semester_id not in semesters:
            semesters[semester_id] = {
                'courses': [], 'total_points': 0.0, 'total_hours': 0.0, 
                'year_str': '', 'semester_name': course.get('semesterCourse', '|').split('|')[1]
            }
        
        # --- Determine course status and grade ---
        is_finished = False
        degree_display = "In Progress"
        letter_grade = "-"
        status = "In Progress"
        grade_points = 0.0

        if is_uni_course:
            grade_n = course.get('gradeN')
            if grade_n is not None and grade_n != '':
                is_finished = True
                if 'P' in grade_n.upper():
                    degree_display, letter_grade, status = "Pass", "P", "Passed"
                elif 'BF' in grade_n.upper():
                    # Show numeric degree if present, else 'BF'
                    deg_val = course.get('Degree', '')
                    degree_display = deg_val if deg_val not in (None, '', 'BF', 'bf') else 'BF'
                    letter_grade = "BF"
                    status = "Failed"
                    grade_points = 0.0
                else:
                    degree_display, letter_grade, status = "Fail", "F", "Failed"
        else: # Regular course logic
            degree_str = course.get('Degree', '')
            grade_n = course.get('gradeN', '')
            # If gradeN contains BF, always fail regardless of numeric degree
            if isinstance(grade_n, str) and 'BF' in grade_n.upper():
                is_finished = True
                # Show numeric degree if present, else 'BF'
                degree_display = degree_str if degree_str not in (None, '', 'BF', 'bf') else 'BF'
                letter_grade = "BF"
                status = "Failed"
                grade_points = 0.0
            elif isinstance(degree_str, str) and degree_str.strip().upper() == 'BF':
                is_finished = True
                degree_display = "BF"
                letter_grade = "BF"
                status = "Failed"
                grade_points = 0.0
            else:
                try:
                    degree_val = float(degree_str)
                    is_finished = True
                    grade_info = get_grade_info(degree_val)
                    letter_grade = grade_info['letter']
                    grade_points = grade_info['points']
                    degree_display = degree_str
                    status = "Passed" if grade_points > 0 else "Failed"
                except (ValueError, TypeError):
                    pass # Stays as "In Progress"

        # Store all attempts for retake logic
        all_attempts[code].append({
            'semester_id': semester_id,
            'name': course_info['name'],
            'code': code,
            'degree': degree_display,
            'letter': letter_grade,
            'hours': course_info['credit_hours'],
            'status': status,
            'is_finished': is_finished,
            'grade_points': grade_points,
            'is_uni_course': is_uni_course,
            'course_info': course_info
        })

        # Determine academic year string
        level_str = course_info.get('level', 'Unknown').split(' ')[0]
        level_ord = level_map.get(level_str, 0)
        if level_ord > 0:
            highest_level = max(highest_level, level_ord)
            year = start_year + level_ord - 1
            semesters[semester_id]['year_str'] = f"{year}/{year + 1}"
        
    # Now, for each course code, decide which attempts to count for GPA/progress
    passed_courses = set()
    for code, attempts in all_attempts.items():
        # Sort attempts by semester (assuming semester_id is sortable)
        attempts_sorted = sorted(attempts, key=lambda x: x['semester_id'])
        # Add all attempts to their respective semesters for display
        for att in attempts_sorted:
            if not att['is_uni_course'] and not att['is_finished'] and att['status'] == 'In Progress':
                # Only show registered/in-progress if not finished
                course_obj = att.copy()
                semesters[att['semester_id']]['courses'].append(course_obj)
            elif att['is_finished'] or att['status'] != 'In Progress':
                semesters[att['semester_id']]['courses'].append(att.copy())
        # Only the latest passing attempt counts for progress and GPA
        latest_pass = None
        for att in reversed(attempts_sorted):
            if att['is_finished'] and att['status'] == 'Passed':
                latest_pass = att
                break
        if latest_pass:
            passed_courses.add(code)
        # For GPA, only count the latest finished attempt (even if failed)
        latest_finished = None
        for att in reversed(attempts_sorted):
            if att['is_finished'] and not att['is_uni_course']:
                latest_finished = att
                break
        if latest_finished:
            sem = semesters[latest_finished['semester_id']]
            sem['total_points'] += latest_finished['grade_points'] * latest_finished['hours']
            sem['total_hours'] += latest_finished['hours']

    return semesters, passed_courses, highest_level, None

# --- Display Functions ---
def display_semester(console, semester_data, semester_name):
    """Displays a formatted table for a single semester."""
    table = Table(title=f"📚 {semester_name}", title_style="bold green", show_header=True, header_style="bold magenta")
    table.add_column("Course Name", style="cyan", no_wrap=True, width=40)
    table.add_column("Code", style="white")
    table.add_column("Credit Hours", justify="right", style="yellow")
    table.add_column("Numeric Degree", justify="right", style="green")
    table.add_column("Letter Grade", justify="right", style="blue")
    table.add_column("Status", style="white")
    
    for c in sorted(semester_data['courses'], key=lambda x: x['code']):
        grade_color = "red" if c['letter'] == 'F' else "blue"
        status_color = "green" if c['status'] == "Passed" else "yellow"
        table.add_row(
            c['name'], c['code'], f"{c['hours']:.1f}", str(c['degree']),
            f"[{grade_color}]{c['letter']}[/{grade_color}]",
            f"[{status_color}]{c['status']}[/{status_color}]"
        )
    
    console.print(table)
    
    # Display Semester GPA in a formatted table
    gpa = (semester_data['total_points'] / semester_data['total_hours']) if semester_data['total_hours'] > 0 else 0
    gpa_table = Table(show_header=False, show_edge=False, box=None, padding=(0, 1))
    gpa_table.add_column(style="bold")
    gpa_table.add_column(style="bold cyan", justify="right")
    gpa_table.add_row("Semester GPA:", f"{gpa:.2f}")
    console.print(Panel(gpa_table, title="[bold]Semester Summary[/bold]", border_style="blue", expand=False))
    console.print() # Add a newline for spacing

def display_all_semesters(console, semesters):
    """Displays all semesters sorted by time."""
    if not semesters:
        console.print("[bold red]No semester data to display.[/bold red]")
        return
        
    sorted_semesters = sorted(semesters.items(), key=lambda x: x[0] if x[0] is not None else 0)
    for sem_id, sem_data in sorted_semesters:
        display_semester(console, sem_data, f"{sem_data['year_str']} - {sem_data['semester_name']}")

def display_cumulative_gpa(console, semesters):
    """Calculates and displays the cumulative GPA."""
    total_points = sum(s['total_points'] for s in semesters.values())
    total_hours = sum(s['total_hours'] for s in semesters.values())
    gpa = (total_points / total_hours) if total_hours > 0 else 0
    
    console.print(Panel(f"[bold cyan]🏆 Cumulative GPA: {gpa:.2f}[/bold cyan]", title="Overall Result", border_style="bold blue"))

def display_progress_report(console, curriculum, passed_courses):
    console.print(Panel("[bold cyan]Degree Progress Report[/bold cyan]", border_style="blue"))
    
    total_hours = sum(c['credit_hours'] for c in curriculum.values())
    completed_hours = sum(curriculum[c]['credit_hours'] for c in passed_courses if c in curriculum)
    
    console.print(f"[bold]Credit Hours:[/bold] {completed_hours} / {total_hours} ({completed_hours/total_hours:.1%}) Completed\n")
    
    remaining_courses = {code: data for code, data in curriculum.items() if code not in passed_courses}
    
    table = Table(title="Remaining Courses", title_style="bold yellow")
    table.add_column("Code", style="white")
    table.add_column("Course Name", style="cyan", width=40)
    table.add_column("Hours", style="yellow")
    table.add_column("Prerequisites Met?", style="white")

    for code, data in sorted(remaining_courses.items(), key=lambda item: (item[1]['level'], item[1]['semester'])):
        prereqs_met = all(p in passed_courses for p in data['prerequisites'])
        status_str = "[green]Yes[/green]" if prereqs_met else "[red]No[/red]"
        table.add_row(code, data['name'], str(data['credit_hours']), status_str)
    
    console.print(table)

def get_pasted_data(console):
    """Prompts the user to paste JSON data and parses it."""
    console.print(
        Panel(
            "[bold yellow]Please paste the JSON content from the student portal below.[/bold yellow]\n\n"
            "[dim]On Windows, right-click to paste. On macOS/Linux, use standard paste shortcuts.\n"
            "After pasting, press ESC and then Enter to submit.[/dim]",
            title="[bold]Awaiting Student Data[/bold]",
            border_style="blue"
        )
    )
    
    json_input = questionary.text(
        "Paste your JSON here:",
        multiline=True
    ).ask()

    if not json_input:
        return None, "No data was pasted."

    try:
        data = json.loads(json_input)
        return data, None
    except json.JSONDecodeError:
        return None, "Error: Invalid JSON format. Please make sure you copied the entire content correctly."

# --- Hardcoded Curricula ---
COMPUTER_SCIENCE_CURRICULUM = {
     "BSD101": {
        "name": "Calculus",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "First Level",
        "semester": "1st Semester",
        "track": "General",
        "type": "General"
    },
    "BSD103": {
        "name": "Discrete Mathematics",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "First Level",
        "semester": "1st Semester",
        "track": "General",
        "type": "General"
    },
    "CSD102": {
        "name": "Basics of Computer Science",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "First Level",
        "semester": "1st Semester",
        "track": "General",
        "type": "General"
    },
    "ISD101": {
        "name": "Fundamentals of Information Systems",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "First Level",
        "semester": "1st Semester",
        "track": "General",
        "type": "General"
    },
    "ISD102": {
        "name": "Introduction to Database Systems",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "First Level",
        "semester": "1st Semester",
        "track": "General",
        "type": "General"
    },
    "BSD104": {
        "name": "Linear Algebra",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "First Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "General"
    },
    "BSD105": {
        "name": "Statistics and Probabilities",
        "credit_hours": 3,
        "prerequisites": [
            "BSD101"
        ],
        "level": "First Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "General"
    },
    "BSD226": {
        "name": "Technical Writing",
        "credit_hours": 2,
        "prerequisites": [],
        "level": "First Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "General"
    },
    "CSD101": {
        "name": "Digital Logic Design",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "First Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "General"
    },
    "CSD106": {
        "name": "Fundamentals of Programming",
        "credit_hours": 3,
        "prerequisites": [
            "CSD102"
        ],
        "level": "First Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "General"
    },
    "ISD104": {
        "name": "System Analysis and Design",
        "credit_hours": 3,
        "prerequisites": [
            "ISD102"
        ],
        "level": "First Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "General"
    },
    "BSD220": {
        "name": "Stochastic Process",
        "credit_hours": 3,
        "prerequisites": [
            "BSD105"
        ],
        "level": "Second Level",
        "semester": "1st Semester",
        "track": "General",
        "type": "General"
    },
    "BSD222": {
        "name": "Operations Research",
        "credit_hours": 3,
        "prerequisites": [
            "BSD101",
            "BSD104"
        ],
        "level": "Second Level",
        "semester": "1st Semester",
        "track": "General",
        "type": "General"
    },
    "CSD221": {
        "name": "Data Structures",
        "credit_hours": 3,
        "prerequisites": [
            "CSD106"
        ],
        "level": "Second Level",
        "semester": "1st Semester",
        "track": "General",
        "type": "General"
    },
    "CSD223": {
        "name": "Object-Oriented Programming",
        "credit_hours": 3,
        "prerequisites": [
            "CSD106"
        ],
        "level": "Second Level",
        "semester": "1st Semester",
        "track": "General",
        "type": "General"
    },
    "ISD224": {
        "name": "Web Pages Programming",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "Second Level",
        "semester": "1st Semester",
        "track": "General",
        "type": "General"
    },
    "BSD227": {
        "name": "Ordinary Differential Equations",
        "credit_hours": 3,
        "prerequisites": [
            "BSD101"
        ],
        "level": "Second Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "General"
    },
    "BSD228": {
        "name": "Advanced Math",
        "credit_hours": 3,
        "prerequisites": [
            "BSD101"
        ],
        "level": "Second Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "General"
    },
    "BSD232": {
        "name": "Physics",
        "credit_hours": 2,
        "prerequisites": [
            "CSD101"
        ],
        "level": "Second Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "General"
    },
    "CSD230": {
        "name": "Analysis of Algorithms",
        "credit_hours": 3,
        "prerequisites": [
            "CSD221"
        ],
        "level": "Second Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "General"
    },
    "ISD229": {
        "name": "Electronic Business",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "Second Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "General"
    },
    "ISD225": {
        "name": "Information Theory",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "Second Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "Elective"
    },
    "CSD231": {
        "name": "Concepts of Programming Languages",
        "credit_hours": 3,
        "prerequisites": [
            "CSD106"
        ],
        "level": "Second Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "Elective"
    },
    "ISD232": {
        "name": "Web Technology",
        "credit_hours": 3,
        "prerequisites": [
            "ISD224"
        ],
        "level": "Second Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "Elective"
    },
    "BSD233": {
        "name": "Numerical Analysis",
        "credit_hours": 3,
        "prerequisites": [
            "BSD101"
        ],
        "level": "Second Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "Elective"
    },
    "BSD229": {
        "name": "Advanced Math-2",
        "credit_hours": 3,
        "prerequisites": [
            "BSD228"
        ],
        "level": "Second Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "Elective"
    },
    "BSD234": {
        "name": "Partial Differential Equations",
        "credit_hours": 3,
        "prerequisites": [
            "BSD101"
        ],
        "level": "Second Level",
        "semester": "2nd Semester",
        "track": "General",
        "type": "Elective"
    },
    "CSD331": {
        "name": "Artificial Intelligence",
        "credit_hours": 3,
        "prerequisites": [
            "CSD230"
        ],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "CSD332": {
        "name": "Computer Architecture",
        "credit_hours": 3,
        "prerequisites": [
            "CSD101"
        ],
        "level": "Third Level",
        "semester": "1st Semester",
        "track": "Computer Science",
        "type": "General"
    },
    "CSD333": {
        "name": "Operating Systems",
        "credit_hours": 3,
        "prerequisites": [
            "CSD230"
        ],
        "level": "Third Level",
        "semester": "1st Semester",
        "track": "Computer Science",
        "type": "General"
    },
    "CSD334": {
        "name": "Digital Image Processing",
        "credit_hours": 3,
        "prerequisites": [
            "BSD104",
            "CSD230"
        ],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "Elective"
    },
    "CSD335": {
        "name": "Assembly Language",
        "credit_hours": 2,
        "prerequisites": [
            "CSD101"
        ],
        "level": "Third Level",
        "semester": "1st Semester",
        "track": "Computer Science",
        "type": "General"
    },
    "CSD336": {
        "name": "Theory and Design of Compilers",
        "credit_hours": 3,
        "prerequisites": [
            "CSD231"
        ],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "General"
    },
    "CSD337": {
        "name": "Computer Graphics",
        "credit_hours": 3,
        "prerequisites": [
            "CSD230"
        ],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "General"
    },
    "CSD338": {
        "name": "Introduction to Computer Networks",
        "credit_hours": 3,
        "prerequisites": [
            "CSD332"
        ],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "General"
    },
    "CSD341": {
        "name": "Software Engineering",
        "credit_hours": 3,
        "prerequisites": [
            "ISD104"
        ],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "CSD340": {
        "name": "Simulation and Modeling",
        "credit_hours": 3,
        "prerequisites": [
            "BSD105"
        ],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "General"
    },
    "CSD342": {
        "name": "Advanced Programming Languages",
        "credit_hours": 3,
        "prerequisites": [
            "CSD223"
        ],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "Elective"
    },
    "ISD303": {
        "name": "Information Visualization",
        "credit_hours": 3,
        "prerequisites": [
            "ISD101"
        ],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "Elective"
    },
    "CSD343": {
        "name": "Digital Signal Processing",
        "credit_hours": 3,
        "prerequisites": [
            "CSD230"
        ],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "Elective"
    },
    "CSD344": {
        "name": "Logic Programming",
        "credit_hours": 3,
        "prerequisites": [
            "CSD335"
        ],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "Elective"
    },
    "ISD352": {
        "name": "Knowledge Representation & Reasoning",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "Elective"
    },
    "CSD339": {
        "name": "Mobile Computing",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "Third Level",
        "semester": "1st Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "CSD345": {
        "name": "Computer Arabization",
        "credit_hours": 3,
        "prerequisites": [
            "CSD106"
        ],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "Elective"
    },
    "ISD335": {
        "name": "Security and Cryptography",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "Elective"
    },
    "CSD346": {
        "name": "Human Computer Interaction",
        "credit_hours": 3,
        "prerequisites": [
            "CSD106"
        ],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "Elective"
    },
    "ISD347": {
        "name": "Computer Network Management",
        "credit_hours": 3,
        "prerequisites": [
            "ISD104"
        ],
        "level": "Third Level",
        "semester": "1st Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "ISD331": {
        "name": "Information Retrieval Systems",
        "credit_hours": 3,
        "prerequisites": [
            "ISD104"
        ],
        "level": "Third Level",
        "semester": "1st Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "ISD333": {
        "name": "Decision Support Systems",
        "credit_hours": 3,
        "prerequisites": [
            "ISD104"
        ],
        "level": "Third Level",
        "semester": "1st Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "ISD338": {
        "name": "Big Data Analysis",
        "credit_hours": 3,
        "prerequisites": [
            "ISD104"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "Elective"
    },
    "ISD336": {
        "name": "Advanced Database Systems",
        "credit_hours": 3,
        "prerequisites": [
            "ISD102"
        ],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "ISD337": {
        "name": "Information Security",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "ISD365": {
        "name": "Electronic Government",
        "credit_hours": 2,
        "prerequisites": [],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "ISD334": {
        "name": "Management Information Systems",
        "credit_hours": 3,
        "prerequisites": [
            "ISD101"
        ],
        "level": "Third Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "Elective"
    },
    "CSD441": {
        "name": "Mobile Communication Systems",
        "credit_hours": 3,
        "prerequisites": [
            "CSD338"
        ],
        "level": "Fourth Level",
        "semester": "1st Semester",
        "track": "Computer Science",
        "type": "General"
    },
    "CSD444": {
        "name": "Distributed Systems",
        "credit_hours": 3,
        "prerequisites": [
            "CSD333"
        ],
        "level": "Fourth Level",
        "semester": "1st Semester",
        "track": "Computer Science",
        "type": "General"
    },
    "CSD443": {
        "name": "Computer Vision Systems",
        "credit_hours": 3,
        "prerequisites": [
            "CSD334"
        ],
        "level": "Fourth Level",
        "semester": "1st Semester",
        "track": "Computer Science",
        "type": "General"
    },
    "CSD449": {
        "name": "Graduation Project",
        "credit_hours": 3,
        "prerequisites": [
            "CSD449 (1st Sem)"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "General"
    },
    "CSD451": {
        "name": "Computer and Network Security",
        "credit_hours": 3,
        "prerequisites": [
            "CSD332"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "General"
    },
    "CSD447": {
        "name": "Cloud Computing",
        "credit_hours": 3,
        "prerequisites": [
            "CSD444"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "General"
    },
    "CSD442": {
        "name": "Neural Networks and Deep Learning",
        "credit_hours": 3,
        "prerequisites": [
            "CSD331"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "General"
    },
    "CSD452": {
        "name": "Dynamic Languages",
        "credit_hours": 3,
        "prerequisites": [
            "CSD106"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "Elective"
    },
    "ISD471": {
        "name": "Data Mining",
        "credit_hours": 3,
        "prerequisites": [
            "ISD102"
        ],
        "level": "Fourth Level",
        "semester": "1st Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "CSD453": {
        "name": "Introduction to Quantum Computing",
        "credit_hours": 3,
        "prerequisites": [
            "BSD228"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "Elective"
    },
    "CSD458": {
        "name": "Cyber Security",
        "credit_hours": 3,
        "prerequisites": [
            "ISD337"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "ISD441": {
        "name": "Bioinformatics",
        "credit_hours": 3,
        "prerequisites": [
            "ISD102"
        ],
        "level": "Fourth Level",
        "semester": "1st Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "CSD446": {
        "name": "Optimization Systems",
        "credit_hours": 3,
        "prerequisites": [
            "CSD331"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "Elective"
    },
    "CSD448": {
        "name": "Parallel Processing",
        "credit_hours": 3,
        "prerequisites": [
            "CSD333"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Computer Science",
        "type": "Elective"
    },
    "CSD445": {
        "name": "Introduction to Machine Learning",
        "credit_hours": 3,
        "prerequisites": [
            "CSD331"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "ISD444": {
        "name": "Medical Information Systems",
        "credit_hours": 3,
        "prerequisites": [
            "ISD101"
        ],
        "level": "Fourth Level",
        "semester": "1st Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "ISD446": {
        "name": "Graduation Project",
        "credit_hours": 3,
        "prerequisites": [
            "ISD446 (1st Sem)"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "ISD445": {
        "name": "Geographical Information Systems",
        "credit_hours": 3,
        "prerequisites": [
            "ISD334"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "General"
    },
    "ISD451": {
        "name": "XML Databases",
        "credit_hours": 3,
        "prerequisites": [
            "ISD102"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "Elective"
    },
    "ISD453": {
        "name": "Web Information Systems",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "Elective"
    },
    "ISD456": {
        "name": "Quantum Information",
        "credit_hours": 3,
        "prerequisites": [
            "BSD228"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "Elective"
    },
    "ISD455": {
        "name": "Electronic Health",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "Elective"
    },
    "ISD452": {
        "name": "Electronic Commerce",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "Elective"
    },
    "ISD454": {
        "name": "Cloud Computing Applications",
        "credit_hours": 3,
        "prerequisites": [
            "ISD332"
        ],
        "level": "Fourth Level",
        "semester": "2nd Semester",
        "track": "Information Systems",
        "type": "Elective"
    }
}

ENGINEERING_CURRICULUM = {
    # Placeholder for Engineering curriculum
    "ENG101": {
        "name": "Engineering Placeholder Course",
        "credit_hours": 3,
        "prerequisites": [],
        "level": "First Level",
        "semester": "1st Semester",
        "track": "General",
        "type": "General"
    }
}

# --- Main Application ---
def main():
    console = Console()
    
    # Faculty selection
    faculty_choice = questionary.select(
        "Select your faculty:",
        choices=[
            "Faculty of Computer Science and Informatics",
            "Faculty of Engineering"
        ]
    ).ask()

    if faculty_choice == "Faculty of Computer Science and Informatics":
        curriculum = COMPUTER_SCIENCE_CURRICULUM
    else:
        curriculum = ENGINEERING_CURRICULUM

    # Check if running in a non-interactive CI environment
    is_ci = os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'

    if is_ci:
        # Non-interactive mode for GitHub Actions
        console.print("[dim]CI environment detected. Running in non-interactive mode...[/dim]")
        student_response, error = load_json_data('Response.txt')
        if error:
            console.print(f"[bold red]{error}[/bold red]"); return

        semesters, passed, level, error = process_student_data(student_response, curriculum)
        if error:
            console.print(f"[bold red]{error}[/bold red]"); return
            
        # Print all reports
        console.print(Panel("[bold cyan]Full Academic Report[/bold cyan]", border_style="green", expand=False))
        display_all_semesters(console, semesters)
        display_cumulative_gpa(console, semesters)
        display_progress_report(console, curriculum, passed)
        console.print("\n[green]✅ Report generation complete.[/green]")

    else:
        # Interactive mode for local execution
        student_response, error = get_pasted_data(console)
        if error:
            console.print(f"[bold red]{error}[/bold red]")
            return

        semesters, passed, level, error = process_student_data(student_response, curriculum)
        if error:
            console.print(f"[bold red]{error}[/bold red]"); return

        while True:
            clear_console()
            console.print(Panel("[bold cyan]Student GPA & Progress Advisor[/bold cyan]", border_style="green"))
            
            choice = questionary.select(
                "What would you like to do?",
                choices=[
                    "View My Degree Progress",
                    "View Report for a Specific Semester",
                    "View Full GPA Report (All Semesters)",
                    "Show Cumulative GPA Only",
                    "Paste New Data",
                    "Exit"
                ]
            ).ask()

            if choice == "View My Degree Progress":
                display_progress_report(console, curriculum, passed)
            elif choice == "View Full GPA Report (All Semesters)":
                if semesters:
                    display_all_semesters(console, semesters)
            
            elif choice == "View Report for a Specific Semester":
                if not semesters:
                    console.print("[yellow]No semesters available to select.[/yellow]")
                    continue
                
                semester_choices = {f"{s['year_str']} - {s['semester_name']}": sid for sid, s in semesters.items() if sid is not None}
                if not semester_choices:
                    console.print("[yellow]No semesters available to select.[/yellow]")
                    continue
                
                selected_semester_name = questionary.select(
                    "Choose a semester:",
                    choices=list(semester_choices.keys())
                ).ask()
                
                if selected_semester_name:
                    selected_id = semester_choices[selected_semester_name]
                    display_semester(console, semesters[selected_id], selected_semester_name)

            elif choice == "Show Cumulative GPA Only":
                if semesters:
                    display_cumulative_gpa(console, semesters)
            
            elif choice == "Paste New Data":
                student_response, error = get_pasted_data(console)
                if error:
                    console.print(f"[bold red]{error}[/bold red]")
                    console.print("[bold yellow]Continuing with previous data.[/bold yellow]")
                else:
                    semesters, passed, level, error = process_student_data(student_response, curriculum)
                    if error:
                        console.print(f"[bold red]{error}[/bold red]")
                        console.print("[bold yellow]Could not process new data, reverting to previous data.[/bold yellow]")
                    else:
                        console.print(f"[green]Successfully loaded new pasted data.[/green]")

            elif choice == "Exit" or choice is None:
                break
            
            if choice != "Exit":
                questionary.press_any_key_to_continue().ask()

if __name__ == "__main__":
    main() 