from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy_mptt.mixins import BaseNestedSets
from .database import Base

class Node(Base, BaseNestedSets):
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    
    # Provider mapping (e.g. 'folder', 'smb', 'podcast_rss', 'stream_icecast')
    provider = Column(String, nullable=False, default="folder")
    
    # JSON string containing provider specific data (URL, SMB path, API keys, etc.)
    provider_config = Column(String, nullable=True)
    
    image_url = Column(String, nullable=True)
    
    # Comma separated list of MAC addresses. If null/empty, accessible by all.
    allowed_macs = Column(String, nullable=True)
    
    # Force FFmpeg transcoding instead of Direct Play
    use_transcoding = Column(Boolean, default=False)
    
    # If true, the folder is treated as a continuous audio stream
    is_continuous_stream = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Node(id={self.id}, name='{self.name}', provider='{self.provider}')>"

class Favorite(Base):
    __tablename__ = "favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    mac_address = Column(String, index=True, nullable=False)
    node_id = Column(Integer, ForeignKey('nodes.id'), nullable=False)
    
    node = relationship("Node")

class History(Base):
    __tablename__ = "history"
    
    id = Column(Integer, primary_key=True, index=True)
    mac_address = Column(String, index=True, nullable=False)
    node_id = Column(Integer, ForeignKey('nodes.id'), nullable=False)
    played_at = Column(DateTime(timezone=True), server_default=func.now())
    
    node = relationship("Node")

class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(String, nullable=False) # Store AES encrypted SMB credentials or UI password hash

class Source(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    provider = Column(String, nullable=False) # 'm3u', 'podcast', 'smb', 'local'
    config = Column(String, nullable=True) # JSON containing url or path

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    mac_address = Column(String, unique=True, index=True, nullable=False)
    icon = Column(String, default="devices") # Material Symbols icon name
    color = Column(String, default="#3b82f6") # Hex color code
