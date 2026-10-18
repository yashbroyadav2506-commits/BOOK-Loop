from functools import wraps
from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app.extensions import db
from app.admin import admin_bp
from app.models.user import User
from app.models.book import Book
from app.models.exchange_request import ExchangeRequest, RequestStatus
from app.models.report import ListingReport, ReportStatus
from app.models.audit_log import AdminAuditLog


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def log_admin_action(action: str, target_type: str, target_id: int | None = None, details: str | None = None):
    """Helper to record moderation actions in the audit trail."""
    log = AdminAuditLog(
        admin_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=request.remote_addr
    )
    db.session.add(log)


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    active_books = Book.query.filter_by(is_active=True, is_hidden=False).count()
    completed_exchanges = ExchangeRequest.query.filter_by(status=RequestStatus.COMPLETED).count()
    pending_reports = ListingReport.query.filter_by(status=ReportStatus.PENDING).count()

    recent_reports = ListingReport.query.order_by(ListingReport.created_at.desc()).limit(5).all()
    recent_logs = AdminAuditLog.query.order_by(AdminAuditLog.created_at.desc()).limit(10).all()

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        active_books=active_books,
        completed_exchanges=completed_exchanges,
        pending_reports=pending_reports,
        recent_reports=recent_reports,
        recent_logs=recent_logs,
        title='Admin Center - Pallotti BookLoop'
    )


@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    status_filter = request.args.get('status', 'Pending')
    query = ListingReport.query

    if status_filter != 'All':
        query = query.filter_by(status=status_filter)

    all_reports = query.order_by(ListingReport.created_at.desc()).all()

    return render_template(
        'admin/reports.html',
        reports=all_reports,
        selected_status=status_filter,
        title='Moderation Reports - Pallotti BookLoop'
    )


@admin_bp.route('/reports/<int:report_id>/dismiss', methods=['POST'])
@login_required
@admin_required
def dismiss_report(report_id: int):
    rep = db.session.get(ListingReport, report_id)
    if not rep:
        flash('Report not found.', 'warning')
        return redirect(url_for('admin.reports'))

    rep.status = ReportStatus.DISMISSED
    rep.reviewed_at = datetime.now(timezone.utc)
    rep.reviewed_by_id = current_user.id

    log_admin_action('DISMISS_REPORT', 'ListingReport', rep.id, f"Dismissed report for Book {rep.book_id}")
    db.session.commit()

    flash('Report dismissed.', 'info')
    return redirect(url_for('admin.reports'))


@admin_bp.route('/reports/<int:report_id>/hide-book', methods=['POST'])
@login_required
@admin_required
def hide_reported_book(report_id: int):
    rep = db.session.get(ListingReport, report_id)
    if not rep:
        flash('Report not found.', 'warning')
        return redirect(url_for('admin.reports'))

    rep.status = ReportStatus.REVIEWED
    rep.reviewed_at = datetime.now(timezone.utc)
    rep.reviewed_by_id = current_user.id

    if rep.book:
        rep.book.is_hidden = True

    log_admin_action('HIDE_BOOK', 'Book', rep.book_id, f"Hidden book '{rep.book.title if rep.book else 'N/A'}' based on report #{rep.id}")
    db.session.commit()

    flash(f"Book '{rep.book.title if rep.book else ''}' has been hidden from marketplace.", 'success')
    return redirect(url_for('admin.reports'))


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    search = request.args.get('q', '').strip()
    query = User.query

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                User.full_name.ilike(search_pattern),
                User.college_email.ilike(search_pattern),
                User.department.ilike(search_pattern)
            )
        )

    all_users = query.order_by(User.created_at.desc()).all()
    return render_template(
        'admin/users.html',
        users=all_users,
        search=search,
        title='User Management - Pallotti BookLoop'
    )


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id: int):
    if user_id == current_user.id:
        flash('You cannot deactivate your own admin account.', 'danger')
        return redirect(url_for('admin.users'))

    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'warning')
        return redirect(url_for('admin.users'))

    user.is_active = not user.is_active
    action_str = "ACTIVATED" if user.is_active else "DEACTIVATED"
    log_admin_action(f"{action_str}_USER", 'User', user.id, f"User {user.college_email} was {action_str.lower()}")
    db.session.commit()

    flash(f"Account for {user.full_name} has been {action_str.lower()}.", 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_user_admin(user_id: int):
    if user_id == current_user.id:
        flash('You cannot revoke your own admin rights.', 'danger')
        return redirect(url_for('admin.users'))

    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'warning')
        return redirect(url_for('admin.users'))

    user.is_admin = not user.is_admin
    action_str = "PROMOTED_ADMIN" if user.is_admin else "DEMOTED_ADMIN"
    log_admin_action(action_str, 'User', user.id, f"Admin status toggled to {user.is_admin}")
    db.session.commit()

    flash(f"Admin rights for {user.full_name}: {user.is_admin}.", 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/books')
@login_required
@admin_required
def books():
    search = request.args.get('q', '').strip()
    query = Book.query

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Book.title.ilike(search_pattern),
                Book.author.ilike(search_pattern),
                Book.owner_name.ilike(search_pattern)
            )
        )

    all_books = query.order_by(Book.created_at.desc()).all()
    return render_template(
        'admin/books.html',
        books=all_books,
        search=search,
        title='Book Moderation - Pallotti BookLoop'
    )


@admin_bp.route('/books/<int:book_id>/toggle-hidden', methods=['POST'])
@login_required
@admin_required
def toggle_book_hidden(book_id: int):
    book = db.session.get(Book, book_id)
    if not book:
        flash('Book not found.', 'warning')
        return redirect(url_for('admin.books'))

    book.is_hidden = not book.is_hidden
    action_str = "HIDDEN" if book.is_hidden else "UNHIDDEN"
    log_admin_action(f"{action_str}_BOOK", 'Book', book.id, f"Listing '{book.title}' was {action_str.lower()}")
    db.session.commit()

    flash(f"Book '{book.title}' has been {action_str.lower()}.", 'info')
    return redirect(url_for('admin.books'))


@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    logs = AdminAuditLog.query.order_by(AdminAuditLog.created_at.desc()).limit(100).all()
    return render_template(
        'admin/audit_logs.html',
        logs=logs,
        title='Moderation Audit Logs - Pallotti BookLoop'
    )
