from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from app.models.book import BookCategory, BookCondition

CATEGORY_CHOICES = [(c, c) for c in BookCategory.ALL]
CONDITION_CHOICES = [(c, c) for c in BookCondition.ALL]
SEMESTER_CHOICES = [
    ("", "Not Specified / General"),
    ("Semester 1", "Semester 1"),
    ("Semester 2", "Semester 2"),
    ("Semester 3", "Semester 3"),
    ("Semester 4", "Semester 4"),
    ("Semester 5", "Semester 5"),
    ("Semester 6", "Semester 6"),
    ("Semester 7", "Semester 7"),
    ("Semester 8", "Semester 8"),
]


class BookForm(FlaskForm):
    title = StringField('Book Title', validators=[DataRequired(), Length(max=200)])
    author = StringField('Author(s)', validators=[DataRequired(), Length(max=150)])
    category = SelectField('Academic Category', choices=CATEGORY_CHOICES, validators=[DataRequired()])
    condition = SelectField('Book Condition', choices=CONDITION_CHOICES, validators=[DataRequired()])
    semester = SelectField('Engineering Semester', choices=SEMESTER_CHOICES, validators=[Optional()])
    description = TextAreaField(
        'Description & Edition Notes (e.g., 3rd Edition, semester, highlights, course code)',
        validators=[Optional(), Length(max=3000)]
    )
    isbn = StringField('ISBN (Optional, 10 or 13 digits)', validators=[Optional(), Length(max=30)])
    cover_image_url = StringField('Cover Image URL (Optional)', validators=[Optional(), Length(max=500)])
    cover_image_file = FileField(
        'Upload Cover Image (Optional, max 2MB)',
        validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only (JPG, PNG, WebP)')]
    )
    submit = SubmitField('Submit Book Listing')
