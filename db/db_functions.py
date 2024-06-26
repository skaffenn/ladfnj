from sqlalchemy import select, update
from db_init import session_factory
from db_models import UsersOrm


async def update_user_values(tg_id: int, new_values: str):
    async with session_factory() as session:
        result = await session.execute(select(UsersOrm).filter(UsersOrm.tg_id == tg_id))
        user = result.scalars().first()
        if user:
            existing_values = set(map(str.strip, map(str.lower, user.value.split(",") if user.value else [])))
            new_values_set = set(map(str.strip, map(str.lower, new_values.split(","))))
            combined_values = ",".join(existing_values.union(new_values_set))
            await session.execute(
                update(UsersOrm)
                .where(UsersOrm.tg_id == tg_id)
                .values(value=combined_values)
            )
        else:
            user = UsersOrm(tg_id=tg_id, value=new_values)
            session.add(user)
        await session.commit()
        return user








#async def insert_data():
#    async with engine.connect() as conn:
#       stmt = insert(users_values).values(
#           [
#                {"tg_id": 25,"value": "human life"},
#                {"tg_id": 52,"value": "happiness"},
#            ]
#        )
#       await conn.execute(stmt)
#        await conn.commit()

