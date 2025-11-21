"""
Database models for Face Recognition Access Control System Admin Dashboard.
"""

from datetime import datetime, time
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Time, Text
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Employee(db.Model):
    """Employee model representing registered users in the system."""
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    position = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    access_rules = relationship('AccessRule', back_populates='employee', cascade='all, delete-orphan')
    access_logs = relationship('AccessLog', back_populates='employee', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Employee {self.name} (id: {self.id})>'
    
    def to_dict(self):
        """Convert employee to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'position': self.position,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AccessRule(db.Model):
    """Access rule model defining when employees can access the system."""
    __tablename__ = 'access_rules'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    # Relationships
    employee = relationship('Employee', back_populates='access_rules')
    
    def __repr__(self):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return f'<AccessRule {days[self.day_of_week]} {self.start_time}-{self.end_time}>'
    
    def to_dict(self):
        """Convert rule to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None
        }


class AccessLog(db.Model):
    """Access log model recording all access attempts."""
    __tablename__ = 'access_logs'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='SET NULL'), nullable=True)
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)
    status = Column(String(20), nullable=False)  # 'Granted' or 'Denied'
    snapshot_path = Column(String(255))  # Optional path to captured image
    
    # Relationships
    employee = relationship('Employee', back_populates='access_logs')
    
    def __repr__(self):
        return f'<AccessLog {self.timestamp} - {self.status}>'
    
    def to_dict(self):
        """Convert log to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else 'Unknown',
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'status': self.status,
            'snapshot_path': self.snapshot_path
        }
