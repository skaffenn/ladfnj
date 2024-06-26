from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import declarative_base


Base = declarative_base()
metadata_obj = Base.metadata


class UsersOrm(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int]
    value: Mapped[str]















#users_values = Table(
#    "users",
#    metadata_obj,
#    Column("id", Integer, primary_key=True),
#   Column("tg_id", Integer),
#    Column("value", String),
#)


