from extensions import db


class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    student_skills = db.relationship(
        "StudentSkill",
        back_populates="skill",
        cascade="all, delete-orphan",
    )
    students = db.relationship(
        "Student",
        secondary="student_skills",
        viewonly=True,
        back_populates="skills",
    )
