from datetime import datetime, timezone
from urllib.parse import urlsplit
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.extensions import db, limiter
from app.models.user import User
from app.auth import auth_bp
from app.auth.forms import (
    LoginForm,
    RegistrationForm,
    ProfileForm,
    ChangePasswordForm,
    ForgotPasswordForm,
    ResetPasswordForm
)
from app.auth.tokens import (
    generate_verification_token,
    confirm_verification_token,
    generate_reset_token,
    confirm_reset_token
)
from app.email_service import send_verification_email, send_password_reset_email


def is_safe_redirect_url(target: str) -> bool:
    """Ensure redirection URL stays within the current host."""
    test_url = urlsplit(target)
    return test_url.scheme == '' and test_url.netloc == ''


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('books.marketplace'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            full_name=form.full_name.data.strip(),
            college_email=form.college_email.data.strip().lower(),
            department=form.department.data,
            academic_year=form.academic_year.data,
            phone_number=form.phone_number.data.strip() if form.phone_number.data else None,
            is_active=True,
            is_verified=False
        )
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()

            # Generate email verification token and send email
            token = generate_verification_token(user.id)
            send_verification_email(user, token)

            login_user(user)
            flash(
                'Welcome to Pallotti BookLoop! Your student account was created. '
                'We have sent a verification link to your email. Please verify your account to list books and send requests.',
                'success'
            )
            return redirect(url_for('books.marketplace'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration. Please try again: {str(e)}', 'danger')

    return render_template('register.html', form=form, title='Register - Pallotti BookLoop')


@auth_bp.route('/verify-email/<token>')
def verify_email(token: str):
    user_id = confirm_verification_token(token)
    if not user_id:
        flash('The verification link is invalid or has expired. Please request a new one.', 'warning')
        return redirect(url_for('books.marketplace'))

    user = db.session.get(User, user_id)
    if not user:
        flash('User account not found.', 'danger')
        return redirect(url_for('auth.login'))

    if user.is_verified:
        flash('Your email is already verified. You are ready to trade books!', 'info')
    else:
        user.is_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        db.session.commit()
        flash('Your email has been verified successfully! You can now list books and request exchanges.', 'success')

    return redirect(url_for('dashboard.index'))


@auth_bp.route('/resend-verification', methods=['POST', 'GET'])
@login_required
@limiter.limit("3 per hour")
def resend_verification():
    if current_user.is_verified:
        flash('Your account is already verified.', 'info')
        return redirect(url_for('dashboard.index'))

    token = generate_verification_token(current_user.id)
    send_verification_email(current_user, token)
    flash(f'A fresh verification email has been sent to {current_user.college_email}. Please check your inbox.', 'success')
    return redirect(url_for('dashboard.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('books.marketplace'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.college_email.data.strip().lower()
        user = User.query.filter_by(college_email=email).first()

        # Always show confirmation message to avoid user enumeration
        if user and user.is_active:
            token = generate_reset_token(user.id)
            send_password_reset_email(user, token)

        flash('If that email is registered in our system, we have sent instructions to reset your password.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html', form=form, title='Forgot Password - Pallotti BookLoop')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def reset_password(token: str):
    if current_user.is_authenticated:
        return redirect(url_for('books.marketplace'))

    user_id = confirm_reset_token(token)
    if not user_id:
        flash('The password reset link is invalid or has expired. Please request a new one.', 'warning')
        return redirect(url_for('auth.forgot_password'))

    user = db.session.get(User, user_id)
    if not user or not user.is_active:
        flash('User account not found or deactivated.', 'danger')
        return redirect(url_for('auth.login'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        user.reset_failed_logins()
        db.session.commit()
        flash('Your password has been reset successfully! You can now sign in with your new password.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', form=form, title='Reset Password - Pallotti BookLoop')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('books.marketplace'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.college_email.data.strip().lower()
        user = User.query.filter_by(college_email=email).first()

        if user:
            # Check account lockout
            if user.is_account_locked():
                flash('Your account has been temporarily locked due to multiple failed login attempts. Please wait 15 minutes before trying again.', 'danger')
                return render_template('login.html', form=form, title='Sign In - Pallotti BookLoop')

            if user.check_password(form.password.data):
                if not user.is_active:
                    flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                    return render_template('login.html', form=form, title='Sign In - Pallotti BookLoop')

                user.reset_failed_logins()
                db.session.commit()

                login_user(user, remember=form.remember_me.data)
                flash(f'Welcome back, {user.full_name.split()[0]}!', 'success')

                next_page = request.args.get('next')
                if next_page and is_safe_redirect_url(next_page):
                    return redirect(next_page)
                return redirect(url_for('dashboard.index'))
            else:
                is_locked = user.record_failed_login()
                db.session.commit()
                if is_locked:
                    flash('Account locked for 15 minutes due to 5 consecutive failed login attempts.', 'danger')
                else:
                    attempts_left = max(0, 5 - user.failed_login_attempts)
                    flash(f'Invalid email or password. {attempts_left} attempt(s) remaining before temporary lockout.', 'danger')
        else:
            flash('Invalid email or password. Please verify and try again.', 'danger')

    return render_template('login.html', form=form, title='Sign In - Pallotti BookLoop')


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('books.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    profile_form = ProfileForm(obj=current_user)
    password_form = ChangePasswordForm()

    if 'submit_profile' in request.form and profile_form.validate_on_submit():
        current_user.full_name = profile_form.full_name.data.strip()
        current_user.department = profile_form.department.data
        current_user.academic_year = profile_form.academic_year.data
        current_user.phone_number = profile_form.phone_number.data.strip() if profile_form.phone_number.data else None
        current_user.preferred_contact_method = profile_form.preferred_contact_method.data
        current_user.preferred_meeting_spot = profile_form.preferred_meeting_spot.data
        
        # Also sync owner_name on active book listings
        for book in current_user.books:
            book.owner_name = current_user.full_name

        try:
            db.session.commit()
            flash('Your profile details and contact preferences have been updated.', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')

    if 'submit_password' in request.form and password_form.validate_on_submit():
        if not current_user.check_password(password_form.current_password.data):
            flash('Incorrect current password.', 'danger')
        else:
            current_user.set_password(password_form.new_password.data)
            try:
                db.session.commit()
                flash('Your password has been changed successfully.', 'success')
                return redirect(url_for('auth.profile'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating password: {str(e)}', 'danger')

    return render_template(
        'profile.html',
        profile_form=profile_form,
        password_form=password_form,
        title='My Account Profile'
    )
