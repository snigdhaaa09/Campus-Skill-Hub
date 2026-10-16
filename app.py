import os
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")




from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import inspect, text

from config import Config
from extensions import db

from models import Achievement, Certification, Project, Skill, Student, StudentSkill

app = Flask(__name__)
app.config.from_object(Config)
app.json.sort_keys = False

CORS(app)
db.init_app(app)

import models  # registers Student, Skill, StudentSkill, Project, Certification, Achievement


def _missing_settings():
    required = (
        "SECRET_KEY",
        "MYSQL_HOST",
        "MYSQL_PORT",
        "MYSQL_USER",
        "MYSQL_DATABASE",
    )
    missing = []
    for name in required:
        value = app.config.get(name)
        if value in (None, "", "dev-secret-key-change-me"):
            if name == "SECRET_KEY":
                continue
            missing.append(name)
    return missing


def _registered_tables():
    return sorted(db.metadata.tables.keys())


def _error_response(message, status_code, **extra):
    payload = {"success": False, "message": message}
    payload.update(extra)
    return jsonify(payload), status_code


def _serialize_skill(skill, proficiency=None):
    return {
        "id": skill.id,
        "name": skill.name,
        "proficiency": proficiency,
    }


def _serialize_student(student):
    skill_rows = []
    for student_skill in student.student_skills:
        skill_rows.append(
            _serialize_skill(student_skill.skill, student_skill.proficiency)
        )

    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "department": student.department,
        "year": student.year,
        "phone": student.phone,
        "bio": student.bio,
        "profile_photo": student.profile_photo,
        "created_at": student.created_at.isoformat() if student.created_at else None,
        "projects": [
            {
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "tech_stack": project.tech_stack,
                "project_url": project.project_url,
                "created_at": project.created_at.isoformat() if project.created_at else None,
            }
            for project in student.projects
        ],
        "certifications": [
            {
                "id": certification.id,
                "name": certification.name,
                "issuing_organization": certification.issuing_organization,
                "issue_date": certification.issue_date.isoformat() if certification.issue_date else None,
                "credential_url": certification.credential_url,
            }
            for certification in student.certifications
        ],
        "achievements": [
            {
                "id": achievement.id,
                "title": achievement.title,
                "description": achievement.description,
                "date": achievement.date.isoformat() if achievement.date else None,
            }
            for achievement in student.achievements
        ],
        "skills": skill_rows,
    }


def _serialize_project(project):
    return {
        "id": project.id,
        "student_id": project.student_id,
        "title": project.title,
        "description": project.description,
        "tech_stack": project.tech_stack,
        "project_url": project.project_url,
        "created_at": project.created_at.isoformat() if project.created_at else None,
    }


def _serialize_certification(certification):
    return {
        "id": certification.id,
        "student_id": certification.student_id,
        "name": certification.name,
        "issuing_organization": certification.issuing_organization,
        "issue_date": certification.issue_date.isoformat() if certification.issue_date else None,
        "credential_url": certification.credential_url,
    }


def _serialize_achievement(achievement):
    return {
        "id": achievement.id,
        "student_id": achievement.student_id,
        "title": achievement.title,
        "description": achievement.description,
        "date": achievement.date.isoformat() if achievement.date else None,
    }


def _parse_date_value(value, field_name):
    if value in (None, ""):
        return None

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValueError(f"{field_name} must be a valid date in YYYY-MM-DD format.")

    raise ValueError(f"{field_name} must be a valid date in YYYY-MM-DD format.")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify(
        {
            "success": True,
            "message": "Campus Skill Hub backend is running",
        }
    )


@app.route("/api/db-test", methods=["GET"])
def db_test():
    registered_tables = _registered_tables()
    missing = _missing_settings()
    if missing:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "MySQL connection failed",
                    "error": (
                        "Missing environment variables: "
                        + ", ".join(missing)
                        + ". Copy .env.example to .env and fill in the values."
                    ),
                    "registered_tables": registered_tables,
                }
            ),
            500,
        )

    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        existing_tables = sorted(inspect(db.engine).get_table_names())
        missing_tables = [
            table for table in registered_tables if table not in existing_tables
        ]
        return jsonify(
            {
                "success": True,
                "message": "MySQL connection successful",
                "database": app.config.get("MYSQL_DATABASE"),
                "registered_tables": registered_tables,
                "existing_tables": existing_tables,
                "missing_tables": missing_tables,
            }
        )
    except Exception as error:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "MySQL connection failed",
                    "error": str(error),
                    "database": app.config.get("MYSQL_DATABASE"),
                    "registered_tables": registered_tables,
                }
            ),
            500,
        )


@app.route("/api/students", methods=["GET"])
def get_students():
    try:
        students = Student.query.order_by(Student.created_at.desc()).all()
        return jsonify(
            {
                "success": True,
                "students": [_serialize_student(student) for student in students],
            }
        )
    except Exception as error:
        return _error_response(
            "Unable to load students.",
            500,
            error=str(error),
        )


@app.route("/api/students", methods=["POST"])
def create_student():
    payload = request.get_json(silent=True) or {}

    required_fields = ("name", "email", "department", "year")
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        return _error_response(
            "Missing required student fields.",
            400,
            missing_fields=missing,
        )

    if Student.query.filter_by(email=payload["email"].strip()).first():
        return _error_response(
            "A student with this email already exists.",
            409,
        )

    try:
        student = Student(
            name=payload["name"].strip(),
            email=payload["email"].strip(),
            department=payload["department"].strip(),
            year=int(payload["year"]),
            phone=payload.get("phone"),
            bio=payload.get("bio"),
            profile_photo=payload.get("profile_photo"),
        )
        db.session.add(student)
        db.session.commit()
        return jsonify(
            {
                "success": True,
                "message": "Student created successfully.",
                "student": _serialize_student(student),
            }
        ), 201
    except ValueError:
        db.session.rollback()
        return _error_response("Year must be a valid integer.", 400)
    except Exception as error:
        db.session.rollback()
        return _error_response(
            "Unable to create student.",
            500,
            error=str(error),
        )


@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)
    return jsonify({"success": True, "student": _serialize_student(student)})


@app.route("/api/students/<int:student_id>", methods=["PATCH"])
def update_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    payload = request.get_json(silent=True) or {}
    if not payload:
        return _error_response("No update data provided.", 400)

    try:
        for field in ("name", "department", "phone", "bio", "profile_photo"):
            if field in payload:
                setattr(student, field, payload[field])

        if "email" in payload:
            email = payload["email"].strip()
            if not email:
                return _error_response("Email cannot be empty.", 400)
            if Student.query.filter(Student.email == email, Student.id != student.id).first():
                return _error_response("A student with this email already exists.", 409)
            student.email = email

        if "year" in payload:
            student.year = int(payload["year"])

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Student updated successfully.",
            "student": _serialize_student(student),
        })
    except ValueError:
        db.session.rollback()
        return _error_response("Year must be a valid integer.", 400)
    except Exception as error:
        db.session.rollback()
        return _error_response(
            "Unable to update student.",
            500,
            error=str(error),
        )


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    try:
        db.session.delete(student)
        db.session.commit()
        return jsonify({"success": True, "message": "Student deleted successfully."})
    except Exception as error:
        db.session.rollback()
        return _error_response(
            "Unable to delete student.",
            500,
            error=str(error),
        )


@app.route("/api/skills", methods=["GET"])
def get_skills():
    try:
        skills = Skill.query.order_by(Skill.name.asc()).all()
        return jsonify({
            "success": True,
            "skills": [{"id": skill.id, "name": skill.name} for skill in skills],
        })
    except Exception as error:
        return _error_response("Unable to load skills.", 500, error=str(error))


@app.route("/api/skills", methods=["POST"])
def create_skill():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return _error_response("Skill name is required.", 400)

    try:
        skill = Skill.query.filter_by(name=name).first()
        if not skill:
            skill = Skill(name=name)
            db.session.add(skill)
            db.session.commit()
        return jsonify({
            "success": True,
            "message": "Skill saved successfully.",
            "skill": {"id": skill.id, "name": skill.name},
        }), 201
    except Exception as error:
        db.session.rollback()
        return _error_response("Unable to save skill.", 500, error=str(error))


@app.route("/api/students/<int:student_id>/skills", methods=["GET"])
def get_student_skills(student_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)
    return jsonify({
        "success": True,
        "skills": [
            _serialize_skill(item.skill, item.proficiency)
            for item in student.student_skills
        ],
    })


@app.route("/api/students/<int:student_id>/skills", methods=["POST"])
def add_student_skill(student_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    proficiency = (payload.get("proficiency") or "Beginner").strip() or "Beginner"
    if not name:
        return _error_response("Skill name is required.", 400)

    try:
        skill = Skill.query.filter_by(name=name).first()
        if not skill:
            skill = Skill(name=name)
            db.session.add(skill)
            db.session.flush()

        existing_link = StudentSkill.query.filter_by(
            student_id=student.id,
            skill_id=skill.id,
        ).first()
        if existing_link:
            existing_link.proficiency = proficiency
        else:
            link = StudentSkill(student_id=student.id, skill_id=skill.id, proficiency=proficiency)
            db.session.add(link)

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Student skill saved successfully.",
            "skill": _serialize_skill(skill, proficiency),
        }), 201
    except Exception as error:
        db.session.rollback()
        return _error_response("Unable to save student skill.", 500, error=str(error))


@app.route("/api/students/<int:student_id>/projects", methods=["GET"])
def get_student_projects(student_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    return jsonify({
        "success": True,
        "projects": [_serialize_project(project) for project in student.projects],
    })


@app.route("/api/students/<int:student_id>/projects", methods=["POST"])
def create_student_project(student_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    if not title:
        return _error_response("Project title is required.", 400)

    try:
        project = Project(
            student_id=student.id,
            title=title,
            description=payload.get("description"),
            tech_stack=payload.get("tech_stack"),
            project_url=payload.get("project_url"),
        )
        db.session.add(project)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Project added successfully.",
            "project": _serialize_project(project),
        }), 201
    except Exception as error:
        db.session.rollback()
        return _error_response("Unable to add project.", 500, error=str(error))


@app.route("/api/students/<int:student_id>/projects/<int:project_id>", methods=["GET"])
def get_student_project(student_id, project_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    project = Project.query.filter_by(id=project_id, student_id=student.id).first()
    if not project:
        return _error_response("Project not found.", 404)

    return jsonify({
        "success": True,
        "project": _serialize_project(project),
    })


@app.route("/api/students/<int:student_id>/projects/<int:project_id>", methods=["PATCH"])
def update_student_project(student_id, project_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    project = Project.query.filter_by(id=project_id, student_id=student.id).first()
    if not project:
        return _error_response("Project not found.", 404)

    payload = request.get_json(silent=True) or {}
    if not payload:
        return _error_response("No update data provided.", 400)

    try:
        if "title" in payload:
            title = (payload.get("title") or "").strip()
            if not title:
                return _error_response("Project title is required.", 400)
            project.title = title

        if "description" in payload:
            project.description = payload.get("description")

        if "tech_stack" in payload:
            project.tech_stack = payload.get("tech_stack")

        if "project_url" in payload:
            project.project_url = payload.get("project_url")

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Project updated successfully.",
            "project": _serialize_project(project),
        })
    except Exception as error:
        db.session.rollback()
        return _error_response("Unable to update project.", 500, error=str(error))


@app.route("/api/students/<int:student_id>/projects/<int:project_id>", methods=["DELETE"])
def delete_student_project(student_id, project_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    project = Project.query.filter_by(id=project_id, student_id=student.id).first()
    if not project:
        return _error_response("Project not found.", 404)

    try:
        db.session.delete(project)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Project deleted successfully.",
        })
    except Exception as error:
        db.session.rollback()
        return _error_response("Unable to delete project.", 500, error=str(error))


@app.route("/api/students/<int:student_id>/certifications", methods=["GET"])
def get_student_certifications(student_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    return jsonify({
        "success": True,
        "certifications": [
            _serialize_certification(certification)
            for certification in student.certifications
        ],
    })


@app.route("/api/students/<int:student_id>/certifications", methods=["POST"])
def create_student_certification(student_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    issuing_organization = (payload.get("issuing_organization") or "").strip()
    if not name:
        return _error_response("Certification name is required.", 400)
    if not issuing_organization:
        return _error_response("Issuing organization is required.", 400)

    try:
        certification = Certification(
            student_id=student.id,
            name=name,
            issuing_organization=issuing_organization,
            issue_date=_parse_date_value(payload.get("issue_date"), "issue_date"),
            credential_url=payload.get("credential_url"),
        )
        db.session.add(certification)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Certification added successfully.",
            "certification": _serialize_certification(certification),
        }), 201
    except ValueError as error:
        db.session.rollback()
        return _error_response(str(error), 400)
    except Exception as error:
        db.session.rollback()
        return _error_response("Unable to add certification.", 500, error=str(error))


@app.route("/api/students/<int:student_id>/certifications/<int:certification_id>", methods=["GET"])
def get_student_certification(student_id, certification_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    certification = Certification.query.filter_by(id=certification_id, student_id=student.id).first()
    if not certification:
        return _error_response("Certification not found.", 404)

    return jsonify({
        "success": True,
        "certification": _serialize_certification(certification),
    })


@app.route("/api/students/<int:student_id>/certifications/<int:certification_id>", methods=["PATCH"])
def update_student_certification(student_id, certification_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    certification = Certification.query.filter_by(id=certification_id, student_id=student.id).first()
    if not certification:
        return _error_response("Certification not found.", 404)

    payload = request.get_json(silent=True) or {}
    if not payload:
        return _error_response("No update data provided.", 400)

    try:
        if "name" in payload:
            name = (payload.get("name") or "").strip()
            if not name:
                return _error_response("Certification name is required.", 400)
            certification.name = name

        if "issuing_organization" in payload:
            organization = (payload.get("issuing_organization") or "").strip()
            if not organization:
                return _error_response("Issuing organization is required.", 400)
            certification.issuing_organization = organization

        if "issue_date" in payload:
            certification.issue_date = _parse_date_value(payload.get("issue_date"), "issue_date")

        if "credential_url" in payload:
            certification.credential_url = payload.get("credential_url")

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Certification updated successfully.",
            "certification": _serialize_certification(certification),
        })
    except ValueError as error:
        db.session.rollback()
        return _error_response(str(error), 400)
    except Exception as error:
        db.session.rollback()
        return _error_response("Unable to update certification.", 500, error=str(error))


@app.route("/api/students/<int:student_id>/certifications/<int:certification_id>", methods=["DELETE"])
def delete_student_certification(student_id, certification_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    certification = Certification.query.filter_by(id=certification_id, student_id=student.id).first()
    if not certification:
        return _error_response("Certification not found.", 404)

    try:
        db.session.delete(certification)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Certification deleted successfully.",
        })
    except Exception as error:
        db.session.rollback()
        return _error_response("Unable to delete certification.", 500, error=str(error))


@app.route("/api/students/<int:student_id>/achievements", methods=["GET"])
def get_student_achievements(student_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    return jsonify({
        "success": True,
        "achievements": [
            _serialize_achievement(achievement)
            for achievement in student.achievements
        ],
    })


@app.route("/api/students/<int:student_id>/achievements", methods=["POST"])
def create_student_achievement(student_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    if not title:
        return _error_response("Achievement title is required.", 400)

    try:
        achievement = Achievement(
            student_id=student.id,
            title=title,
            description=payload.get("description"),
            date=_parse_date_value(payload.get("date"), "date"),
        )
        db.session.add(achievement)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Achievement added successfully.",
            "achievement": _serialize_achievement(achievement),
        }), 201
    except ValueError as error:
        db.session.rollback()
        return _error_response(str(error), 400)
    except Exception as error:
        db.session.rollback()
        return _error_response("Unable to add achievement.", 500, error=str(error))


@app.route("/api/students/<int:student_id>/achievements/<int:achievement_id>", methods=["GET"])
def get_student_achievement(student_id, achievement_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    achievement = Achievement.query.filter_by(id=achievement_id, student_id=student.id).first()
    if not achievement:
        return _error_response("Achievement not found.", 404)

    return jsonify({
        "success": True,
        "achievement": _serialize_achievement(achievement),
    })


@app.route("/api/students/<int:student_id>/achievements/<int:achievement_id>", methods=["PATCH"])
def update_student_achievement(student_id, achievement_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    achievement = Achievement.query.filter_by(id=achievement_id, student_id=student.id).first()
    if not achievement:
        return _error_response("Achievement not found.", 404)

    payload = request.get_json(silent=True) or {}
    if not payload:
        return _error_response("No update data provided.", 400)

    try:
        if "title" in payload:
            title = (payload.get("title") or "").strip()
            if not title:
                return _error_response("Achievement title is required.", 400)
            achievement.title = title

        if "description" in payload:
            achievement.description = payload.get("description")

        if "date" in payload:
            achievement.date = _parse_date_value(payload.get("date"), "date")

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Achievement updated successfully.",
            "achievement": _serialize_achievement(achievement),
        })
    except ValueError as error:
        db.session.rollback()
        return _error_response(str(error), 400)
    except Exception as error:
        db.session.rollback()
        return _error_response("Unable to update achievement.", 500, error=str(error))


@app.route("/api/students/<int:student_id>/achievements/<int:achievement_id>", methods=["DELETE"])
def delete_student_achievement(student_id, achievement_id):
    student = Student.query.get(student_id)
    if not student:
        return _error_response("Student not found.", 404)

    achievement = Achievement.query.filter_by(id=achievement_id, student_id=student.id).first()
    if not achievement:
        return _error_response("Achievement not found.", 404)

    try:
        db.session.delete(achievement)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Achievement deleted successfully.",
        })
    except Exception as error:
        db.session.rollback()
        return _error_response("Unable to delete achievement.", 500, error=str(error))


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"success": False, "message": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(_error):
    return jsonify({"success": False, "message": "Internal server error"}), 500


if __name__ == "__main__":
    missing = _missing_settings()
    if missing:
        print("MySQL / Flask settings are incomplete.")
        print("Copy .env.example to .env and fill in these values:")
        for name in missing:
            print(f"  - {name}")
        print("The health endpoint will still run. Database features will fail until this is fixed.")


app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 5000)),
    debug=False
)