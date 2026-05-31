import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_PROFILE_STORE_PATH = Path("speakers.json")
DEFAULT_VOICE_ASSET_ROOT = Path("assets/voices")


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class VoiceProfile:
    id: str
    name: str
    type: str
    prompt_path: str
    language: str | None = None
    ref_text: str | None = None
    tags: list[str] | None = None
    favorite: bool = False
    notes: str | None = None
    preview_path: str | None = None
    asset_dir: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


class VoiceProfileStore:
    def __init__(self, path: str | Path = DEFAULT_PROFILE_STORE_PATH):
        self.path = Path(path)

    def _read_records(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        if not isinstance(raw, dict):
            return {}
        return {str(profile_id): record for profile_id, record in raw.items() if isinstance(record, dict)}

    def _write_records(self, records: dict[str, dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(records, ensure_ascii=True, indent=2), encoding="utf-8")

    def _asset_dir_for_profile(self, profile_id: str) -> str:
        safe_id = "".join(char if char.isalnum() or char in "._-" else "-" for char in profile_id).strip(".-_")
        return str(DEFAULT_VOICE_ASSET_ROOT / (safe_id or "voice")).replace("\\", "/")

    def _normalize_tags(self, value: Any) -> list[str]:
        if isinstance(value, str):
            raw_items = value.split(",")
        elif isinstance(value, list):
            raw_items = value
        else:
            raw_items = []
        tags: list[str] = []
        seen: set[str] = set()
        for item in raw_items:
            tag = str(item).strip()
            if not tag or tag.lower() in seen:
                continue
            tags.append(tag)
            seen.add(tag.lower())
        return tags

    def _normalize_profile(self, profile_id: str, record: dict[str, Any]) -> VoiceProfile:
        return VoiceProfile(
            id=profile_id,
            name=str(record.get("name") or profile_id),
            type=str(record.get("type") or "clone"),
            prompt_path=str(record.get("prompt_path") or ""),
            language=record.get("language"),
            ref_text=record.get("ref_text"),
            tags=self._normalize_tags(record.get("tags")),
            favorite=bool(record.get("favorite", False)),
            notes=record.get("notes"),
            preview_path=record.get("preview_path"),
            asset_dir=str(record.get("asset_dir") or self._asset_dir_for_profile(profile_id)),
            created_at=record.get("created_at"),
            updated_at=record.get("updated_at"),
        )

    def list_profiles(self) -> list[VoiceProfile]:
        records = self._read_records()
        return [self._normalize_profile(profile_id, records[profile_id]) for profile_id in sorted(records)]

    def search_profiles(
        self,
        query: str | None = None,
        language: str | None = None,
        favorite: bool | None = None,
        tags: list[str] | None = None,
    ) -> list[VoiceProfile]:
        normalized_query = (query or "").strip().lower()
        normalized_language = (language or "").strip().lower()
        wanted_tags = {tag.strip().lower() for tag in tags or [] if tag.strip()}
        profiles = self.list_profiles()
        results: list[VoiceProfile] = []
        for profile in profiles:
            profile_tags = {tag.lower() for tag in profile.tags or []}
            haystack = " ".join(
                [
                    profile.id,
                    profile.name,
                    profile.type,
                    profile.language or "",
                    profile.ref_text or "",
                    profile.notes or "",
                    " ".join(profile.tags or []),
                ]
            ).lower()
            if normalized_query and normalized_query not in haystack:
                continue
            if normalized_language and (profile.language or "").lower() != normalized_language:
                continue
            if favorite is not None and profile.favorite != favorite:
                continue
            if wanted_tags and not wanted_tags.issubset(profile_tags):
                continue
            results.append(profile)
        return results

    def get_profile(self, profile_id: str) -> VoiceProfile | None:
        records = self._read_records()
        record = records.get(profile_id)
        if record is None:
            return None
        return self._normalize_profile(profile_id, record)

    def create_profile(
        self,
        profile_id: str,
        prompt_path: str,
        language: str | None = None,
        ref_text: str | None = None,
        profile_type: str = "clone",
        name: str | None = None,
    ) -> VoiceProfile:
        records = self._read_records()
        if profile_id in records:
            raise ValueError(f"speaker_id '{profile_id}' already exists.")

        now = utc_now_iso()
        profile = VoiceProfile(
            id=profile_id,
            name=name or profile_id,
            type=profile_type,
            prompt_path=prompt_path,
            language=language,
            ref_text=ref_text,
            tags=[],
            favorite=False,
            notes=None,
            preview_path=None,
            asset_dir=self._asset_dir_for_profile(profile_id),
            created_at=now,
            updated_at=now,
        )
        records[profile_id] = profile.to_record()
        self._write_records(records)
        return profile

    def rename_profile(self, old_profile_id: str, new_profile_id: str, new_prompt_path: str | None = None) -> VoiceProfile:
        records = self._read_records()
        if old_profile_id not in records:
            raise KeyError(f"speaker_id '{old_profile_id}' not found.")
        if new_profile_id in records and new_profile_id != old_profile_id:
            raise ValueError(f"speaker_id '{new_profile_id}' already exists.")
        if new_profile_id == old_profile_id:
            raise ValueError("New speaker_id is the same as current speaker_id.")

        profile = self._normalize_profile(old_profile_id, records[old_profile_id])
        updated = VoiceProfile(
            id=new_profile_id,
            name=new_profile_id,
            type=profile.type,
            prompt_path=new_prompt_path or profile.prompt_path,
            language=profile.language,
            ref_text=profile.ref_text,
            tags=profile.tags,
            favorite=profile.favorite,
            notes=profile.notes,
            preview_path=profile.preview_path,
            asset_dir=self._asset_dir_for_profile(new_profile_id),
            created_at=profile.created_at,
            updated_at=utc_now_iso(),
        )
        records[new_profile_id] = updated.to_record()
        del records[old_profile_id]
        self._write_records(records)
        return updated

    def update_profile_metadata(
        self,
        profile_id: str,
        name: str | None = None,
        language: str | None = None,
        tags: list[str] | None = None,
        favorite: bool | None = None,
        notes: str | None = None,
        preview_path: str | None = None,
    ) -> VoiceProfile:
        records = self._read_records()
        if profile_id not in records:
            raise KeyError(f"speaker_id '{profile_id}' not found.")

        profile = self._normalize_profile(profile_id, records[profile_id])
        updated = VoiceProfile(
            id=profile.id,
            name=name.strip() if name and name.strip() else profile.name,
            type=profile.type,
            prompt_path=profile.prompt_path,
            language=language.strip() if language and language.strip() else profile.language,
            ref_text=profile.ref_text,
            tags=self._normalize_tags(tags) if tags is not None else profile.tags,
            favorite=bool(favorite) if favorite is not None else profile.favorite,
            notes=notes.strip() if notes and notes.strip() else profile.notes,
            preview_path=preview_path.strip() if preview_path and preview_path.strip() else profile.preview_path,
            asset_dir=profile.asset_dir,
            created_at=profile.created_at,
            updated_at=utc_now_iso(),
        )
        records[profile_id] = updated.to_record()
        self._write_records(records)
        return updated

    def delete_profile(self, profile_id: str) -> VoiceProfile:
        records = self._read_records()
        if profile_id not in records:
            raise KeyError(f"speaker_id '{profile_id}' not found.")

        profile = self._normalize_profile(profile_id, records[profile_id])
        del records[profile_id]
        self._write_records(records)
        return profile

    def to_legacy_speakers(self) -> dict[str, dict[str, Any]]:
        speakers = {}
        for profile in self.list_profiles():
            record = profile.to_record()
            record.pop("id", None)
            speakers[profile.id] = record
        return speakers
