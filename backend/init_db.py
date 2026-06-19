from app.core.db import Base, engine
from app.models import Transaction  # noqa: F401


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("portfolio.db initialized")

