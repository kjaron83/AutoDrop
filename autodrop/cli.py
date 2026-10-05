"""Command-line interface commands for administrative tasks."""

import argparse
import sys

from autodrop.core.database import SessionLocal
from autodrop.services.user import create_superuser


def handle_create_superuser(args: argparse.Namespace) -> None:
    """Creates a superuser / administrator account from command line arguments."""
    db = SessionLocal()
    try:
        user = create_superuser(
            db=db,
            email=args.email,
            password=args.password,
            first_name=args.first_name,
            last_name=args.last_name,
            phone=args.phone,
        )
        print(f"Superuser '{user.email}' created/updated successfully (ID: {user.id}).")
    except Exception as e:
        print(f"Error creating superuser: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


def main() -> None:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(description="AutoDrop Administrative CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # createsuperuser command
    create_su_parser = subparsers.add_parser("createsuperuser", help="Create or elevate an admin superuser")
    create_su_parser.add_argument("--email", required=True, help="Administrator email address")
    create_su_parser.add_argument("--password", required=True, help="Administrator password")
    create_su_parser.add_argument("--first-name", default="Admin", help="First name")
    create_su_parser.add_argument("--last-name", default="User", help="Last name")
    create_su_parser.add_argument("--phone", default=None, help="Optional phone number")
    create_su_parser.set_defaults(func=handle_create_superuser)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
