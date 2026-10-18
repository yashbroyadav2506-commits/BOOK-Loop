import os
import click
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.book import Book, BookCategory, BookCondition, ExchangeStatus
from app.models.exchange_request import ExchangeRequest, RequestStatus

app = create_app(os.environ.get('FLASK_ENV', 'development'))


@app.cli.command("create-db")
def create_database():
    """Create all database tables."""
    with app.app_context():
        db.create_all()
        click.echo("[OK] Database tables created successfully.")


@app.cli.command("create-admin")
@click.option('--email', prompt='Admin College Email', help='Administrator college email')
@click.option('--name', prompt='Admin Full Name', help='Administrator full name')
@click.option('--department', prompt='Department', default='Computer Science & Engineering', help='Department')
@click.option('--year', prompt='Academic Year', default='Faculty/Staff', help='Academic Year')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
def create_admin(email, name, department, year, password):
    """Create a verified administrator account with interactive secure input."""
    with app.app_context():
        email_clean = email.strip().lower()
        user = User.query.filter_by(college_email=email_clean).first()
        if user:
            user.is_admin = True
            user.is_verified = True
            user.set_password(password)
            click.echo(f"[OK] Existing user '{email_clean}' has been promoted to Administrator.")
        else:
            user = User(
                full_name=name.strip(),
                college_email=email_clean,
                department=department.strip(),
                academic_year=year.strip(),
                is_admin=True,
                is_verified=True,
                is_active=True
            )
            user.set_password(password)
            db.session.add(user)
            click.echo(f"[OK] Administrator account created successfully for '{email_clean}'.")

        db.session.commit()


@app.cli.command("seed")
@click.option('--reset', is_flag=True, help='Clear existing sample data before seeding.')
def seed_data(reset):
    """Seed sample academic books for testing and demonstration."""
    with app.app_context():
        if reset:
            click.echo("Resetting database...")
            db.drop_all()
            db.create_all()

        # Check if demonstration student exists or create
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
                is_admin=True  # One demo student has admin capabilities for evaluation
            )
            demo_student3.set_password("Student@123")
            db.session.add(demo_student3)
        else:
            demo_student3.is_verified = True
            demo_student3.is_admin = True

        db.session.commit()

        # Seed sample books across multiple departments and conditions
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
        click.echo(f"[OK] Successfully seeded {count} academic book listings across 3 demo student accounts.")
        click.echo("Demo accounts created (Password for all: Student@123):")
        click.echo("  1. aarav.cse@stvincentngp.edu.in (Verified Student)")
        click.echo("  2. priya.aids@stvincentngp.edu.in (Verified Student)")
        click.echo("  3. rohit.mech@stvincentngp.edu.in (Administrator & Verified Student)")


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
