# Suez University GPA & Progress Advisor

A powerful, interactive command-line tool designed for students at Suez University to calculate their GPA and track their academic progress against their official curriculum.

This tool reads the JSON data available from the student portal and provides a detailed, color-coded report including:
-   GPA for each semester.
-   A cumulative GPA.
-   A full degree progress report showing completed and remaining courses.
-   A prerequisite check for all remaining courses.

## 🌐 Live Website

**Visit our user-friendly website:** [https://egyptiancomrade.github.io/Suez-Canal-CS-GPA-Helper/](https://egyptiancomrade.github.io/Suez-Canal-CS-GPA-Helper/)

The website provides step-by-step instructions and a beautiful interface to guide you through using the tool.

## 🚀 Quick Start (No Download Required!)

You can use this tool directly on GitHub without downloading anything! Here's how:

1. **Go to the Actions tab** on this repository: [Actions](https://github.com/EgyptianComrade/Suez-Canal-CS-GPA-Helper/actions)
2. **Click on "Run GPA & Progress Advisor"** in the left sidebar
3. **Click the "Run workflow" button** (blue button)
4. **Paste your student data** in the input field (see instructions below for getting this data)
5. **Click "Run workflow"** and wait for the results!

The tool will automatically run and show you your complete academic report in the workflow output.

## 📋 How to Get Your Student Data

**To get your student response data:**

1.  Log in to the Suez University student portal: `http://credit.suez.edu.eg/static/PortalStudent.html#`
2.  Open the Developer Tools in your browser (usually by pressing `F12` or `Ctrl+Shift+I`).
3.  Go to the **Network** tab.
4.  Navigate to the "Student Academic Register" page or any page that triggers a request to the `getJCI` endpoint.
5.  Find the network request named `getJCI` in the list, click on it.
6.  Go to the **Response** tab.
7.  Copy the **entire** JSON content.
8.  Paste this content into the GitHub Action input field.

**💡 Pro Tip:** Before using the GitHub Action, you can test your data locally to make sure it's in the correct format:

```bash
python test_action.py
```

This will validate your data and show you a summary before you use the GitHub Action.

## Features

-   **Interactive Menu:** A clean, easy-to-use menu to navigate through different reports.
-   **Detailed GPA Reports:** View your GPA for specific semesters or see a full report.
-   **Degree Progress Tracking:** Compares your completed courses against the official curriculum to show you exactly what's left.
-   **Prerequisite Checking:** Instantly see if you are eligible to take your remaining courses.
-   **Pass/Fail Course Handling:** Correctly identifies and displays University Requirement (`UNI-`) courses without affecting your GPA.
-   **Polished Output:** Uses modern, rich-text tables for a clear and professional-looking report.
-   **GitHub Action:** Run the tool directly on GitHub without any downloads!
-   **Data Validation:** Test your data format before using the tool.

## 🛠️ Local Installation (Optional)

If you prefer to run the tool locally, follow these steps:

### 1. Installation

First, clone the repository to your local machine and navigate into the project directory:

```bash
git clone https://github.com/EgyptianComrade/Suez-Canal-CS-GPA-Helper.git
cd Suez-Canal-CS-GPA-Helper
```

Next, install the required Python packages:

```bash
pip install -r requirements.txt
```

### 2. Getting Your Academic Data

This tool requires two data files to run: `Response.txt` (your personal academic record) and `curriculum.json` (the official degree plan).

**To get your `Response.txt`:**

Follow the same steps as above to get your student data, then:
1. Create a new file named `Response.txt` in the project directory
2. Paste the copied JSON content into it

**To generate the `curriculum.json`:**

If the `curriculum.json` is not already present, you can generate it from the `meh.txt` file (which contains the full curriculum in markdown).

```bash
python build_curriculum.py
```

### 3. Running the Advisor

Once the setup is complete, you can run the main application:

```bash
python gpa_calculator.py
```

You will be greeted with an interactive menu to explore your academic progress.

## 📊 Sample Output

The tool provides comprehensive reports including:

- **Semester-by-semester breakdown** with individual course grades
- **Cumulative GPA calculation**
- **Degree progress percentage** with remaining courses
- **Prerequisite status** for upcoming courses
- **Color-coded status indicators** for easy reading

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## ⚠️ Disclaimer

This tool is designed to help students track their academic progress at Suez University. While every effort has been made to ensure accuracy, please verify all calculations with your official university records. This tool is not affiliated with Suez University and should not replace official academic advising.
