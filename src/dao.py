from sqlalchemy import insert, select, delete, update

from src.database import Session


class BaseDAO:
    model = None

    @classmethod
    async def get_one(cls, **filters):
        stmt = select(cls.model).filter_by(**filters)

        async with Session() as session:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @classmethod
    async def add(cls, **data):
        stmt = insert(cls.model).values(**data)

        async with Session() as session:
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def update(cls, data: dict, **filters):
        stmt = (
            update(cls.model).filter_by(**filters).values(**data).returning(cls.model)
        )
        async with Session() as session:
            res = await session.execute(stmt)
            await session.commit()
            return res.scalar()

    @classmethod
    async def delete(cls, **filters):
        stmt = delete(cls.model).filter_by(**filters)

        async with Session() as session:
            await session.execute(stmt)
            await session.commit()
