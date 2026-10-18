from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.dashboard import dashboard_bp
from app.exchanges import services as exchange_services
from app.models.book import Book
from app.models.exchange_request import ExchangeRequest, RequestStatus
from app.models.notification import Notification


@dashboard_bp.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    active_tab = request.args.get('tab', 'summary')

    summary = exchange_services.get_user_dashboard_summary(current_user.id)

    my_books = Book.query.filter_by(
        owner_id=current_user.id,
        is_active=True
    ).order_by(Book.created_at.desc()).all()

    incoming_requests = ExchangeRequest.query.filter_by(
        owner_id=current_user.id
    ).order_by(ExchangeRequest.created_at.desc()).all()

    outgoing_requests = ExchangeRequest.query.filter_by(
        requester_id=current_user.id
    ).order_by(ExchangeRequest.created_at.desc()).all()

    return render_template(
        'dashboard.html',
        summary=summary,
        my_books=my_books,
        incoming_requests=incoming_requests,
        outgoing_requests=outgoing_requests,
        active_tab=active_tab,
        RequestStatus=RequestStatus,
        title='My Dashboard - Pallotti BookLoop'
    )


@dashboard_bp.route('/notifications')
@login_required
def notifications():
    user_notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()

    return render_template(
        'notifications.html',
        notifications=user_notifications,
        title='My Notifications - Pallotti BookLoop'
    )


@dashboard_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'info')
    return redirect(url_for('dashboard.notifications'))


@dashboard_bp.route('/notifications/<int:notif_id>/read')
@login_required
def mark_notification_read(notif_id: int):
    notif = db.session.get(Notification, notif_id)
    if notif and notif.user_id == current_user.id:
        notif.is_read = True
        db.session.commit()
        if notif.link:
            return redirect(notif.link)
    return redirect(url_for('dashboard.notifications'))
