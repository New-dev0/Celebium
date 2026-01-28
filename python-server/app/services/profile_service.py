"""Profile service - Business logic for profile management"""
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime
import json

from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileUpdate


class ProfileService:
    """Handle profile CRUD operations and business logic"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Profile]:
        """Get all profiles"""
        return self.db.query(Profile).all()

    def get_by_id(self, profile_id: str) -> Optional[Profile]:
        """Get profile by ID"""
        return self.db.query(Profile).filter(Profile.id == profile_id).first()

    def get_by_folder(self, folder: str) -> List[Profile]:
        """Get all profiles in a specific folder"""
        return self.db.query(Profile).filter(Profile.folder == folder).all()

    def get_by_status(self, status: str) -> List[Profile]:
        """Get profiles by status (available, running, locked)"""
        return self.db.query(Profile).filter(Profile.status == status).all()

    def create(self, profile_data: ProfileCreate) -> Profile:
        """
        Create a new profile

        Args:
            profile_data: Profile creation data

        Returns:
            Created profile
        """
        # Convert Pydantic model to dict
        data = profile_data.model_dump()

        # Convert lists to JSON strings for SQLite storage
        if 'tags' in data and isinstance(data['tags'], list):
            data['tags'] = json.dumps(data['tags'])

        if 'cookies' in data and data['cookies']:
            data['cookies'] = json.dumps(data['cookies'])

        if 'local_storage' in data and data['local_storage']:
            data['local_storage'] = json.dumps(data['local_storage'])

        # Handle proxy mapping
        if 'proxy' in data and data['proxy']:
            proxy_val = data.pop('proxy')
            if '://' in proxy_val:
                data['proxy_string'] = proxy_val
            else:
                data['proxy_id'] = proxy_val

        # Create profile with UUID
        profile = Profile(
            id=str(uuid.uuid4()),
            **data
        )

        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)

        return profile

    def update(self, profile_id: str, profile_data: ProfileUpdate) -> Optional[Profile]:
        """
        Update an existing profile

        Args:
            profile_id: Profile ID to update
            profile_data: Updated profile data

        Returns:
            Updated profile or None if not found
        """
        profile = self.get_by_id(profile_id)

        if not profile:
            return None

        # Update only provided fields
        update_data = profile_data.model_dump(exclude_unset=True)

        # Convert lists to JSON strings
        if 'tags' in update_data and isinstance(update_data['tags'], list):
            update_data['tags'] = json.dumps(update_data['tags'])

        if 'cookies' in update_data and update_data['cookies']:
            update_data['cookies'] = json.dumps(update_data['cookies'])

        # Handle proxy mapping
        if 'proxy' in update_data and update_data['proxy']:
            proxy_val = update_data.pop('proxy')
            if '://' in proxy_val:
                update_data['proxy_string'] = proxy_val
            else:
                update_data['proxy_id'] = proxy_val

        for key, value in update_data.items():
            setattr(profile, key, value)

        profile.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(profile)

        return profile

    def update_status(
        self,
        profile_id: str,
        status: str,
        debug_port: Optional[int] = None,
        websocket_url: Optional[str] = None,
        pid: Optional[int] = None
    ) -> Optional[Profile]:
        """
        Update profile runtime status

        Args:
            profile_id: Profile ID
            status: New status (available, running, locked)
            debug_port: Chrome debug port (if running)
            websocket_url: WebSocket URL (if running)
            pid: Process ID (if running)
        """
        profile = self.get_by_id(profile_id)

        if not profile:
            return None

        profile.status = status
        profile.debug_port = debug_port
        profile.websocket_url = websocket_url
        profile.pid = pid

        if status == "running":
            profile.last_used_at = datetime.now()

        profile.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(profile)

        return profile

    def delete(self, profile_id: str) -> bool:
        """
        Delete a profile

        Args:
            profile_id: Profile ID to delete

        Returns:
            True if deleted, False if not found
        """
        profile = self.get_by_id(profile_id)

        if not profile:
            return False

        # Delete profile data directory
        import shutil
        import os
        from app.core.config import settings

        profile_dir = os.path.join(settings.PROFILES_DIR, f"profile_{profile_id}")
        if os.path.exists(profile_dir):
            try:
                shutil.rmtree(profile_dir)
            except Exception as e:
                print(f"Warning: Failed to delete profile directory: {e}")

        # Delete from database
        self.db.delete(profile)
        self.db.commit()

        return True

    def search(self, query: str) -> List[Profile]:
        """
        Search profiles by name, folder, or tags

        Args:
            query: Search query string

        Returns:
            List of matching profiles
        """
        return self.db.query(Profile).filter(
            (Profile.name.contains(query)) |
            (Profile.folder.contains(query)) |
            (Profile.tags.contains(query))
        ).all()

    def duplicate(self, profile_id: str, new_name: str) -> Optional[Profile]:
        """
        Duplicate an existing profile

        Args:
            profile_id: Profile ID to duplicate
            new_name: Name for the duplicated profile

        Returns:
            New profile or None if source not found
        """
        source_profile = self.get_by_id(profile_id)

        if not source_profile:
            return None

        # Create new profile with same settings
        new_profile = Profile(
            id=str(uuid.uuid4()),
            name=new_name,
            folder=source_profile.folder,
            tags=source_profile.tags,
            os=source_profile.os,
            browser=source_profile.browser,
            user_agent=source_profile.user_agent,
            screen_resolution=source_profile.screen_resolution,
            language=source_profile.language,
            timezone=source_profile.timezone,
            geolocation=source_profile.geolocation,
            cpu_cores=source_profile.cpu_cores,
            memory_gb=source_profile.memory_gb,
            webgl_vendor=source_profile.webgl_vendor,
            webgl_renderer=source_profile.webgl_renderer,
            proxy_id=source_profile.proxy_id,
            proxy_string=source_profile.proxy_string,
            webrtc_mode=source_profile.webrtc_mode,
            canvas_mode=source_profile.canvas_mode,
            audio_mode=source_profile.audio_mode,
            notes=f"Duplicated from {source_profile.name}",
            type=source_profile.type,
            config_id=source_profile.config_id
        )

        self.db.add(new_profile)
        self.db.commit()
        self.db.refresh(new_profile)

        return new_profile

    def count_by_status(self) -> dict:
        """Get profile count by status"""
        from sqlalchemy import func

        results = self.db.query(
            Profile.status,
            func.count(Profile.id).label('count')
        ).group_by(Profile.status).all()

        return {status: count for status, count in results}

    def get_running_profiles(self) -> List[Profile]:
        """Get all currently running profiles"""
        return self.get_by_status("running")
