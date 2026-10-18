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
    from app.seed_util import seed_database
    with app.app_context():
        count = seed_database(reset=reset)
        click.echo(f"[OK] Successfully seeded {count} academic book listings across 3 demo student accounts.")
        click.echo("Demo accounts created (Password for all: Student@123):")
        click.echo("  1. aarav.cse@stvincentngp.edu.in (Verified Student)")
        click.echo("  2. priya.aids@stvincentngp.edu.in (Verified Student)")
        click.echo("  3. rohit.mech@stvincentngp.edu.in (Administrator & Verified Student)")


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
