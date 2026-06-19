from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class VendorInput(Base):
    __tablename__ = "vendor_inputs"
    
    input_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    legal_name = Column(String(255), nullable=False, index=True)
    website_domain = Column(String(255))
    registration_number = Column(String(100))
    jurisdiction_country = Column(String(10))
    tax_identifier = Column(String(100))
    registered_address = Column(String(500))
    director_names = Column(JSON)  
    director_din = Column(JSON)    
    founder_ceo_name = Column(String(255))
    social_handles = Column(JSON)  
    corporate_email_domain = Column(String(255))
    
    source_method = Column(String(10), default="manual")
    source_filename = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class KybScan(Base):
    __tablename__ = "kyb_scans"
    
    scan_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    input_id = Column(String(36), ForeignKey("vendor_inputs.input_id"), index=True)
    scan_type = Column(String(10)) # quick or deep
    scan_timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="PENDING")
    overall_risk_level = Column(String(10))
    risk_score = Column(Integer, default=0)
    total_findings = Column(Integer, default=0)
    requires_review = Column(Boolean, default=False)
    partial_input_flags = Column(JSON)
    resolved_entity = Column(JSON)
    raw_data_summary = Column(JSON)
    completed_at = Column(DateTime)
    
    findings = relationship("AdverseFinding", backref="scan", cascade="all, delete-orphan")
    subjects = relationship("ScanSubject", backref="scan", cascade="all, delete-orphan")

class AdverseFinding(Base):
    __tablename__ = "adverse_findings"
    
    finding_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String(36), ForeignKey("kyb_scans.scan_id"), index=True)
    
    subject_type = Column(String(20))
    subject_name = Column(String(255), nullable=False)
    contamination_path = Column(String(500))
    
    category = Column(String(30), nullable=False)
    severity = Column(String(10), nullable=False)
    confidence_score = Column(Integer)
    
    title = Column(String(500), nullable=False)
    detail = Column(String(2000))
    
    source_tool = Column(String(50))
    source_urls = Column(JSON)
    source_name = Column(String(255))
    finding_date = Column(DateTime)
    raw_excerpt = Column(String(1000))
    
    requires_human_review = Column(Boolean, default=True)
    recommended_action = Column(String(50))
    excel_highlight = Column(String(20))
    
    created_at = Column(DateTime, default=datetime.utcnow)

class ScanSubject(Base):
    __tablename__ = "scan_subjects"
    
    subject_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String(36), ForeignKey("kyb_scans.scan_id"), index=True)
    subject_type = Column(String(20))
    name = Column(String(255), nullable=False)
    role = Column(String(100))
    nationality = Column(String(10))
    is_pep = Column(Boolean, default=False)
    screened_at = Column(DateTime, default=datetime.utcnow)
