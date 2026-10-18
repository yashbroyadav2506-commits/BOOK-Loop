from typing import Optional
from app.extensions import db
from app.models.book import Book, ExchangeStatus
from app.models.exchange_request import ExchangeRequest, RequestStatus
from app.models.user import User
from app.models.notification import Notification
from app.models.rating import ExchangeRating
from app.email_service import send_exchange_notification


class ExchangeServiceError(Exception):
    """Custom exception for exchange request operations."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def create_exchange_request(
    requester: User,
    book_id: int,
    message: Optional[str] = None,
    offered_book_id: Optional[int] = None
) -> ExchangeRequest:
    """
    Create a new book exchange request.
    Rules:
    - Requester must be email verified.
    - Requester cannot request their own book.
    - Book must be active and not already Reserved or Exchanged.
    - No duplicate active (Pending or Accepted) requests from the same student for the same book.
    """
    if not requester.is_verified:
        raise ExchangeServiceError("Please verify your college email address before sending exchange requests.", status_code=403)

    book = Book.query.filter_by(id=book_id, is_active=True).first()
    if not book:
        raise ExchangeServiceError("The requested book does not exist or has been removed.", status_code=404)

    if book.owner_id == requester.id:
        raise ExchangeServiceError("You cannot request an exchange for your own book listing.")

    if book.exchange_status in [ExchangeStatus.RESERVED, ExchangeStatus.EXCHANGED, ExchangeStatus.UNAVAILABLE]:
        raise ExchangeServiceError(
            f"This book is currently {book.exchange_status.lower()} and cannot be requested.",
            status_code=400
        )

    # Check duplicate active requests
    existing_request = ExchangeRequest.query.filter(
        ExchangeRequest.book_id == book.id,
        ExchangeRequest.requester_id == requester.id,
        ExchangeRequest.status.in_([RequestStatus.PENDING, RequestStatus.ACCEPTED])
    ).first()

    if existing_request:
        raise ExchangeServiceError(
            "You already have an active exchange request for this book.",
            status_code=409
        )

    # Validate offered book if provided
    if offered_book_id:
        offered_book = Book.query.filter_by(id=offered_book_id, is_active=True).first()
        if not offered_book:
            raise ExchangeServiceError("The offered book does not exist or is inactive.", status_code=404)
        if offered_book.owner_id != requester.id:
            raise ExchangeServiceError("You can only offer books that belong to your account.")
        if offered_book.id == book.id:
            raise ExchangeServiceError("You cannot offer the same book being requested.")
        if offered_book.exchange_status in [ExchangeStatus.RESERVED, ExchangeStatus.EXCHANGED]:
            raise ExchangeServiceError(f"Your offered book is already {offered_book.exchange_status.lower()}.")

    # Database transaction
    try:
        req = ExchangeRequest(
            book_id=book.id,
            requester_id=requester.id,
            owner_id=book.owner_id,
            message=message.strip() if message else None,
            offered_book_id=offered_book_id,
            status=RequestStatus.PENDING
        )
        db.session.add(req)

        # Update book status to Exchange Requested if it was Available
        if book.exchange_status == ExchangeStatus.AVAILABLE:
            book.exchange_status = ExchangeStatus.EXCHANGE_REQUESTED

        # Create in-app notification for owner
        notif = Notification(
            user_id=book.owner_id,
            title="New Exchange Request!",
            message=f"{requester.full_name} has requested an exchange for '{book.title}'.",
            link="/dashboard/?tab=incoming"
        )
        db.session.add(notif)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ExchangeServiceError(f"Database error creating request: {str(e)}", status_code=500)

    # Send transactional email to owner
    if book.owner and book.owner.college_email:
        send_exchange_notification(
            to_email=book.owner.college_email,
            title=f"New Exchange Request for '{book.title}'",
            message=f"{requester.full_name} ({requester.department}) wants to exchange for your book '{book.title}'.",
            action_url="/dashboard/?tab=incoming"
        )

    return req


def accept_exchange_request(user: User, request_id: int) -> ExchangeRequest:
    """Owner accepts a pending request and reserves book."""
    req = db.session.get(ExchangeRequest, request_id)
    if not req:
        raise ExchangeServiceError("Exchange request not found.", status_code=404)

    if req.owner_id != user.id:
        raise ExchangeServiceError("Only the book owner can accept this exchange request.", status_code=403)

    if req.status != RequestStatus.PENDING:
        raise ExchangeServiceError(f"Cannot accept a request with status '{req.status}'.")

    book = req.book
    if not book or not book.is_active:
        raise ExchangeServiceError("Associated book is no longer available.", status_code=400)

    if book.exchange_status in [ExchangeStatus.RESERVED, ExchangeStatus.EXCHANGED]:
        raise ExchangeServiceError(
            f"Cannot accept this request because the book is already {book.exchange_status.lower()}.",
            status_code=409
        )

    try:
        req.status = RequestStatus.ACCEPTED
        book.exchange_status = ExchangeStatus.RESERVED

        # Create in-app notification for requester
        notif = Notification(
            user_id=req.requester_id,
            title="Exchange Request Accepted!",
            message=f"{user.full_name} accepted your request for '{book.title}'. Check contact details to meet on campus.",
            link="/dashboard/?tab=outgoing"
        )
        db.session.add(notif)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ExchangeServiceError(f"Database error accepting request: {str(e)}", status_code=500)

    # Send email to requester
    if req.requester and req.requester.college_email:
        send_exchange_notification(
            to_email=req.requester.college_email,
            title=f"Accepted: Your request for '{book.title}' was accepted!",
            message=f"{user.full_name} has accepted your exchange request. Preferred meeting spot: {user.preferred_meeting_spot or 'Central Library'}.",
            action_url="/dashboard/?tab=outgoing"
        )

    return req


def reject_exchange_request(user: User, request_id: int) -> ExchangeRequest:
    """Owner rejects a pending request."""
    req = db.session.get(ExchangeRequest, request_id)
    if not req:
        raise ExchangeServiceError("Exchange request not found.", status_code=404)

    if req.owner_id != user.id:
        raise ExchangeServiceError("Only the book owner can reject this exchange request.", status_code=403)

    if req.status != RequestStatus.PENDING:
        raise ExchangeServiceError(f"Cannot reject a request with status '{req.status}'.")

    book = req.book

    try:
        req.status = RequestStatus.REJECTED

        other_pending = ExchangeRequest.query.filter(
            ExchangeRequest.book_id == book.id,
            ExchangeRequest.id != req.id,
            ExchangeRequest.status == RequestStatus.PENDING
        ).count()

        if other_pending == 0 and book.exchange_status == ExchangeStatus.EXCHANGE_REQUESTED:
            book.exchange_status = ExchangeStatus.AVAILABLE

        # Create in-app notification for requester
        notif = Notification(
            user_id=req.requester_id,
            title="Exchange Request Update",
            message=f"Your request for '{book.title}' was declined by the owner.",
            link="/dashboard/?tab=outgoing"
        )
        db.session.add(notif)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ExchangeServiceError(f"Database error rejecting request: {str(e)}", status_code=500)

    return req


def cancel_exchange_request(user: User, request_id: int) -> ExchangeRequest:
    """Requester cancels their own pending request."""
    req = db.session.get(ExchangeRequest, request_id)
    if not req:
        raise ExchangeServiceError("Exchange request not found.", status_code=404)

    if req.requester_id != user.id:
        raise ExchangeServiceError("Only the student who submitted this request can cancel it.", status_code=403)

    if req.status != RequestStatus.PENDING:
        raise ExchangeServiceError(f"Cannot cancel a request that is already '{req.status}'.")

    book = req.book

    try:
        req.status = RequestStatus.CANCELLED

        other_active = ExchangeRequest.query.filter(
            ExchangeRequest.book_id == book.id,
            ExchangeRequest.id != req.id,
            ExchangeRequest.status.in_([RequestStatus.PENDING, RequestStatus.ACCEPTED])
        ).count()

        if other_active == 0 and book.exchange_status == ExchangeStatus.EXCHANGE_REQUESTED:
            book.exchange_status = ExchangeStatus.AVAILABLE

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ExchangeServiceError(f"Database error cancelling request: {str(e)}", status_code=500)

    return req


def complete_exchange_request(user: User, request_id: int) -> ExchangeRequest:
    """Mark an exchange completed by an authorized participant."""
    req = db.session.get(ExchangeRequest, request_id)
    if not req:
        raise ExchangeServiceError("Exchange request not found.", status_code=404)

    if user.id not in [req.owner_id, req.requester_id]:
        raise ExchangeServiceError("You are not an authorized participant in this exchange.", status_code=403)

    if req.status != RequestStatus.ACCEPTED:
        raise ExchangeServiceError(
            f"Only accepted exchange requests can be marked completed (current status: '{req.status}')."
        )

    book = req.book

    try:
        req.status = RequestStatus.COMPLETED
        if book:
            book.exchange_status = ExchangeStatus.EXCHANGED

        if req.offered_book_id and req.offered_book:
            req.offered_book.exchange_status = ExchangeStatus.EXCHANGED

        # Auto-reject any conflicting pending requests for the same book
        conflicting = ExchangeRequest.query.filter(
            ExchangeRequest.book_id == book.id,
            ExchangeRequest.id != req.id,
            ExchangeRequest.status == RequestStatus.PENDING
        ).all()

        for conf in conflicting:
            conf.status = RequestStatus.REJECTED

        # In-app notifications
        partner_id = req.requester_id if user.id == req.owner_id else req.owner_id
        db.session.add(Notification(
            user_id=partner_id,
            title="Exchange Completed!",
            message=f"The exchange for '{book.title}' has been marked completed. Thank you for sharing!",
            link="/dashboard/"
        ))

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ExchangeServiceError(f"Database error completing exchange: {str(e)}", status_code=500)

    return req


def rate_exchange_partner(rater: User, request_id: int, rating_value: int, comment: Optional[str] = None) -> ExchangeRating:
    """Submit post-exchange rating for peer student (1 to 5 stars)."""
    req = db.session.get(ExchangeRequest, request_id)
    if not req:
        raise ExchangeServiceError("Exchange request not found.", status_code=404)

    if rater.id not in [req.owner_id, req.requester_id]:
        raise ExchangeServiceError("You are not an authorized participant in this exchange.", status_code=403)

    if req.status != RequestStatus.COMPLETED:
        raise ExchangeServiceError("You can only rate an exchange after it has been marked completed.")

    if rating_value < 1 or rating_value > 5:
        raise ExchangeServiceError("Rating must be between 1 and 5 stars.")

    existing_rating = ExchangeRating.query.filter_by(
        exchange_request_id=req.id,
        rater_id=rater.id
    ).first()
    if existing_rating:
        raise ExchangeServiceError("You have already submitted a rating for this exchange.")

    rated_user_id = req.requester_id if rater.id == req.owner_id else req.owner_id

    try:
        new_rating = ExchangeRating(
            exchange_request_id=req.id,
            rater_id=rater.id,
            rated_user_id=rated_user_id,
            rating=rating_value,
            comment=comment.strip() if comment else None
        )
        db.session.add(new_rating)
        db.session.commit()
        return new_rating
    except Exception as e:
        db.session.rollback()
        raise ExchangeServiceError(f"Database error submitting rating: {str(e)}", status_code=500)


def get_user_dashboard_summary(user_id: int) -> dict:
    """Aggregate counts and lists for the student dashboard."""
    total_books = Book.query.filter_by(owner_id=user_id, is_active=True).count()
    available_books = Book.query.filter_by(
        owner_id=user_id,
        exchange_status=ExchangeStatus.AVAILABLE,
        is_active=True
    ).count()

    pending_incoming = ExchangeRequest.query.filter_by(
        owner_id=user_id,
        status=RequestStatus.PENDING
    ).count()

    pending_outgoing = ExchangeRequest.query.filter_by(
        requester_id=user_id,
        status=RequestStatus.PENDING
    ).count()

    accepted_exchanges = ExchangeRequest.query.filter(
        db.or_(ExchangeRequest.owner_id == user_id, ExchangeRequest.requester_id == user_id),
        ExchangeRequest.status == RequestStatus.ACCEPTED
    ).count()

    completed_exchanges = ExchangeRequest.query.filter(
        db.or_(ExchangeRequest.owner_id == user_id, ExchangeRequest.requester_id == user_id),
        ExchangeRequest.status == RequestStatus.COMPLETED
    ).count()

    unread_notifications = Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).count()

    return {
        'total_books': total_books,
        'available_books': available_books,
        'pending_incoming': pending_incoming,
        'pending_outgoing': pending_outgoing,
        'accepted_exchanges': accepted_exchanges,
        'completed_exchanges': completed_exchanges,
        'unread_notifications': unread_notifications,
    }
