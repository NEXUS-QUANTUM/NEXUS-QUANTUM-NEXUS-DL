# ==========================================================================
#  NexusDL 2.0 - Modèle Paramètres
#  Fichier : backend/app/models/settings.py
# ==========================================================================

import json
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.models import Base


class Setting(Base):
    """
    Modèle pour stocker les paramètres globaux de l'application sous forme clé-valeur.
    Permet de gérer la configuration dynamique (modifiable sans redémarrage).
    """
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)  # Valeur brute, sera typée selon le champ type
    type = Column(String(20), default="string")  # string, int, bool, float, json
    description = Column(String(200), nullable=True)
    category = Column(String(50), default="general")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Setting(key='{self.key}', type='{self.type}')>"

    def get_value(self) -> Any:
        """
        Retourne la valeur convertie selon le type déclaré.
        """
        if self.value is None:
            return None
        if self.type == "int":
            return int(self.value)
        elif self.type == "float":
            return float(self.value)
        elif self.type == "bool":
            return self.value.lower() in ("true", "1", "yes")
        elif self.type == "json":
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return None
        else:  # string par défaut
            return self.value

    def set_value(self, value: Any):
        """
        Définit la valeur et détermine automatiquement le type.
        """
        if isinstance(value, int):
            self.type = "int"
            self.value = str(value)
        elif isinstance(value, float):
            self.type = "float"
            self.value = str(value)
        elif isinstance(value, bool):
            self.type = "bool"
            self.value = str(value).lower()
        elif isinstance(value, (dict, list)):
            self.type = "json"
            self.value = json.dumps(value, ensure_ascii=False)
        else:
            self.type = "string"
            self.value = str(value)

    def to_dict(self) -> dict:
        """
        Convertit l'objet en dictionnaire avec la valeur typée.
        """
        return {
            "id": self.id,
            "key": self.key,
            "value": self.get_value(),
            "type": self.type,
            "description": self.description,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_setting(cls, session, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de paramètre depuis la base de données.
        Si la clé n'existe pas, retourne la valeur par défaut.
        """
        setting = session.query(cls).filter_by(key=key).first()
        if setting:
            return setting.get_value()
        return default

    @classmethod
    def set_setting(cls, session, key: str, value: Any,
                    description: Optional[str] = None,
                    category: str = "general") -> "Setting":
        """
        Définit ou met à jour un paramètre en base.
        Retourne l'objet Setting modifié ou créé.
        """
        setting = session.query(cls).filter_by(key=key).first()
        if setting:
            setting.set_value(value)
            if description is not None:
                setting.description = description
            if category:
                setting.category = category
        else:
            setting = cls(key=key, description=description, category=category)
            setting.set_value(value)
            session.add(setting)
        session.commit()
        return setting

    @classmethod
    def delete_setting(cls, session, key: str) -> bool:
        """
        Supprime un paramètre de la base.
        Retourne True si supprimé, False si non trouvé.
        """
        setting = session.query(cls).filter_by(key=key).first()
        if setting:
            session.delete(setting)
            session.commit()
            return True
        return False
