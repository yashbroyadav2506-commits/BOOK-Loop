import pytest
from app.exchanges import services as exchange_services
from app.models.book import ExchangeStatus, Book
from app.models.exchange_request import RequestStatus, ExchangeRequest
from app.models.user import User
from app.extensions import db


def test_cannot_request_own_book(app, student_a, sample_book):
    with app.app_context():
        u = db.session.get(User, student_a.id)
        with pytest.raises(exchange_services.ExchangeServiceError) as exc_info:
            exchange_services.create_exchange_request(requester=u, book_id=sample_book.id)
        assert "cannot request an exchange for your own book" in exc_info.value.message


def test_create_exchange_request(app, student_b, sample_book):
    with app.app_context():
        u = db.session.get(User, student_b.id)
        req = exchange_services.create_exchange_request(
            requester=u,
            book_id=sample_book.id,
            message="Hi, I need this for semester 3 algorithms!"
        )
        assert req.id is not None
        assert req.status == RequestStatus.PENDING

        b = db.session.get(Book, sample_book.id)
        assert b.exchange_status == ExchangeStatus.EXCHANGE_REQUESTED


def test_duplicate_exchange_request_rejected(app, student_b, sample_book):
    with app.app_context():
        u = db.session.get(User, student_b.id)
        exchange_services.create_exchange_request(requester=u, book_id=sample_book.id)

        with pytest.raises(exchange_services.ExchangeServiceError) as exc:
            exchange_services.create_exchange_request(requester=u, book_id=sample_book.id)
        assert "already have an active exchange request" in exc.value.message
        assert exc.value.status_code == 409


def test_accept_and_reserve_workflow(app, student_a, student_b, sample_book):
    with app.app_context():
        ub = db.session.get(User, student_b.id)
        ua = db.session.get(User, student_a.id)

        req = exchange_services.create_exchange_request(requester=ub, book_id=sample_book.id)
        accepted_req = exchange_services.accept_exchange_request(user=ua, request_id=req.id)

        assert accepted_req.status == RequestStatus.ACCEPTED
        b = db.session.get(Book, sample_book.id)
        assert b.exchange_status == ExchangeStatus.RESERVED


def test_non_owner_cannot_accept(app, student_b, sample_book):
    with app.app_context():
        ub = db.session.get(User, student_b.id)
        req = exchange_services.create_exchange_request(requester=ub, book_id=sample_book.id)

        with pytest.raises(exchange_services.ExchangeServiceError) as exc:
            exchange_services.accept_exchange_request(user=ub, request_id=req.id)
        assert exc.value.status_code == 403


def test_cancel_request_reverts_book_status(app, student_b, sample_book):
    with app.app_context():
        ub = db.session.get(User, student_b.id)
        req = exchange_services.create_exchange_request(requester=ub, book_id=sample_book.id)
        
        b = db.session.get(Book, sample_book.id)
        assert b.exchange_status == ExchangeStatus.EXCHANGE_REQUESTED

        exchange_services.cancel_exchange_request(user=ub, request_id=req.id)
        
        assert req.status == RequestStatus.CANCELLED
        b_after = db.session.get(Book, sample_book.id)
        assert b_after.exchange_status == ExchangeStatus.AVAILABLE


def test_complete_exchange_and_conflicting_requests(app, student_a, student_b, sample_book):
    with app.app_context():
        # Create third student
        student_c = User(
            full_name="Student Charlie",
            college_email="charlie@stvincentngp.edu.in",
            department="Electrical",
            academic_year="2nd Year",
            is_active=True,
            is_verified=True
        )
        student_c.set_password("Charlie123")
        db.session.add(student_c)
        db.session.commit()

        ua = db.session.get(User, student_a.id)
        ub = db.session.get(User, student_b.id)
        uc = db.session.get(User, student_c.id)

        # Student B and Student C both request the book
        req_b = exchange_services.create_exchange_request(requester=ub, book_id=sample_book.id)
        req_c = exchange_services.create_exchange_request(requester=uc, book_id=sample_book.id)

        # Owner accepts Student B's request
        exchange_services.accept_exchange_request(user=ua, request_id=req_b.id)

        # Owner and Student B complete the physical exchange
        exchange_services.complete_exchange_request(user=ua, request_id=req_b.id)

        req_b_refreshed = db.session.get(ExchangeRequest, req_b.id)
        req_c_refreshed = db.session.get(ExchangeRequest, req_c.id)
        book_refreshed = db.session.get(Book, sample_book.id)

        assert req_b_refreshed.status == RequestStatus.COMPLETED
        assert book_refreshed.exchange_status == ExchangeStatus.EXCHANGED
        # Conflicting request C is auto-rejected
        assert req_c_refreshed.status == RequestStatus.REJECTED
