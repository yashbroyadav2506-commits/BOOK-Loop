import logging
from app.extensions import db
from app.models.user import User
from app.models.book import Book, BookCategory, BookCondition, ExchangeStatus

logger = logging.getLogger(__name__)


def seed_database(reset: bool = False) -> int:
    """
    Ensure database tables exist and seed default SVPCET demo accounts and textbooks.
    Safe to run repeatedly; only seeds records that do not yet exist.
    """
    db.create_all()

    if reset:
        logger.info("Resetting all database tables...")
        db.drop_all()
        db.create_all()

    # 1. Seed demo student accounts
    demo_student1 = User.query.filter_by(college_email="aarav.cse@stvincentngp.edu.in").first()
    if not demo_student1:
        demo_student1 = User(
            full_name="Aarav Sharma",
            college_email="aarav.cse@stvincentngp.edu.in",
            department="Computer Science & Engineering",
            academic_year="3rd Year",
            phone_number="+91 98765 43210",
            is_active=True,
            is_verified=True,
            is_admin=False
        )
        demo_student1.set_password("Student@123")
        db.session.add(demo_student1)
    else:
        demo_student1.is_verified = True

    demo_student2 = User.query.filter_by(college_email="priya.aids@stvincentngp.edu.in").first()
    if not demo_student2:
        demo_student2 = User(
            full_name="Priya Patel",
            college_email="priya.aids@stvincentngp.edu.in",
            department="Artificial Intelligence & Data Science",
            academic_year="2nd Year",
            phone_number="+91 98765 43211",
            is_active=True,
            is_verified=True,
            is_admin=False
        )
        demo_student2.set_password("Student@123")
        db.session.add(demo_student2)
    else:
        demo_student2.is_verified = True

    demo_student3 = User.query.filter_by(college_email="rohit.mech@stvincentngp.edu.in").first()
    if not demo_student3:
        demo_student3 = User(
            full_name="Rohit Kulkarni",
            college_email="rohit.mech@stvincentngp.edu.in",
            department="Mechanical Engineering",
            academic_year="4th Year",
            phone_number="+91 98765 43212",
            is_active=True,
            is_verified=True,
            is_admin=True
        )
        demo_student3.set_password("Student@123")
        db.session.add(demo_student3)
    else:
        demo_student3.is_verified = True
        demo_student3.is_admin = True

    db.session.commit()

    # 2. Seed sample books
    sample_books = [
        {
            "title": "Introduction to Algorithms (CLRS)",
            "author": "Thomas H. Cormen, Charles E. Leiserson",
            "category": BookCategory.COMPUTER_SCIENCE,
            "condition": BookCondition.LIKE_NEW,
            "semester": "Semester 3",
            "description": "Essential textbook for Data Structures and Algorithms. 3rd Edition, pristine condition with all chapter bookmarks intact.",
            "isbn": "9780262033848",
            "cover_image_url": "https://images.unsplash.com/photo-1532012164546-f432f2e3edd4?w=600&auto=format&fit=crop&q=80",
            "owner": demo_student1,
            "status": ExchangeStatus.AVAILABLE
        },
        {
            "title": "Pattern Recognition and Machine Learning",
            "author": "Christopher M. Bishop",
            "category": BookCategory.DATA_SCIENCE,
            "condition": BookCondition.GOOD,
            "semester": "Semester 5",
            "description": "Recommended for Semester 5 Machine Learning & AI course. Minimal pencil notes on Bayesian chapters.",
            "isbn": "9780387310732",
            "cover_image_url": "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=600&auto=format&fit=crop&q=80",
            "owner": demo_student2,
            "status": ExchangeStatus.AVAILABLE
        },
        {
            "title": "Higher Engineering Mathematics",
            "author": "Dr. B.S. Grewal",
            "category": BookCategory.MATHEMATICS,
            "condition": BookCondition.FAIR,
            "semester": "Semester 1",
            "description": "Covers M-1, M-2, and M-3 syllabi for RTMNU & autonomous curriculum. Includes solved question papers.",
            "isbn": "9788174091955",
            "cover_image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80",
            "owner": demo_student3,
            "status": ExchangeStatus.AVAILABLE
        },
        {
            "title": "Computer Networks: A Systems Approach",
            "author": "Larry L. Peterson, Bruce S. Davie",
            "category": BookCategory.COMPUTER_SCIENCE,
            "condition": BookCondition.LIKE_NEW,
            "semester": "Semester 4",
            "description": "5th Edition. Clear explanations of TCP/IP, OSI, and network routing protocols. Used for Semester 4 CSE.",
            "isbn": "9780123850591",
            "cover_image_url": "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=600&auto=format&fit=crop&q=80",
            "owner": demo_student1,
            "status": ExchangeStatus.AVAILABLE
        },
        {
            "title": "Fundamentals of Electric Circuits",
            "author": "Charles K. Alexander, Matthew N.O. Sadiku",
            "category": BookCategory.ELECTRONICS,
            "condition": BookCondition.GOOD,
            "semester": "Semester 2",
            "description": "Standard book for Basic Electrical & Network Analysis courses in first and second year engineering.",
            "isbn": "9780078028229",
            "cover_image_url": "https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=600&auto=format&fit=crop&q=80",
            "owner": demo_student3,
            "status": ExchangeStatus.AVAILABLE
        },
        {
            "title": "GATE Computer Science & IT Topic-Wise Solved Papers",
            "author": "Made Easy Publications",
            "category": BookCategory.COMPETITIVE_EXAMS,
            "condition": BookCondition.HEAVILY_USED,
            "semester": "Semester 7",
            "description": "Last 20 years GATE CS solved questions with comprehensive explanations. Highlighting on key formulas.",
            "isbn": "9789391061982",
            "cover_image_url": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=600&auto=format&fit=crop&q=80",
            "owner": demo_student1,
            "status": ExchangeStatus.AVAILABLE
        },
        {
            "title": "Fluid Mechanics and Hydraulic Machines",
            "author": "Dr. R.K. Bansal",
            "category": BookCategory.ENGINEERING,
            "condition": BookCondition.GOOD,
            "semester": "Semester 3",
            "description": "Comprehensive reference for Mechanical and Civil engineering students. Very helpful for lab exams.",
            "isbn": "9788131808047",
            "cover_image_url": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=600&auto=format&fit=crop&q=80",
            "owner": demo_student3,
            "status": ExchangeStatus.AVAILABLE
        },
        {
            "title": "Engineering Physics",
            "author": "H.K. Malik, A.K. Singh",
            "category": BookCategory.PHYSICS,
            "condition": BookCondition.FAIR,
            "semester": "Semester 1",
            "description": "First year textbook covering Optics, Lasers, Quantum Mechanics, and Semiconductors.",
            "isbn": "9780070671539",
            "cover_image_url": "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?w=600&auto=format&fit=crop&q=80",
            "owner": demo_student2,
            "status": ExchangeStatus.AVAILABLE
        }
    ]

    count = 0
    for b_data in sample_books:
        existing = Book.query.filter_by(title=b_data["title"], owner_id=b_data["owner"].id).first()
        if not existing:
            b = Book(
                title=b_data["title"],
                author=b_data["author"],
                category=b_data["category"],
                condition=b_data["condition"],
                semester=b_data.get("semester"),
                description=b_data["description"],
                isbn=b_data["isbn"],
                cover_image_url=b_data["cover_image_url"],
                owner_name=b_data["owner"].full_name,
                owner_id=b_data["owner"].id,
                exchange_status=b_data["status"],
                is_active=True,
                is_hidden=False
            )
            db.session.add(b)
            count += 1

    db.session.commit()
    logger.info(f"Seeded {count} academic book listings.")
    return count
