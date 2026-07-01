import os
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Exercise, Service, GalleryPhoto, User

class ExerciseRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> List[Exercise]:
        result = await self.session.execute(
            select(Exercise).where(Exercise.is_active == True).order_by(Exercise.sort_order, Exercise.id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, exercise_id: int) -> Optional[Exercise]:
        result = await self.session.execute(select(Exercise).where(Exercise.id == exercise_id))
        return result.scalar_one_or_none()

    async def create(self, name: str, description: str, video_file_id: str) -> Exercise:
        ex = Exercise(name=name, description=description, video_file_id=video_file_id)
        self.session.add(ex)
        await self.session.commit()
        await self.session.refresh(ex)
        return ex

    async def delete(self, exercise_id: int):
        ex = await self.get_by_id(exercise_id)
        if ex:
            ex.is_active = False
            await self.session.commit()

class ServiceRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> List[Service]:
        result = await self.session.execute(
            select(Service).where(Service.is_active == True).order_by(Service.sort_order, Service.id)
        )
        return list(result.scalars().all())

    async def get_by_key(self, key: str) -> Optional[Service]:
        result = await self.session.execute(select(Service).where(Service.key == key))
        return result.scalar_one_or_none()

    async def upsert(self, key: str, name: str, description: str, price_usd: float) -> Service:
        svc = await self.get_by_key(key)
        if svc:
            svc.name = name
            svc.description = description
            svc.price_usd = price_usd
        else:
            svc = Service(key=key, name=name, description=description, price_usd=price_usd)
            self.session.add(svc)
        await self.session.commit()
        await self.session.refresh(svc)
        return svc

class GalleryRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> List[GalleryPhoto]:
        result = await self.session.execute(
            select(GalleryPhoto).where(GalleryPhoto.is_active == True).order_by(GalleryPhoto.id.desc())
        )
        return list(result.scalars().all())

    async def add_photo(self, file_id: str, caption: str = "") -> GalleryPhoto:
        photo = GalleryPhoto(file_id=file_id, caption=caption)
        self.session.add(photo)
        await self.session.commit()
        await self.session.refresh(photo)
        return photo

class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, telegram_id: int, username: str, first_name: str) -> User:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id, username=username, first_name=first_name)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        return user

    async def is_admin(self, telegram_id: int) -> bool:
        admin_ids = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
        return telegram_id in admin_ids
