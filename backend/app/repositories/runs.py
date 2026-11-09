from sqlmodel import Session, col, func, select

from app.db.models import GenerationRun


class RunRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, run: GenerationRun) -> GenerationRun:
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def get(self, run_id: str) -> GenerationRun | None:
        return self.session.get(GenerationRun, run_id)

    def page(self, *, limit: int = 50, offset: int = 0) -> tuple[list[GenerationRun], int]:
        total = self.session.exec(select(func.count()).select_from(GenerationRun)).one()
        items = self.session.exec(
            select(GenerationRun).order_by(col(GenerationRun.created_at).desc()).offset(offset).limit(limit)
        ).all()
        return list(items), total

    def stats(self) -> dict:
        r = GenerationRun
        row = self.session.exec(
            select(
                func.count(),
                func.avg(r.latency_ms),
                func.avg(r.avg_score),
                func.coalesce(func.sum(r.input_tokens), 0),
                func.coalesce(func.sum(r.output_tokens), 0),
                func.coalesce(func.sum(r.accepted_count), 0),
                func.coalesce(func.sum(r.rejected_count), 0),
            )
        ).one()
        by_status = dict(self.session.exec(select(r.status, func.count()).group_by(r.status)).all())
        total = row[0] or 0
        accepted, rejected = int(row[5]), int(row[6])
        reviewed = accepted + rejected
        return {
            "total_runs": total,
            "by_status": by_status,
            "avg_latency_ms": round(row[1]) if row[1] is not None else None,
            "avg_score": round(row[2], 2) if row[2] is not None else None,
            "total_input_tokens": int(row[3]),
            "total_output_tokens": int(row[4]),
            "acceptance_rate": round(accepted / reviewed, 3) if reviewed else None,
        }
