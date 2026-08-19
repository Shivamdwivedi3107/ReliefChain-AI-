from sqlalchemy import Column, String, Float, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Resource(Base, TimestampMixin):
    __tablename__ = "resources"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String(120), nullable=False, unique=True, index=True)
    category = Column(String(50), nullable=False, index=True)  # food, water, medicine, clothing, shelter, equipment, hygiene
    unit = Column(String(30), nullable=False, default="units")  # kg, liters, boxes, packets, units
    description = Column(Text, nullable=True)

    # Relationships
    inventories = relationship("ResourceInventory", back_populates="resource", cascade="all, delete-orphan")
    donations = relationship("Donation", back_populates="resource")
    distributions = relationship("Distribution", back_populates="resource")


class ResourceInventory(Base, TimestampMixin):
    __tablename__ = "resource_inventories"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_id = Column(String(36), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    total_quantity = Column(Float, nullable=False, default=0.0)
    available_quantity = Column(Float, nullable=False, default=0.0)
    reserved_quantity = Column(Float, nullable=False, default=0.0)
    warehouse_location = Column(String(200), nullable=True)

    __table_args__ = (
        UniqueConstraint("organization_id", "resource_id", name="uq_org_resource_inventory"),
    )

    # Relationships
    organization = relationship("Organization", back_populates="inventories")
    resource = relationship("Resource", back_populates="inventories")
