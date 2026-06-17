from sqlalchemy import Column, String, Integer, DateTime, JSON, Numeric, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class VendorInput(Base):
    __tablename__ = "vendor_inputs"
    
    input_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    legal_name = Column(String(255), nullable=False, index=True)
    jurisdiction = Column(String(100))
    registration_number = Column(String(100))
    directors = Column(JSON)  # [{"name": "John Doe", "position": "CEO"}]
    ubo = Column(JSON)        # [{"name": "Jane Doe", "ownership_pct": 51}]
    website_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    reports = relationship("VendorRiskReport", back_populates="input")
    
    class Config:
        from_attributes = True

class VendorRiskReport(Base):
    __tablename__ = "vendor_risk_reports"
    
    report_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    input_id = Column(String(36), ForeignKey("vendor_inputs.input_id"), index=True)
    
    overall_risk_tier = Column(String(20))  # critical, high, medium, low
    risk_score = Column(Numeric(4, 2))      # 0.00 to 100.00
    summary = Column(String(1000))
    
    findings_count = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    
    findings_json = Column(JSON)  # Serialized findings
    recommendations = Column(String(2000))
    
    raw_api_data = Column(JSON)   # Store raw responses for debugging
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    input = relationship("VendorInput", back_populates="reports")
    
    class Config:
        from_attributes = True
