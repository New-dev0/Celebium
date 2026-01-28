"""Metadata Service - Folders and Configurations"""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.folder import Folder
from app.models.configuration import Configuration
from app.schemas.metadata import FolderCreate, ConfigurationCreate


class MetadataService:
    def __init__(self, db: Session):
        self.db = db

    # --- Folders ---
    def get_all_folders(self) -> List[Folder]:
        return self.db.query(Folder).all()

    def create_folder(self, folder_data: FolderCreate) -> Folder:
        folder = Folder(
            id=str(uuid.uuid4())[:8],
            name=folder_data.name
        )
        self.db.add(folder)
        self.db.commit()
        self.db.refresh(folder)
        return folder

    def delete_folder(self, folder_id: str) -> bool:
        folder = self.db.query(Folder).filter(Folder.id == folder_id).first()
        if folder:
            self.db.delete(folder)
            self.db.commit()
            return True
        return False

    # --- Configurations ---
    def get_all_configs(self) -> List[Configuration]:
        return self.db.query(Configuration).all()

    def create_config(self, config_data: ConfigurationCreate) -> Configuration:
        config = Configuration(
            id=str(uuid.uuid4())[:8],
            **config_data.model_dump()
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def delete_config(self, config_id: str) -> bool:
        config = self.db.query(Configuration).filter(Configuration.id == config_id).first()
        if config:
            self.db.delete(config)
            self.db.commit()
            return True
        return False
