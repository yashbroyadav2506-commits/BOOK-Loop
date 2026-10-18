import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.book import Book, BookCategory, BookCondition, ExchangeStatus


@pytest.fixture
def app():
    """Create and configure a clean testing app instance with in-memory DB."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for HTTP requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def student_a(app):
    """Fixture student A (owner)."""
    with app.app_context():
        user = User(
            full_name="Student Alpha",
            college_email="alpha@stvincentngp.edu.in",
            department="Computer Science & Engineering",
            academic_year="3rd Year",
            phone_number="9876543210",
            is_active=True,
            is_verified=True
        )
        user.set_password("AlphaPass123")
        db.session.add(user)
        db.session.commit()
        return db.session.get(User, user.id)


@pytest.fixture
def student_b(app):
    """Fixture student B (requester)."""
    with app.app_context():
        user = User(
            full_name="Student Beta",
            college_email="beta@stvincentngp.edu.in",
            department="Artificial Intelligence & Data Science",
            academic_year="2nd Year",
            phone_number="9876543211",
            is_active=True,
            is_verified=True
        )
        user.set_password("BetaPass123")
        db.session.add(user)
        db.session.commit()
        return db.session.get(User, user.id)


@pytest.fixture
def sample_book(app, student_a):
    """Sample book listed by Student A."""
    with app.app_context():
        book = Book(
            title="Algorithms Unlocked",
            author="Thomas Cormen",
            category=BookCategory.COMPUTER_SCIENCE,
            condition=BookCondition.GOOD,
            description="Clear guide to basic algorithms.",
            isbn="9780262518802",
            owner_name=student_a.full_name,
            owner_id=student_a.id,
            exchange_status=ExchangeStatus.AVAILABLE,
            is_active=True
        )
        db.session.add(book)
        db.session.commit()
        return db.session.get(Book, book.id)
