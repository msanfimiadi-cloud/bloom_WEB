from __future__ import annotations

import argparse

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import AdminUser, UserRole


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the first admin user.")
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument(
        "--update-password",
        action="store_true",
        help="Update the password when an admin user with this email already exists",
    )
    return parser.parse_args()


def create_admin(email: str, password: str, update_password: bool = False) -> bool:
    normalized_email = email.strip().lower()
    with SessionLocal() as session:
        result = session.execute(select(AdminUser).where(AdminUser.email == normalized_email))
        existing = result.scalar_one_or_none()
        if existing is not None:
            if not update_password:
                print(f"Admin user {normalized_email} already exists; no duplicate was created.")
                return False

            existing.password_hash = hash_password(password)
            existing.is_active = True
            if existing.role != UserRole.ADMIN.value:
                existing.role = UserRole.ADMIN.value
            session.commit()
            print(f"Admin user {normalized_email} password updated.")
            return True

        admin = AdminUser(
            email=normalized_email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        session.add(admin)
        session.commit()
        print(f"Admin user {normalized_email} created.")
        return True


def main() -> None:
    args = parse_args()
    create_admin(args.email, args.password, update_password=args.update_password)


if __name__ == "__main__":
    main()
