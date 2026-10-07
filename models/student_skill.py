from extensions import db


class StudentSkill(db.Model):
    __tablename__ = "student_skills"
    __table_args__ = (
        db.UniqueConstraint("student_id", "skill_id", name="uq_student_skill"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id = db.Column(
        db.Integer,
        db.ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    proficiency = db.Column(db.String(40), nullable=False)

    student = db.relationship("Student", back_populates="student_skills")
    skill = db.relationship("Skill", back_populates="student_skills")
