# ==========================================================================
#  NexusDL 2.0 - Base SQLAlchemy
#  Fichier : backend/app/models/base.py
#  Description : Instance `Base` partagée par tous les modèles SQLAlchemy.
#  Version : 2.0.0
# ==========================================================================

from sqlalchemy.orm import declarative_base

Base = declarative_base()
