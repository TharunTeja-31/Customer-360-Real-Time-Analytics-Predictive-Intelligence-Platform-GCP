import os
from dataclasses import dataclass
from typing import List

@dataclass
class PlatformConfig:
    """
    Centralized configuration for the Customer 360 Platform.
    Features toggle to switch between Local SQLite and GCP BigQuery/PubSub.
    """
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    LOGS_DIR: str = os.path.join(BASE_DIR, 'logs')
    STORAGE_DIR: str = os.path.join(BASE_DIR, 'storage')
    CSV_EVENTS_PATH: str = os.path.join(LOGS_DIR, 'raw_events.csv')
    SQLITE_DB_PATH: str = os.path.join(STORAGE_DIR, 'customer_360.db')
    
    # Execution Environment
    USE_GCP: bool = False  # Set to True to use Pub/Sub and BigQuery
    
    # GCP Configurations
    GCP_PROJECT_ID: str = "customer-360-492614"
    GCP_PUBSUB_TOPIC: str = "customer-events"
    GCP_PUBSUB_SUB: str = "customer-events-sub"
    GCP_BQ_DATASET: str = "customer_360"
    
    # Event Generation Settings
    NUM_USERS: int = 500
    EVENT_TYPES: tuple = ('login', 'product_view', 'add_to_cart', 'purchase')
    SIMULATION_WAIT_MIN_SEC: float = 0.5
    SIMULATION_WAIT_MAX_SEC: float = 2.0
    
    # ML Model Settings
    KMEANS_CLUSTERS: int = 3
    CHURN_INACTIVITY_THRESHOLD_DAYS: int = 30
    
    def __post_init__(self):
        """Ensure directories exist upon initialization."""
        os.makedirs(self.LOGS_DIR, exist_ok=True)
        os.makedirs(self.STORAGE_DIR, exist_ok=True)

config = PlatformConfig()
