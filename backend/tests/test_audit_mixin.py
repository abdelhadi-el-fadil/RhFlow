from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base


class AuditTestModel(Base, AuditMixin):
    __tablename__ = "audit_test_model"

    id: Mapped[int] = mapped_column(primary_key=True)


def test_audit_mixin_adds_user_fk_columns() -> None:
    table = AuditTestModel.__table__

    assert "created_by_id" in table.c
    assert "updated_by_id" in table.c

    created_column = table.c["created_by_id"]
    updated_column = table.c["updated_by_id"]

    assert created_column.nullable is True
    assert updated_column.nullable is True

    created_fk = next(iter(created_column.foreign_keys))
    updated_fk = next(iter(updated_column.foreign_keys))

    assert created_fk.target_fullname == "users.id"
    assert updated_fk.target_fullname == "users.id"
