from datetime import datetime, timezone

from extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(120), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    projects = db.relationship(
        "Project",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    certifications = db.relationship(
        "Certification",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    achievements = db.relationship(
        "Achievement",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    student_skills = db.relationship(
        "StudentSkill",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    skills = db.relationship(
        "Skill",
        secondary="student_skills",
        viewonly=True,
        back_populates="students",
    )
