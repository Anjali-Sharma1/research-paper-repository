# RPRMS — Research Paper Repository Management System

An enterprise-grade, role-based research paper repository and peer-review management platform built with Python, Streamlit, and MySQL / SQLite.

---

## 🌟 Key Features & Completed Modules

| Order | Module | Status | Highlights |
| :---: | :--- | :---: | :--- |
| **1** | **Project Foundation & Database** | ✅ Complete | Clean modular architecture, MySQL support with seamless SQLite automatic fallback, unified schema, `.env` configuration. |
| **2** | **Authentication & Session** | ✅ Complete | Secure login, session state persistence, Bcrypt password hashing, session timeout, role checking. |
| **3** | **User & Department Management** | ✅ Complete | Full CRUD for users & departments, student self-registration, role hierarchy (`admin`, `faculty`, `student`). |
| **4** | **Role-Based Dashboards** | ✅ Complete | Modern themed dashboards for Admin, Faculty, and Students featuring real-time KPI cards, SVG charts, and activity summaries. |
| **5** | **Paper Upload & Metadata** | ✅ Complete | PDF upload validation, file size limits, comprehensive metadata capture, and automatic Paper ID formatting (`RPRMS-YYYY-XXXX`). |
| **6** | **Paper Approval Workflow** | ✅ Complete | Submission by faculty, Admin review queue, Approve / Reject / Request Changes actions, and immutable status audit trails. |
| **7** | **Paper Version Management** | ✅ Complete | Iterative revision uploads (v1, v2, ...), changelog notes, version history tracking, and archive preservation. |
| **8** | **Search & Paper Discovery** | ✅ Complete | Multi-attribute search across title, abstract, keywords, author, and research area; filter by department, year, and paper type. |
| **9** | **Bookmark & Download Tracking** | ✅ Complete | Personal bookmarking for students and faculty, secure PDF downloads, and real-time download count tracking. |
| **10** | **Analytics & Reports** | ✅ Complete | Most downloaded papers, monthly submission trends, department-wise publication metrics, and status distribution breakdown. |
| **11** | **Activity Logs & Notifications** | ✅ Complete | Audit trails for logins and actions, system notifications with unread counts, and mark-as-read controls. |
| **12** | **QR Code & Final Features** | ✅ Complete | Auto-generated QR codes encoding direct URLs (`?paper_id=...`), mobile scanner routing, QR regeneration, and PNG downloads. |
| **13** | **Integration & Testing** | ✅ Complete | End-to-end integration across all user journeys, database connection diagnostics (`test_connection.py`). |
| **14** | **Deployment Preparation** | ✅ Complete | Sanitized `.env.example`, `.gitignore`, standardized `requirements.txt`, and zero-dependency PDF generation fallback. |

---

## 🚀 Quick Start Guide

### 1. Prerequisites & Environment Setup
Clone or navigate to the repository directory:
```bash
cd rprms_app
```

Create a virtual environment and activate it:
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

### 2. Database Setup (Zero Config Out-of-the-Box)
The application includes a dual-mode database adapter (`database/connection.py`):
1. **SQLite (Default / Zero-Config):** A pre-seeded SQLite database (`database/rprms.db`) is already included! You can launch the app immediately without installing or configuring MySQL.
2. **MySQL (Production / Enterprise):** If you wish to use MySQL, configure your credentials in `.env` (refer to `.env.example`). If MySQL is reachable, the application will automatically connect to it.

To test your database connectivity at any time:
```bash
python test_connection.py
```

### 3. Load Sample Data (Optional)
To populate the repository with 100 realistic research papers across various academic fields with auto-generated PDFs and QR codes:
```bash
python scripts/seed_sample_data.py
```

### 4. Run the Application
Launch the Streamlit app:
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 🔑 Default Credentials

| Role | Email | Password |
| :--- | :--- | :--- |
| **Admin** | `admin@rprms.edu` | `Admin@123` |
| **Faculty** | `faculty@rprms.edu` | `Faculty@123` |
| **Student** | `student@rprms.edu` | `Student@123` |

*(New students can also register directly using the "Register as Student" link on the login page.)*

---

## 📁 Project Structure

```
rprms_app/
├── app.py                      # Main Streamlit application entry point & router
├── requirements.txt            # Python dependencies
├── test_connection.py          # Database diagnostic & connectivity test script
├── .env                        # Local environment variables
├── .env.example                # Template environment variables
├── .gitignore                  # Git ignore rules
│
├── auth/                       # Authentication and authorization
│   ├── login.py                # Login page UI & controller
│   ├── logout.py               # Session cleanup & logout handler
│   ├── password.py             # Bcrypt hashing & verification
│   ├── register.py             # Student self-registration form
│   └── roles.py                # Role checking decorators & guards
│
├── database/                   # Database access & migrations
│   ├── connection.py           # Dual-mode connector (MySQL + SQLite fallback adapter)
│   ├── schema.sql              # Master DDL schema definition
│   ├── seed.py                 # Initial database seeding script
│   └── rprms.db                # SQLite database file
│
├── pages/                      # Role-specific UI views
│   ├── admin/                  # Admin portal views
│   │   ├── dashboard.py        # System KPIs, growth metrics, charts
│   │   ├── approvals.py        # Paper review and approval queue
│   │   ├── papers.py           # All repository papers management
│   │   ├── paper_versions.py   # Version history inspection
│   │   ├── user_management.py  # User CRUD & activation controls
│   │   ├── departments.py      # Department CRUD
│   │   ├── qr_codes.py         # Batch & individual QR management
│   │   ├── analytics.py        # Administrative analytics
│   │   └── activity_logs.py    # Security audit trails
│   ├── faculty/                # Faculty portal views
│   │   ├── dashboard.py        # Submission stats & pending reviews
│   │   ├── upload_paper.py     # New research paper upload
│   │   ├── upload_new_version.py # Paper revision upload
│   │   ├── my_papers.py        # Author's papers list
│   │   ├── paper_status.py     # Paper review status & reviewer remarks
│   │   └── analytics.py        # Research impact analytics
│   ├── student/                # Student portal views
│   │   ├── dashboard.py        # Quick search, bookmarks, recent downloads
│   │   ├── bookmarks.py        # Saved research papers
│   │   └── analytics.py        # Reading & repository statistics
│   └── shared/                 # Shared views
│       ├── search.py           # Advanced search, filters & paper details
│       ├── notifications.py    # In-app notifications center
│       └── profile.py          # User profile view
│
├── services/                   # Business logic services
│   ├── auth_service.py         # Authentication & session services
│   ├── user_service.py         # User management logic
│   ├── department_service.py   # Department management logic
│   ├── paper_service.py        # Paper metadata & versioning logic
│   ├── search_service.py       # Paper query & filter engine
│   ├── bookmark_download_service.py # Bookmark & download tracking
│   ├── analytics_service.py    # Data aggregation & analytics metrics
│   ├── notification_service.py # User notification handlers
│   ├── qr_service.py           # QR code generation & URL encoding
│   ├── email_service.py        # Submission email notification stub
│   ├── registration_service.py # Student self-registration service
│   └── ui_theme_service.py     # Visual theme, CSS, charts, KPI widgets
│
├── scripts/                    # Utilities & sample data
│   └── seed_sample_data.py     # Seeds 100 sample research papers with PDFs & QRs
│
├── data/                       # Static dataset information
│   └── sample_papers_readme.txt# Notes on sample paper datasets
│
└── uploads/                    # File storage
    ├── papers/                 # Uploaded research paper PDF files
    └── qr/                     # Generated QR code images (.png)
```
