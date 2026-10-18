from flask import current_app
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from app.models.user import User

DEPARTMENTS = [
    ("Computer Science & Engineering", "Computer Science & Engineering"),
    ("Artificial Intelligence & Data Science", "Artificial Intelligence & Data Science"),
    ("Electronics & Telecommunication", "Electronics & Telecommunication"),
    ("Electrical Engineering", "Electrical Engineering"),
    ("Mechanical Engineering", "Mechanical Engineering"),
    ("Civil Engineering", "Civil Engineering"),
    ("Basic Sciences & Humanities", "Basic Sciences & Humanities"),
    ("Other", "Other")
]

ACADEMIC_YEARS = [
    ("1st Year", "1st Year"),
    ("2nd Year", "2nd Year"),
    ("3rd Year", "3rd Year"),
    ("4th Year", "4th Year"),
    ("Alumni", "Alumni"),
    ("Faculty/Staff", "Faculty/Staff")
]

CONTACT_METHODS = [
    ("WhatsApp", "WhatsApp Message"),
    ("Phone Call", "Phone Call"),
    ("College Email", "College Email"),
]

MEETING_SPOTS = [
    ("Central Library Entrance", "Central Library Entrance"),
    ("Admin Block Foyer", "Admin Block Foyer"),
    ("Tech Park Lobby", "Tech Park Lobby"),
    ("Campus Cafeteria", "Campus Cafeteria"),
    ("Department Notice Board", "Department Notice Board"),
    ("Main College Gate", "Main College Gate"),
]


class LoginForm(FlaskForm):
    college_email = StringField('College / Student Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me signed in')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    college_email = StringField('College / Student Email', validators=[DataRequired(), Email()])
    department = SelectField('Department', choices=DEPARTMENTS, validators=[DataRequired()])
    academic_year = SelectField('Academic Year', choices=ACADEMIC_YEARS, validators=[DataRequired()])
    phone_number = StringField('Contact / WhatsApp Number (Optional)', validators=[Optional(), Length(max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match.')]
    )
    submit = SubmitField('Create Account')

    def validate_college_email(self, field):
        email = field.data.strip().lower()
        allowed = current_app.config.get('ALLOWED_EMAIL_DOMAINS', [])
        if allowed:
            domain = email.split('@')[-1]
            if domain not in allowed:
                raise ValidationError(f"Email must belong to one of: {', '.join(allowed)}")

        existing = User.query.filter_by(college_email=email).first()
        if existing:
            raise ValidationError('This email is already registered. Please sign in instead.')


class ForgotPasswordForm(FlaskForm):
    college_email = StringField('Registered Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Password Reset Link')


class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6, max=128)])
    confirm_new_password = PasswordField(
        'Confirm New Password',
        validators=[DataRequired(), EqualTo('new_password', message='Passwords must match.')]
    )
    submit = SubmitField('Reset Password')


class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    department = SelectField('Department', choices=DEPARTMENTS, validators=[DataRequired()])
    academic_year = SelectField('Academic Year', choices=ACADEMIC_YEARS, validators=[DataRequired()])
    phone_number = StringField('Contact / WhatsApp Number', validators=[Optional(), Length(max=25)])
    preferred_contact_method = SelectField('Preferred Contact Method', choices=CONTACT_METHODS, validators=[DataRequired()])
    preferred_meeting_spot = SelectField('Preferred Campus Meeting Spot', choices=MEETING_SPOTS, validators=[DataRequired()])
    submit = SubmitField('Save Profile')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6, max=128)])
    confirm_new_password = PasswordField(
        'Confirm New Password',
        validators=[DataRequired(), EqualTo('new_password', message='Passwords must match.')]
    )
    submit = SubmitField('Update Password')
