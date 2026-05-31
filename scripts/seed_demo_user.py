import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import AsyncSessionLocal
from app.repositories.users import UserRepository


async def main() -> None:
    email = os.getenv("DEMO_EMAIL", "demo@example.com")
    password = os.getenv("DEMO_PASSWORD", "ChangeMe12345")
    async with AsyncSessionLocal() as db:
        repo = UserRepository(db)
        user = await repo.get_by_email(email)
        if user is None:
            await repo.create(email, password, "Demo Patient")
            await db.commit()
            print(f"Created demo user {email}")
        else:
            print(f"Demo user already exists: {email}")


if __name__ == "__main__":
    asyncio.run(main())
