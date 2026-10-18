from flask import redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import limiter
from app.exchanges import exchanges_bp
from app.exchanges import services as exchange_services


@exchanges_bp.route('/request/<int:book_id>', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def request_exchange(book_id: int):
    if not current_user.is_verified:
        flash('Please verify your college email address before requesting an exchange.', 'warning')
        return redirect(url_for('books.book_detail', book_id=book_id))

    message = request.form.get('message', '').strip()
    offered_book_id_raw = request.form.get('offered_book_id')

    offered_book_id = None
    if offered_book_id_raw and offered_book_id_raw.isdigit():
        offered_book_id = int(offered_book_id_raw)

    try:
        req = exchange_services.create_exchange_request(
            requester=current_user,
            book_id=book_id,
            message=message if message else None,
            offered_book_id=offered_book_id
        )
        flash('Exchange request submitted successfully! The book owner has been notified.', 'success')
    except exchange_services.ExchangeServiceError as e:
        flash(e.message, 'danger')

    return redirect(url_for('books.book_detail', book_id=book_id))


@exchanges_bp.route('/<int:request_id>/accept', methods=['POST'])
@login_required
def accept(request_id: int):
    try:
        exchange_services.accept_exchange_request(user=current_user, request_id=request_id)
        flash('Exchange request accepted! The book is now reserved. You can now coordinate handover on campus.', 'success')
    except exchange_services.ExchangeServiceError as e:
        flash(e.message, 'danger')

    return redirect(url_for('dashboard.index', tab='incoming'))


@exchanges_bp.route('/<int:request_id>/reject', methods=['POST'])
@login_required
def reject(request_id: int):
    try:
        exchange_services.reject_exchange_request(user=current_user, request_id=request_id)
        flash('Exchange request rejected.', 'info')
    except exchange_services.ExchangeServiceError as e:
        flash(e.message, 'danger')

    return redirect(url_for('dashboard.index', tab='incoming'))


@exchanges_bp.route('/<int:request_id>/cancel', methods=['POST'])
@login_required
def cancel(request_id: int):
    try:
        exchange_services.cancel_exchange_request(user=current_user, request_id=request_id)
        flash('Exchange request cancelled.', 'info')
    except exchange_services.ExchangeServiceError as e:
        flash(e.message, 'danger')

    return redirect(url_for('dashboard.index', tab='outgoing'))


@exchanges_bp.route('/<int:request_id>/complete', methods=['POST'])
@login_required
def complete(request_id: int):
    try:
        exchange_services.complete_exchange_request(user=current_user, request_id=request_id)
        flash('Exchange completed! Thank you for sharing academic knowledge with your peers.', 'success')
    except exchange_services.ExchangeServiceError as e:
        flash(e.message, 'danger')

    return redirect(url_for('dashboard.index'))


@exchanges_bp.route('/<int:request_id>/rate', methods=['POST'])
@login_required
def rate_partner(request_id: int):
    rating_val_raw = request.form.get('rating', '5')
    comment = request.form.get('comment', '').strip()

    try:
        rating_val = int(rating_val_raw)
        exchange_services.rate_exchange_partner(
            rater=current_user,
            request_id=request_id,
            rating_value=rating_val,
            comment=comment if comment else None
        )
        flash('Thank you for submitting a peer rating! This helps build community trust on campus.', 'success')
    except exchange_services.ExchangeServiceError as e:
        flash(e.message, 'danger')
    except ValueError:
        flash('Invalid rating score.', 'warning')

    return redirect(url_for('dashboard.index'))
