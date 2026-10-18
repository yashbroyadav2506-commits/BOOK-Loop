from marshmallow import Schema, fields, validate, validates, ValidationError
from app.models.book import BookCategory, BookCondition
from flask import current_app


class UserRegisterSchema(Schema):
    full_name = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100, error="Name must be between 2 and 100 characters.")
    )
    college_email = fields.Email(
        required=True,
        error_messages={"invalid": "Please provide a valid email address."}
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=6, max=128, error="Password must be at least 6 characters.")
    )
    confirm_password = fields.String(required=True)
    department = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100, error="Department is required.")
    )
    academic_year = fields.String(
        required=True,
        validate=validate.OneOf(
            ["1st Year", "2nd Year", "3rd Year", "4th Year", "Alumni", "Faculty/Staff"],
            error="Please select a valid academic year."
        )
    )
    phone_number = fields.String(
        load_default="",
        validate=validate.Length(max=25)
    )

    @validates('college_email')
    def validate_domain(self, value, **kwargs):
        allowed = current_app.config.get('ALLOWED_EMAIL_DOMAINS', [])
        if allowed:
            domain = value.split('@')[-1].lower()
            if domain not in allowed:
                raise ValidationError(
                    f"Email must belong to one of the authorized domains: {', '.join(allowed)}"
                )


class UserLoginSchema(Schema):
    college_email = fields.Email(required=True)
    password = fields.String(required=True)


class UserProfileUpdateSchema(Schema):
    full_name = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100)
    )
    department = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100)
    )
    academic_year = fields.String(
        required=True,
        validate=validate.OneOf(
            ["1st Year", "2nd Year", "3rd Year", "4th Year", "Alumni", "Faculty/Staff"]
        )
    )
    phone_number = fields.String(load_default="", validate=validate.Length(max=25))


class PasswordChangeSchema(Schema):
    current_password = fields.String(required=True)
    new_password = fields.String(
        required=True,
        validate=validate.Length(min=6, max=128, error="New password must be at least 6 characters.")
    )
    confirm_new_password = fields.String(required=True)


class BookCreateSchema(Schema):
    title = fields.String(
        required=True,
        validate=validate.Length(min=1, max=200, error="Book title is required (up to 200 chars).")
    )
    author = fields.String(
        required=True,
        validate=validate.Length(min=1, max=150, error="Author name is required (up to 150 chars).")
    )
    category = fields.String(
        required=True,
        validate=validate.OneOf(BookCategory.ALL, error=f"Invalid category. Choose from: {BookCategory.ALL}")
    )
    condition = fields.String(
        required=True,
        validate=validate.OneOf(BookCondition.ALL, error=f"Invalid condition. Choose from: {BookCondition.ALL}")
    )
    description = fields.String(load_default="", validate=validate.Length(max=3000))
    isbn = fields.String(load_default="", validate=validate.Length(max=30))
    cover_image_url = fields.String(load_default="", validate=validate.Length(max=500))

    @validates('cover_image_url')
    def validate_cover_url(self, value, **kwargs):
        if value:
            val = value.strip().lower()
            if not (val.startswith('http://') or val.startswith('https://')):
                raise ValidationError("Cover image URL must start with http:// or https://")


class BookUpdateSchema(Schema):
    title = fields.String(validate=validate.Length(min=1, max=200))
    author = fields.String(validate=validate.Length(min=1, max=150))
    category = fields.String(validate=validate.OneOf(BookCategory.ALL))
    condition = fields.String(validate=validate.OneOf(BookCondition.ALL))
    description = fields.String(validate=validate.Length(max=3000))
    isbn = fields.String(validate=validate.Length(max=30))
    cover_image_url = fields.String(validate=validate.Length(max=500))

    @validates('cover_image_url')
    def validate_cover_url(self, value, **kwargs):
        if value:
            val = value.strip().lower()
            if not (val.startswith('http://') or val.startswith('https://')):
                raise ValidationError("Cover image URL must start with http:// or https://")


class ExchangeRequestCreateSchema(Schema):
    book_id = fields.Integer(required=True)
    message = fields.String(load_default="", validate=validate.Length(max=1000))
    offered_book_id = fields.Integer(load_default=None, allow_none=True)
