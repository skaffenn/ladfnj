from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from db_models import metadata_obj
URL = "postgresql+asyncpg://postgres:mDBsuGsgSVpAfbZWtRkfxwfLzufjuHXp@monorail.proxy.rlwy.net:44360/railway"

engine = create_async_engine(
    url=URL

)

session_factory = async_sessionmaker(engine)


async def init_bd():
    async with engine.connect() as conn:
        await conn.run_sync(metadata_obj.drop_all)
        await conn.run_sync(metadata_obj.create_all)
        await conn.commit()




