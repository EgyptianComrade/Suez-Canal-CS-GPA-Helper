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

# --- Software Engineering Grading Scheme ---
SOFTWARE_ENG_GPA_MAP = [
    (95, 100, 3.7, 4.0, 'A+'),
    (90, 95, 3.4, 3.7, 'A'),
    (85, 90, 3.1, 3.4, 'A-'),
    (80, 85, 2.8, 3.1, 'B+'),
    (75, 80, 2.5, 2.8, 'B'),
    (70, 75, 2.2, 2.5, 'C+'),
    (65, 70, 1.9, 2.2, 'C'),
    (60, 65, 1.6, 1.9, 'D+'),
    (50, 60, 1.0, 1.6, 'D'),
    (0, 50, 0.0, 0.0, 'F'),
]
def get_grade_info_software_eng(degree):
    """Converts a numerical degree to a letter grade and GPA points for Software Engineering branch using the provided mapping."""
    try:
        score = float(degree)
    except (ValueError, TypeError):
        return {'letter': 'N/A', 'points': 0.0}
    for lower, upper, gpa_min, gpa_max, letter in SOFTWARE_ENG_GPA_MAP:
        if lower <= score < upper or (upper == 100 and score == 100):
            # Linear interpolation within the range
            if gpa_min == gpa_max:
                gpa = gpa_min
            else:
                gpa = gpa_min + (gpa_max - gpa_min) * (score - lower) / (upper - lower)
            return {'letter': letter, 'points': round(gpa, 2)}
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

def process_student_data(student_response, curriculum, branch=None):
    """Processes student and curriculum data to build a complete academic profile."""
    start_year_match = re.search(r'^(\d{2})', student_response.get('StudentCode', ''))
    start_year = int(f"20{start_year_match.group(1)}") if start_year_match else 2020 # Fallback

    level_map = {"First": 1, "Second": 2, "Third": 3, "Fourth": 4}
    semesters = {}
    all_attempts = defaultdict(list)  # Track all attempts for each course code
    highest_level = 0

    for course in student_response.get('studentProgress', []):
        code = course.get('crscode', '|').split('|')[0]
        # Normalize code for Software Engineering branch only
        if branch == "Software Engineering":
            code = code.replace('-', '')
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
                    degree_display, letter_grade, status = "Passed", "P", "Passed"  # Show 'Passed' as degree
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
                    # Use the correct grading scheme for GPA calculation
                    if branch == "Software Engineering":
                        grade_info = get_grade_info_software_eng(degree_val)
                    else:
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
        # For GPA, only count the latest finished attempt (even if failed), and skip UNI courses
        latest_finished = None
        for att in reversed(attempts_sorted):
            if att['is_finished'] and not att['is_uni_course']:
                latest_finished = att
                break
        if latest_finished and not latest_finished['is_uni_course']:
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
    
    if total_hours == 0:
        console.print("[bold red]No curriculum credit hours found. Please check your curriculum data.[/bold red]")
        return
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

def load_curriculums():
    """Loads all curricula from curriculums.json."""
    with open('curriculums.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def flatten_se_curriculum(json_data):
    """Flattens the nested Software Engineering curriculum JSON into a flat dict like the General curriculum, including both dashed and non-dashed codes as keys."""
    flat = {}
    for level, semesters in json_data.items():
        if not isinstance(semesters, dict):
            continue
        for semester, courses in semesters.items():
            if not isinstance(courses, list):
                continue
            for course in courses:
                code = course['code']
                flat[code] = {
                    'name': course['name'],
                    'credit_hours': course.get('credit_hours', 3),
                    'prerequisites': course.get('prerequisites', []),
                    'level': course['level'],
                    'semester': course['semester'],
                    'track': course.get('type', 'General'),
                    'type': course.get('type', 'General')
                }
                # Also add a version with dashes if not present
                if '-' not in code:
                    dashed_code = code[:3] + '-' + code[3:] if len(code) > 3 else code
                    flat[dashed_code] = flat[code]
                else:
                    nodash_code = code.replace('-', '')
                    flat[nodash_code] = flat[code]
    return flat

# --- Main Application ---
def main():
    console = Console()
    curriculums = load_curriculums()
    
    # Faculty selection
    faculty_choice = questionary.select(
        "Select your faculty:",
        choices=[
            "Faculty of Computer Science and Informatics",
            questionary.Choice("Faculty of Engineering (Coming Soon!)", disabled="Not available yet")
        ]
    ).ask()

    if faculty_choice == "Faculty of Computer Science and Informatics":
        # Branch selection for Computer Science
        branch_choice = questionary.select(
            "Select your branch:",
            choices=[
                "General",
                "Software Engineering",
                questionary.Choice("Artificial Intelligence (Coming Soon!)", disabled="Not available yet")
            ]
        ).ask()
        
        if branch_choice == "General":
            curriculum = curriculums["General"]
            grade_info_func = get_grade_info
        elif branch_choice == "Software Engineering":
            curriculum = flatten_se_curriculum(curriculums["SoftwareEngineering"]["curriculum"])
            grade_info_func = get_grade_info_software_eng
    else:
        curriculum = curriculums["General"]
        grade_info_func = get_grade_info

    # Check if running in a non-interactive CI environment
    is_ci = os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'

    if is_ci:
        # Non-interactive mode for GitHub Actions
        console.print("[dim]CI environment detected. Running in non-interactive mode...[/dim]")
        student_response, error = load_json_data('Response.txt')
        if error:
            console.print(f"[bold red]{error}[/bold red]"); return

        semesters, passed, level, error = process_student_data(student_response, curriculum, branch_choice)
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

        semesters, passed, level, error = process_student_data(student_response, curriculum, branch_choice)
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
                    semesters, passed, level, error = process_student_data(student_response, curriculum, branch_choice)
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