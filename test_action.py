#!/usr/bin/env python3
"""
Test script to validate student data format before using the GitHub Action.
This helps users ensure their data is in the correct format.
"""

import json
import sys
import os

def validate_student_data(data):
    """Validate that the student data has the required structure."""
    required_fields = ['StudentCode', 'studentProgress']
    
    if not isinstance(data, dict):
        return False, "Data must be a JSON object"
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    if not isinstance(data['studentProgress'], list):
        return False, "studentProgress must be an array"
    
    if len(data['studentProgress']) == 0:
        return False, "studentProgress array is empty"
    
    # Check if at least one course has the required fields
    sample_course = data['studentProgress'][0]
    course_fields = ['crscode', 'crsName', 'creditv', 'yearsem']
    
    for field in course_fields:
        if field not in sample_course:
            return False, f"Course missing required field: {field}"
    
    return True, "Data format is valid!"

def main():
    print("🔍 Suez University GPA Calculator - Data Validator")
    print("=" * 50)
    print()
    
    # Check if Response.txt exists
    if os.path.exists('Response.txt'):
        print("📁 Found Response.txt file. Validating...")
        try:
            with open('Response.txt', 'r', encoding='utf-8') as f:
                content = f.read().strip()
                data = json.loads(content)
        except json.JSONDecodeError:
            print("❌ Error: Response.txt contains invalid JSON")
            return 1
        except Exception as e:
            print(f"❌ Error reading Response.txt: {e}")
            return 1
    else:
        print("📝 No Response.txt found. Please paste your JSON data below:")
        print("(Press Ctrl+D on Unix/Linux or Ctrl+Z on Windows when done)")
        print()
        
        try:
            content = sys.stdin.read().strip()
            data = json.loads(content)
        except json.JSONDecodeError:
            print("❌ Error: Invalid JSON format")
            return 1
        except KeyboardInterrupt:
            print("\n❌ Input cancelled")
            return 1
    
    # Validate the data
    is_valid, message = validate_student_data(data)
    
    if is_valid:
        print("✅ " + message)
        print()
        print("📊 Data Summary:")
        print(f"   • Student Code: {data.get('StudentCode', 'N/A')}")
        print(f"   • Total Courses: {len(data['studentProgress'])}")
        
        # Count completed courses
        completed = sum(1 for course in data['studentProgress'] 
                       if course.get('Degree') and course['Degree'].strip())
        print(f"   • Completed Courses: {completed}")
        print(f"   • In Progress: {len(data['studentProgress']) - completed}")
        print()
        print("🎉 Your data is ready for the GitHub Action!")
        print("💡 Go to the Actions tab and run the workflow with this data.")
    else:
        print("❌ " + message)
        print()
        print("🔧 Troubleshooting:")
        print("   • Make sure you copied the entire JSON response")
        print("   • Check that you're copying from the 'Response' tab, not 'Headers'")
        print("   • Ensure the JSON is not truncated")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 