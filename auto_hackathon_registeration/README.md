# HackFill ⚡

> **Fill hackathon registrations in seconds.**  
> A premium, keyboard-friendly Windows 11 desktop application designed to inspect, match, and automate hackathon registration forms with surgical precision and zero AI dependencies.

---

## 📌 Overview

**HackFill** is a developer productivity utility engineered for competitive programmers and hackathon enthusiasts. Instead of repeatedly filling out the same personal, academic, team, and essay fields across dozens of hackathon application portals, HackFill automates the process using a controlled, visible Chromium browser driven by Playwright and PySide6.

HackFill is built with an **offline-first matching engine** (strict canonical aliases, normalized token similarity, and confidence scoring) that requires **no external AI APIs, no credentials, and no subscriptions**. Your profile data never leaves your computer.

### Key Philosophy
- **Monochrome AMOLED Aesthetic**: Pure black (`#09090B`), stark white, and balanced grays. Apple-grade restraint, zero purple, zero neon gradients.
- **Safety First**: Zero blind submissions. HackFill **never** submits a form without mandatory human review and explicit user confirmation.
- **Human-in-the-Loop**: Seamlessly pauses on CAPTCHAs, OTPs, login screens, and ambiguous custom questions, allowing the user to interact in the browser and resume instantly.
- **Legal Safeguards**: Terms of Service and legal declarations are never automatically accepted without explicit checkbox confirmation.

---

## 🚀 Features

- **Visible Browser Automation**: Built on Chromium via Playwright. Watch every field populate in real time.
- **Intelligent Field Matching**:
  - Exact key matching (`name`, `email`, `phone`, `college`)
  - Extensive alias matching (`institution` → `college`, `mobileNumber` → `phone`, `github_profile` → `github`)
  - Normalized token similarity and Levenshtein distance
  - Confidence scoring: `>= 70%` automatic fill, `40%–69%` review confirmation, `< 40%` custom question prompt
- **Form Controls Supported**:
  - Text, email, telephone, number, and URL inputs
  - Multi-line textareas (essays, project descriptions, motivations)
  - Select dropdowns (matched by option label, normalized text, value, or partial match)
  - Radio button groups (gender, year, experience)
  - Checkboxes (profile preferences supported; legal declarations guarded)
- **Multi-Step Form Navigation**: Automatically detects `Next`, `Continue`, `Proceed`, `Next Step`, and `Save & Continue` controls with anti-loop state verification.
- **Custom Question Resolver**: Detects unmapped hackathon questions and presents an inline prompt for the user to answer or skip.
- **Pre-Submission Review**: A mandatory review dashboard categorizes personal info, education, team details, custom essays, and legal terms before enabling final submission.
- **Single-Click Profile Management**: Parse, validate, reload, and generate `.txt` profiles with instant syntax feedback.
- **Clean Activity Feed**: Real-time monochrome event logging with timestamped `INFO`, `SUCCESS`, `WARNING`, and `ERROR` badges.

---

## 📸 Interface Preview

```
┌────────────────────────────────────────────────────────────────────────┐
│ HACKFILL                      [ _  □  × ]                              │
│ v1.0.0 • Desktop                                                       │
├───────────────┬────────────────────────────────────────────────────────┤
│  Dashboard    │  HackFill                                              │
│  Automation   │  Fill hackathon registrations in seconds.              │
│  Review       ├────────────────────────────────────────────────────────┤
│  Profile      │  HACKATHON REGISTRATION URL                            │
│  Settings     │  [ https://hackathon.devpost.com/register            ] │
│               │                                                        │
│               │  USER PROFILE (.TXT)                                   │
│               │  [ profiles/example_profile.txt ▼ ] [ Browse ] [ View ]│
│               │                                                        │
│               │  [ START AUTOMATION ]                                  │
│               ├────────────────────────────────────────────────────────┤
│               │  [ READY ] Paste a hackathon registration URL to start │
│               ├────────────────────────────────────────────────────────┤
│               │  RECENT ACTIVITY                                       │
│               │  09:41:12 [INFO]    Opening website                    │
│               │  09:41:15 [SUCCESS] Found 14 fields                    │
│               │  09:41:18 [SUCCESS] Matched 12 fields (confidence >90%)│
└───────────────┴────────────────────────────────────────────────────────┘
```

---

## 📦 Installation & Setup

### Prerequisites
- **Windows 10 / 11** (64-bit)
- **Python 3.12+** (Python 3.12, 3.13, or 3.14)

### Step-by-Step Setup

1. **Clone or navigate to the repository**:
   ```bash
   cd auto_hackathon_registeration
   ```

2. **Create and activate a virtual environment**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install required dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Install Playwright Chromium**:
   ```powershell
   playwright install chromium
   ```

5. **Launch HackFill**:
   ```powershell
   python main.py
   ```

---

## 📄 TXT Profile Format

HackFill uses a clean, transparent key-value format in `.txt` files.

### Syntax Rules
- Lines starting with `#` are comments or section headings.
- Empty lines are ignored.
- Lines are split **only on the first `=`**; subsequent `=` characters in URLs or parameters are preserved.
- Keys are automatically normalized (case-insensitive, spaces/dashes converted to underscores).
- Duplicate keys trigger a warning and safely use the latest value.

### Standard Schema Fields

| Key | Description | Example |
| :--- | :--- | :--- |
| `name` | Full Name | `Swastik Sharma` |
| `email` | Primary Email | `swastik@example.com` |
| `phone` | Contact Number | `9876543210` |
| `college` | University / College | `National Institute of Technology` |
| `degree` | Degree Program | `B.Tech` |
| `branch` | Major / Department | `Computer Science and Engineering` |
| `year` | Year of Study | `3` |
| `graduation_year` | Expected Graduation | `2026` |
| `github` | GitHub Profile URL | `https://github.com/swastik` |
| `linkedin` | LinkedIn Profile URL | `https://linkedin.com/in/swastik` |
| `portfolio` | Personal Website | `https://swastik.dev` |
| `team_name` | Hackathon Team Name | `ByteForce` |
| `team_size` | Team Member Count | `4` |
| `skills` | Key Technologies | `Python, React, PySide6, Go` |
| `why_participate` | Motivation Essay | `I want to build real-world tools...` |
| `project_idea` | Proposed Concept | `An autonomous developer utility...` |

### Example Profile (`profiles/example_profile.txt`)
```ini
# Personal Information
name=Swastik
email=swastik@example.com
phone=9876543210
gender=Male

# Education
college=Example University
degree=B.Tech
branch=Computer Science and Engineering
year=3
graduation_year=2026

# Location
city=Bengaluru
country=India

# Online Profiles
github=https://github.com/example
linkedin=https://linkedin.com/in/example
portfolio=https://example.com

# Team Details
team_name=ByteForce
team_size=3

# Hackathon Experience & Essays
skills=Python, C++, JavaScript, React
hackathon_experience=Yes
why_participate=I want to build practical projects and collaborate with developers.
project_idea=An automated tool to streamline hackathon registration workflows.
```

---

## 🛠️ Architecture

```
auto_hackathon_registeration/
├── main.py                     # Application entrypoint
├── requirements.txt            # Minimal runtime dependencies
├── build.bat                   # PyInstaller standalone packager
├── profiles/
│   └── example_profile.txt     # Standard reference profile
├── test_pages/                 # Local test forms
│   ├── basic_form.html         # Standard text inputs
│   ├── dropdown_form.html      # Selects and radios
│   ├── multi_page_form.html    # Multi-step wizard
│   ├── custom_questions.html   # Textareas & custom essay prompts
│   └── checkbox_form.html      # Legal terms and preferences
├── tests/                      # Automated pytest suite (23 tests)
│   ├── test_profile_parser.py
│   ├── test_field_matching.py
│   ├── test_form_detection.py
│   ├── test_gui_smoke.py
│   └── test_local_forms.py
└── app/
    ├── automation/             # Playwright browser controller
    │   ├── browser.py          # Chromium lifecycle manager
    │   ├── crawler.py          # Master workflow orchestrator
    │   ├── field_matcher.py    # Match coordinator
    │   ├── form_detector.py    # DOM scanner (JS injection)
    │   ├── form_filler.py      # Input, select, radio, checkbox populator
    │   ├── human_intervention.py # CAPTCHA/OTP detector
    │   └── navigation.py       # Multi-page wizard stepper
    ├── models/                 # Pure domain dataclasses
    │   ├── form_field.py
    │   ├── profile.py
    │   └── scan_result.py
    ├── profile/                # Profile parsing & semantic validation
    │   ├── parser.py
    │   ├── schema.py
    │   └── validator.py
    ├── services/               # Cross-cutting concerns
    │   ├── logger.py           # Thread-safe Qt signal logger
    │   └── settings.py         # JSON configuration manager
    ├── ui/                     # PySide6 AMOLED monochrome desktop UI
    │   ├── components.py       # Reusable monochrome widgets & styles
    │   ├── dashboard.py        # Main launchpad
    │   ├── automation_view.py  # Real-time inspection & intervention
    │   ├── review_view.py      # Pre-submission confirmation
    │   ├── profile_view.py     # Profile editor & validator
    │   ├── settings_view.py    # Configuration controls
    │   └── main_window.py      # Host window & QThread worker
    └── utils/
        ├── helpers.py          # URL & string helpers
        └── matching.py         # Offline confidence matching engine
```

---

## 🧪 Testing

HackFill includes a comprehensive test suite of 23 unit and end-to-end tests validating:
- TXT parsing, comments, duplicates, and malformed lines
- Field alias resolution and confidence thresholds
- DOM field discovery and button classification
- Local HTML form filling across inputs, selects, radios, textareas, and checkboxes
- Multi-step page progression and loop prevention
- GUI window and tab navigation smoke tests

Run the test suite:
```powershell
.venv\Scripts\pytest -v
```

---

## 🏗️ Packaging as a Windows Executable

HackFill can be compiled into a standalone Windows executable (`HackFill.exe`) using PyInstaller:

1. Run the build script:
   ```cmd
   build.bat
   ```
2. The executable will be generated inside:
   ```
   dist\HackFill\HackFill.exe
   ```
3. Ensure Playwright's Chromium browser is installed on the target machine:
   ```cmd
   playwright install chromium
   ```

---

## 🔒 Security & Privacy

- **100% Local**: HackFill stores nothing in the cloud and never transmits your profile to external AI APIs or third-party telemetry services.
- **Zero Blind Submissions**: The application will **never** click the final submit button without showing the review screen and receiving explicit user confirmation.
- **No CAPTCHA Bypass**: HackFill does not attempt to bypass security protections. When a CAPTCHA or OTP is detected, it pauses gracefully and prompts you to complete it in the browser.
- **Guarded Legal Checkboxes**: Checkboxes containing terms of service, liability waivers, or code of conduct agreements are flagged and must be confirmed by the user.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
