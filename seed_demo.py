"""Add a small, repeatable set of demo records to the configured database."""

from datetime import date

from app import app
from extensions import db
from models import Achievement, Certification, Project, Skill, Student, StudentSkill


DEMO_STUDENTS = [
    {
        "name": "Aarav Mehta",
        "email": "aarav.mehta.demo@campus.example",
        "department": "Computer Science",
        "year": 3,
        "phone": "+1-555-0101",
        "bio": "Full-stack developer interested in accessible products and civic technology.",
        "skills": {"Python": "Advanced", "React": "Intermediate", "SQL": "Intermediate", "Figma": "Beginner"},
        "projects": [
            {
                "title": "Campus Exchange",
                "description": "A student marketplace for exchanging used textbooks and dorm essentials.",
                "tech_stack": "React, Flask, MySQL",
                "project_url": "https://github.com/example/campus-exchange",
            },
            {
                "title": "Accessible Route Finder",
                "description": "Maps step-free campus routes and reports temporary accessibility issues.",
                "tech_stack": "Python, OpenStreetMap, Leaflet",
                "project_url": "https://github.com/example/accessible-route-finder",
            },
        ],
        "certifications": [
            {"name": "AWS Certified Cloud Practitioner", "issuing_organization": "Amazon Web Services", "issue_date": date(2025, 11, 14), "credential_url": "https://aws.amazon.com/certification/"},
        ],
        "achievements": [
            {"title": "First Place, Campus Innovation Challenge", "description": "Led a four-person team that designed an accessible campus navigation prototype.", "date": date(2026, 3, 21)},
        ],
    },
    {
        "name": "Priya Nair",
        "email": "priya.nair.demo@campus.example",
        "department": "Data Science",
        "year": 2,
        "phone": "+1-555-0102",
        "bio": "Data science student exploring responsible machine learning and public health.",
        "skills": {"Python": "Intermediate", "SQL": "Advanced", "Machine Learning": "Intermediate", "Tableau": "Beginner"},
        "projects": [
            {
                "title": "Community Health Trends",
                "description": "An interactive analysis of public health indicators across local districts.",
                "tech_stack": "Python, pandas, Tableau",
                "project_url": "https://github.com/example/community-health-trends",
            },
            {
                "title": "Study Group Matcher",
                "description": "A lightweight recommendation prototype that groups students by course and availability.",
                "tech_stack": "Python, scikit-learn, Streamlit",
                "project_url": "https://github.com/example/study-group-matcher",
            },
        ],
        "certifications": [
            {"name": "Google Data Analytics Professional Certificate", "issuing_organization": "Google", "issue_date": date(2025, 8, 30), "credential_url": "https://grow.google/certificates/data-analytics/"},
            {"name": "IBM Machine Learning with Python", "issuing_organization": "IBM", "issue_date": date(2026, 1, 18), "credential_url": "https://www.ibm.com/training/"},
        ],
        "achievements": [
            {"title": "Dean's List", "description": "Recognized for strong academic performance in the fall semester.", "date": date(2026, 1, 10)},
            {"title": "Student Research Poster Award", "description": "Received an honorable mention for a poster on transparent health data visualizations.", "date": date(2026, 4, 12)},
        ],
    },
    {
        "name": "Jordan Kim",
        "email": "jordan.kim.demo@campus.example",
        "department": "Information Systems",
        "year": 4,
        "phone": "+1-555-0103",
        "bio": "UX-minded software builder focused on reliable tools for student communities.",
        "skills": {"JavaScript": "Advanced", "React": "Advanced", "Figma": "Intermediate", "SQL": "Beginner"},
        "projects": [
            {
                "title": "Volunteer Shift Board",
                "description": "A responsive scheduling board that helps campus groups coordinate volunteer shifts.",
                "tech_stack": "React, TypeScript, Firebase",
                "project_url": "https://github.com/example/volunteer-shift-board",
            },
            {
                "title": "Lab Equipment Tracker",
                "description": "A small inventory tool for reserving shared equipment in teaching labs.",
                "tech_stack": "JavaScript, Node.js, SQLite",
                "project_url": "https://github.com/example/lab-equipment-tracker",
            },
        ],
        "certifications": [
            {"name": "Meta Front-End Developer Certificate", "issuing_organization": "Meta", "issue_date": date(2025, 12, 5), "credential_url": "https://www.coursera.org/professional-certificates/meta-front-end-developer"},
        ],
        "achievements": [
            {"title": "Open Source Contributor", "description": "Contributed documentation and accessibility improvements to two student-led projects.", "date": date(2026, 2, 7)},
        ],
    },
]


def seed_demo_data():
    added = {"students": 0, "skills": 0, "student_skills": 0, "projects": 0, "certifications": 0, "achievements": 0}

    with app.app_context():
        try:
            for student_data in DEMO_STUDENTS:
                student = Student.query.filter_by(email=student_data["email"]).first()
                if student is None:
                    student = Student(
                        name=student_data["name"],
                        email=student_data["email"],
                        department=student_data["department"],
                        year=student_data["year"],
                        phone=student_data["phone"],
                        bio=student_data["bio"],
                    )
                    db.session.add(student)
                    db.session.flush()
                    added["students"] += 1

                for skill_name, proficiency in student_data["skills"].items():
                    skill = Skill.query.filter_by(name=skill_name).first()
                    if skill is None:
                        skill = Skill(name=skill_name)
                        db.session.add(skill)
                        db.session.flush()
                        added["skills"] += 1
                    student_skill = StudentSkill.query.filter_by(student_id=student.id, skill_id=skill.id).first()
                    if student_skill is None:
                        db.session.add(StudentSkill(student_id=student.id, skill_id=skill.id, proficiency=proficiency))
                        added["student_skills"] += 1

                for project_data in student_data["projects"]:
                    exists = Project.query.filter_by(student_id=student.id, title=project_data["title"]).first()
                    if exists is None:
                        db.session.add(Project(student_id=student.id, **project_data))
                        added["projects"] += 1

                for certification_data in student_data["certifications"]:
                    exists = Certification.query.filter_by(student_id=student.id, name=certification_data["name"]).first()
                    if exists is None:
                        db.session.add(Certification(student_id=student.id, **certification_data))
                        added["certifications"] += 1

                for achievement_data in student_data["achievements"]:
                    exists = Achievement.query.filter_by(student_id=student.id, title=achievement_data["title"]).first()
                    if exists is None:
                        db.session.add(Achievement(student_id=student.id, **achievement_data))
                        added["achievements"] += 1

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    print("Demo data seed complete.")
    print(f"Students added: {added['students']}")
    print(f"Skills added: {added['skills']} (catalog); proficiency assignments added: {added['student_skills']}")
    print(f"Projects added: {added['projects']}")
    print(f"Certifications added: {added['certifications']}")
    print(f"Achievements added: {added['achievements']}")


if __name__ == "__main__":
    seed_demo_data()
