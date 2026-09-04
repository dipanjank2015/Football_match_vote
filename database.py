import os
import hashlib
import secrets

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    Date,
    text
)
from sqlalchemy.orm import declarative_base, sessionmaker


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# Local development
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///football_vote.db"

# Render/Supabase sometimes provides postgres://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()


# ============================================================
# MODELS
# ============================================================

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)

    match_title = Column(
        String(200),
        default="Football Match"
    )

    match_date = Column(
        String(50),
        default=""
    )

    venue = Column(
        String(200),
        default=""
    )

    match_time = Column(
        String(50),
        default=""
    )

    fees = Column(
        String(50),
        default=""
    )


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)

    name = Column(
        String(200),
        nullable=False
    )

    pin_hash = Column(
        String(256),
        nullable=False
    )

    going = Column(
        Boolean,
        default=False
    )

    active = Column(
        Boolean,
        default=True
    )


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)

    username = Column(
        String(100),
        unique=True,
        nullable=False
    )

    password_hash = Column(
        String(256),
        nullable=False
    )


# ============================================================
# PIN / PASSWORD HASHING
# ============================================================

def hash_value(value: str) -> str:
    """
    Hash PIN/password using SHA-256 with random salt.
    """

    salt = secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        value.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()

    return f"{salt}${hashed}"


def verify_value(value: str, stored_hash: str) -> bool:
    """
    Verify PIN/password.
    """

    try:
        salt, stored = stored_hash.split("$")

        hashed = hashlib.pbkdf2_hmac(
            "sha256",
            value.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        ).hex()

        return secrets.compare_digest(
            hashed,
            stored
        )

    except Exception:
        return False


# ============================================================
# INITIAL PLAYERS
# ============================================================

INITIAL_PLAYERS = [
    ("Dipanjan(DIPU)", "0001"),
    ("Avisek(Buro)", "0002"),
    ("Rajib(Banti)", "0003"),
    ("Souvik(Laltu)", "0004"),
    ("Sourav(Nil)", "0005"),
    ("Subhankar(Sunu)", "0006"),
    ("Rohit", "0007"),
    ("Kutti", "0008"),
    ("Shiltu", "0009"),
    ("Tuhin", "0010"),
    ("Bintu", "0011"),
    ("Mainak", "0012"),
    ("Rony", "0013"),
    ("Somnath", "0014"),
    ("papai", "0015"),
    ("Sovon", "0016"),
    ("rajat", "0017"),
    ("Souvik(Tubai)", "0018"),
    ("Jeet", "0019"),
    ("Lonka", "0020"),
]


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    Base.metadata.create_all(engine)

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Settings
        # ----------------------------------------------------

        settings = db.query(Settings).first()

        if not settings:

            settings = Settings(
                match_title="Football Match",
                match_date="",
                venue="",
                match_time="",
                fees=""
            )

            db.add(settings)

        # ----------------------------------------------------
        # Admin
        # ----------------------------------------------------

        admin = db.query(Admin).first()

        if not admin:

            admin = Admin(
                username="admin",
                password_hash=hash_value("admin123")
            )

            db.add(admin)

        # ----------------------------------------------------
        # Initial Players
        # ----------------------------------------------------

        existing_players = db.query(Player).count()

        if existing_players == 0:

            for name, pin in INITIAL_PLAYERS:

                player = Player(
                    name=name,
                    pin_hash=hash_value(pin),
                    going=False,
                    active=True
                )

                db.add(player)

        db.commit()

    finally:

        db.close()


# ============================================================
# DATABASE HELPER
# ============================================================

def get_session():

    return SessionLocal()




# ============================================================

def reset_admin_password(new_password):
    db = get_session()

    admin = db.query(Admin).filter(Admin.username == "admin").first()

    if admin:
        admin.password_hash = hash_value(new_password)
    else:
        admin = Admin(
            username="admin",
            password_hash=hash_value(new_password)
        )
        db.add(admin)

    db.commit()
    db.close()

# ============================================================

def change_admin_password(current_password, new_password):
    db = get_session()

    try:
        admin = db.query(Admin).filter(Admin.username == "admin").first()

        if not admin:
            return False, "Admin account not found."

        # Check current password
        if not verify_value(current_password, admin.password_hash):
            return False, "Current password is incorrect."

        # Save new password
        admin.password_hash = hash_value(new_password)

        db.commit()

        return True, "Admin password changed successfully."

    except Exception as e:
        db.rollback()
        return False, f"Error: {e}"

    finally:
        db.close()