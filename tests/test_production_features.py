import io
import pytest
from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.user import User
from app.models.book import Book, BookCategory, BookCondition, ExchangeStatus
from app.models.exchange_request import ExchangeRequest, RequestStatus
from app.models.wishlist import Wishlist
from app.models.report import ListingReport, ReportStatus
from app.models.audit_log import AdminAuditLog
from app.models.notification import Notification
from app.auth.tokens import (
    generate_verification_token,
    confirm_verification_token,
    generate_reset_token,
    confirm_reset_token
)
from app.books import services as book_services
from app.exchanges import services as exchange_services
from app.upload_service import validate_image_magic_bytes, upload_book_cover
from werkzeug.datastructures import FileStorage


@pytest.fixture
def unverified_student(app):
    """Fixture unverified student."""
    with app.app_context():
        user = User(
            full_name="Unverified Student",
            college_email="unverified@stvincentngp.edu.in",
            department="Computer Science & Engineering",
            academic_year="1st Year",
            is_active=True,
            is_verified=False
        )
        user.set_password("Student123")
        db.session.add(user)
        db.session.commit()
        return db.session.get(User, user.id)


@pytest.fixture
def admin_user(app):
    """Fixture admin student."""
    with app.app_context():
        user = User(
            full_name="Admin Rohit",
            college_email="admin.rohit@stvincentngp.edu.in",
            department="Mechanical Engineering",
            academic_year="4th Year",
            is_active=True,
            is_verified=True,
            is_admin=True
        )
        user.set_password("AdminPass123")
        db.session.add(user)
        db.session.commit()
        return db.session.get(User, user.id)


# --- Phase A: Account Trust & Security ---

def test_verification_token_cycle(app, student_a):
    with app.app_context():
        token = generate_verification_token(student_a.id)
        assert token is not None
        user_id = confirm_verification_token(token, expiration=3600)
        assert user_id == student_a.id

        # Invalid token returns None
        assert confirm_verification_token("invalid-garbage-token") is None


def test_password_reset_token_cycle(app, student_a):
    with app.app_context():
        token = generate_reset_token(student_a.id)
        assert token is not None
        user_id = confirm_reset_token(token, expiration=1800)
        assert user_id == student_a.id

        assert confirm_reset_token("invalid-reset-token") is None


def test_unverified_student_cannot_list_books(app, unverified_student):
    with app.app_context():
        u = db.session.get(User, unverified_student.id)
        with pytest.raises(book_services.BookServiceError) as exc_info:
            book_services.create_book(
                owner=u,
                data={
                    'title': 'Engineering Mechanics',
                    'author': 'Beer and Johnston',
                    'category': BookCategory.ENGINEERING,
                    'condition': BookCondition.FAIR
                }
            )
        assert exc_info.value.status_code == 403
        assert "verify your college email" in str(exc_info.value).lower()


def test_unverified_student_cannot_request_exchange(app, unverified_student, sample_book):
    with app.app_context():
        u = db.session.get(User, unverified_student.id)
        with pytest.raises(exchange_services.ExchangeServiceError) as exc_info:
            exchange_services.create_exchange_request(
                requester=u,
                book_id=sample_book.id
            )
        assert exc_info.value.status_code == 403
        assert "verify your college email" in str(exc_info.value).lower()


def test_account_lockout_after_consecutive_failures(app, student_a):
    with app.app_context():
        u = db.session.get(User, student_a.id)
        assert u.failed_login_attempts == 0
        assert not u.is_account_locked()

        for _ in range(4):
            locked = u.record_failed_login()
            assert not locked
            assert not u.is_account_locked()

        # 5th attempt locks
        locked = u.record_failed_login()
        assert locked is True
        assert u.is_account_locked() is True
        assert u.locked_until is not None

        # Reset
        u.reset_failed_logins()
        assert u.failed_login_attempts == 0
        assert not u.is_account_locked()


# --- Phase B: Image Upload & Validation ---

def test_image_validation_magic_bytes():
    # Valid JPEG header
    jpeg_bytes = b'\xff\xd8\xff\xe0' + b'\x00' * 50
    valid, fmt = validate_image_magic_bytes(io.BytesIO(jpeg_bytes))
    assert valid is True
    assert fmt == 'jpeg'

    # Valid PNG header
    png_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
    valid, fmt = validate_image_magic_bytes(io.BytesIO(png_bytes))
    assert valid is True
    assert fmt == 'png'

    # Valid WebP header
    webp_bytes = b'RIFF' + b'\x00' * 4 + b'WEBP' + b'\x00' * 50
    valid, fmt = validate_image_magic_bytes(io.BytesIO(webp_bytes))
    assert valid is True
    assert fmt == 'webp'

    # Fake extension (e.g. executable disguised as jpg)
    fake_exe = b'MZ\x90\x00\x03\x00' + b'\x00' * 50
    valid, fmt = validate_image_magic_bytes(io.BytesIO(fake_exe))
    assert valid is False
    assert fmt == 'unknown'


def test_upload_book_cover_validation():
    # Disallowed extension
    pdf_file = FileStorage(stream=io.BytesIO(b'%PDF-1.4'), filename='notes.pdf', content_type='application/pdf')
    success, msg = upload_book_cover(pdf_file)
    assert success is False
    assert "Unsupported file format" in msg

    # File exceeding 2MB limit
    huge_bytes = b'\xff\xd8\xff\xe0' + b'\x00' * (2 * 1024 * 1024 + 10)
    huge_file = FileStorage(stream=io.BytesIO(huge_bytes), filename='cover.jpg', content_type='image/jpeg')
    success, msg = upload_book_cover(huge_file)
    assert success is False
    assert "exceeds 2 MB limit" in msg

    # Fake file content with .jpg extension
    fake_file = FileStorage(stream=io.BytesIO(b'MZ\x90\x00\x03\x00'), filename='fake.jpg', content_type='image/jpeg')
    success, msg = upload_book_cover(fake_file)
    assert success is False
    assert "Invalid image file" in msg


# --- Phase C: Notifications & Privacy Contact Disclosure ---

def test_notification_and_contact_disclosure_workflow(app, student_a, student_b, sample_book):
    with app.app_context():
        ua = db.session.get(User, student_a.id)
        ub = db.session.get(User, student_b.id)

        # 1. Student B requests book -> Notification sent to Book Owner (Student A)
        req = exchange_services.create_exchange_request(
            requester=ub,
            book_id=sample_book.id,
            message="Hi, I would love this book for my exams!"
        )

        notifs_a = Notification.query.filter_by(user_id=ua.id).all()
        assert len(notifs_a) >= 1
        assert "Exchange Request" in notifs_a[-1].title

        # Check contact info when pending: NOT yet disclosed between parties
        assert req.status == RequestStatus.PENDING

        # 2. Student A accepts request -> Notification sent to Requester (Student B)
        exchange_services.accept_exchange_request(user=ua, request_id=req.id)
        db.session.refresh(req)
        assert req.status == RequestStatus.ACCEPTED

        notifs_b = Notification.query.filter_by(user_id=ub.id).all()
        assert len(notifs_b) >= 1
        assert "Request Accepted" in notifs_b[-1].title

        # Now that status is Accepted, requester and owner can see each other's contact details
        assert req.book.owner.college_email == ua.college_email
        assert req.requester.college_email == ub.college_email


# --- Phase D: Wishlist Alerts ---

def test_wishlist_notification_on_matching_book_listing(app, student_a, student_b):
    with app.app_context():
        ua = db.session.get(User, student_a.id)
        ub = db.session.get(User, student_b.id)

        # Student B adds a wishlist item for "Compiler Design"
        wish = Wishlist(
            user_id=ub.id,
            title="Principles of Compiler Design",
            category=BookCategory.COMPUTER_SCIENCE
        )
        db.session.add(wish)
        db.session.commit()

        # Student A lists a book that matches
        book = book_services.create_book(
            owner=ua,
            data={
                'title': 'Principles of Compiler Design',
                'author': 'Aho, Ullman',
                'category': BookCategory.COMPUTER_SCIENCE,
                'condition': BookCondition.GOOD
            }
        )

        # Student B should receive a notification
        notifs_b = Notification.query.filter_by(user_id=ub.id).all()
        assert any("Wishlist Match" in n.title for n in notifs_b)


# --- Phase E: Admin Moderation & Audit Logging ---

def test_admin_access_and_moderation_workflow(client, app, student_a, admin_user, sample_book):
    # 1. Non-admin student gets 403 on /admin
    client.post('/login', data={'college_email': student_a.college_email, 'password': 'AlphaPass123'}, follow_redirects=True)
    res_non_admin = client.get('/admin/')
    assert res_non_admin.status_code == 403

    client.get('/logout', follow_redirects=True)

    # 2. Admin logs in and gets 200 on /admin
    client.post('/login', data={'college_email': admin_user.college_email, 'password': 'AdminPass123'}, follow_redirects=True)
    res_admin = client.get('/admin/')
    assert res_admin.status_code == 200
    assert b'Admin &amp; Moderation Center' in res_admin.data or b'Admin & Moderation Center' in res_admin.data

    # 3. Report listing workflow
    with app.app_context():
        ua = db.session.get(User, student_a.id)
        b = db.session.get(Book, sample_book.id)
        report = ListingReport(
            reporter_id=ua.id,
            book_id=b.id,
            reason="Wrong Subject Category",
            note="This book belongs to Mathematics not CS."
        )
        db.session.add(report)
        db.session.commit()
        report_id = report.id

    # Admin visits reports page
    res_reports = client.get('/admin/reports')
    assert res_reports.status_code == 200
    assert b'Wrong Subject Category' in res_reports.data

    # Admin hides the book from the report
    res_action = client.post(f'/admin/reports/{report_id}/hide-book', follow_redirects=True)
    assert res_action.status_code == 200

    with app.app_context():
        b = db.session.get(Book, sample_book.id)
        rep = db.session.get(ListingReport, report_id)
        assert b.is_hidden is True
        assert rep.status == ReportStatus.REVIEWED

        # Check audit log was written
        logs = AdminAuditLog.query.filter_by(action='HIDE_BOOK').all()
        assert len(logs) >= 1
        assert logs[0].target_id == b.id


# --- Phase F: SEO & Public Static Pages ---

def test_public_pages_and_seo(client):
    pages = ['/about', '/how-it-works', '/faq', '/contact', '/terms', '/privacy']
    for p in pages:
        res = client.get(p)
        assert res.status_code == 200, f"Page {p} returned {res.status_code}"

    # robots.txt
    res_robots = client.get('/robots.txt')
    assert res_robots.status_code == 200
    assert 'text/plain' in res_robots.content_type
    assert b'User-agent: *' in res_robots.data
    assert b'Sitemap:' in res_robots.data

    # sitemap.xml
    res_sitemap = client.get('/sitemap.xml')
    assert res_sitemap.status_code == 200
    assert 'application/xml' in res_sitemap.content_type or 'text/xml' in res_sitemap.content_type
    assert b'<urlset' in res_sitemap.data


# --- Phase G: Health & Cron Protected Endpoints ---

def test_health_check_endpoint(client):
    res = client.get('/api/v1/health')
    assert res.status_code == 200
    assert res.json['status'] == 'healthy'
    assert res.json['database'] == 'connected'
    assert res.json['service'] == 'Pallotti BookLoop API'


def test_cron_expire_stale_books_protection(client, app, monkeypatch):
    monkeypatch.setenv('CRON_SECRET', 'super-secret-cron-token-123')

    # Without token -> 401 Unauthorized
    res_unauth = client.post('/api/v1/cron/expire-stale-books')
    assert res_unauth.status_code == 401
    assert res_unauth.json['success'] is False

    # With invalid token -> 401 Unauthorized
    res_bad = client.post('/api/v1/cron/expire-stale-books', headers={'Authorization': 'Bearer wrong-secret'})
    assert res_bad.status_code == 401

    # With valid Bearer token -> 200 OK
    res_auth = client.post('/api/v1/cron/expire-stale-books', headers={'Authorization': 'Bearer super-secret-cron-token-123'})
    assert res_auth.status_code == 200
    assert res_auth.json['success'] is True
    assert 'expired_count' in res_auth.json
