"""Create an account (any environment). The password is read without echo, never from
arguments, so it does not end up in shell history or process lists.

Usage:
  python -m app.scripts.create_user --email a@b.org --name "Dr. A" --role clinician
  python -m app.scripts.create_user --email p@b.org --name "Sam" --role patient \\
      --assign-to a@b.org
Password: prompted, or REHABMIND_NEW_PASSWORD for non-interactive provisioning.
"""

import argparse
import asyncio
import getpass
import os
import sys

from sqlalchemy import select

import app.models  # noqa: F401  (registers every table)
from app.clinicians.models import Clinician
from app.core.db import SessionLocal
from app.users.models import Role, User
from app.users.provisioning import AccountError, create_account

MIN_PASSWORD = 12


async def create(email: str, name: str, role: Role, password: str, assign_to: str | None) -> None:
    async with SessionLocal() as db:
        clinician = None
        if assign_to:
            clinician = await db.scalar(
                select(Clinician)
                .join(User, User.id == Clinician.user_id)
                .where(User.email == User.normalize_email(assign_to))
            )
            if clinician is None:
                sys.exit(f"refused: no clinician {assign_to}")
        try:
            await create_account(
                db,
                email=email,
                name=name,
                role=role,
                password=password,
                clinician=clinician,
                via="cli",
            )
        except AccountError as e:
            sys.exit(f"refused: {e}")
    print(f"created {role.value} {User.normalize_email(email)}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--email", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--role", required=True, choices=[r.value for r in Role])
    p.add_argument("--assign-to", help="clinician email (patients only)")
    args = p.parse_args()
    password = os.environ.get("REHABMIND_NEW_PASSWORD") or getpass.getpass("Password: ")
    if len(password) < MIN_PASSWORD:
        sys.exit(f"refused: password must be at least {MIN_PASSWORD} characters")
    asyncio.run(create(args.email, args.name, Role(args.role), password, args.assign_to))


if __name__ == "__main__":
    main()
