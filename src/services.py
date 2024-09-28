from sqlalchemy import insert, select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    model = None

    @classmethod
    async def get_one(cls, session: AsyncSession, **filters):
        stmt = select(cls.model).filter_by(**filters)

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def add(cls, session: AsyncSession, **data):
        stmt = insert(cls.model).values(**data)

        await session.execute(stmt)
        await session.commit()

    @classmethod
    async def update(cls, session: AsyncSession, data: dict, **filters):
        stmt = (
            update(cls.model).filter_by(**filters).values(**data).returning(cls.model)
        )

        res = await session.execute(stmt)
        await session.commit()
        return res.scalar()

    @classmethod
    async def delete(cls, session: AsyncSession, **filters):
        stmt = delete(cls.model).filter_by(**filters)

        await session.execute(stmt)
        await session.commit()
