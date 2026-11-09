from sqlmodel import Session, col, func, select

from app.db.models import Background, Post


class BackgroundRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, background_id: str) -> Background | None:
        return self.session.get(Background, background_id)

    def add(self, background: Background) -> Background:
        self.session.add(background)
        self.session.commit()
        self.session.refresh(background)
        return background


class PostRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, post_id: str) -> Post | None:
        return self.session.get(Post, post_id)

    def add(self, post: Post) -> Post:
        self.session.add(post)
        self.session.commit()
        self.session.refresh(post)
        return post

    def delete(self, post: Post) -> None:
        self.session.delete(post)
        self.session.commit()

    def page(self, *, limit: int = 50, offset: int = 0) -> tuple[list[Post], int]:
        total = self.session.exec(select(func.count()).select_from(Post)).one()
        items = self.session.exec(
            select(Post).order_by(col(Post.created_at).desc()).offset(offset).limit(limit)
        ).all()
        return list(items), total

    def count(self) -> int:
        return self.session.exec(select(func.count()).select_from(Post)).one()
