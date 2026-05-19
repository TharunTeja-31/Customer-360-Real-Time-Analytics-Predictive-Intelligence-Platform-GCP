import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from utils.logger import get_logger
from transformations.base_transformer import BaseAnalyticsModule

class CustomerSegmentationModel(BaseAnalyticsModule):
    """
    Unsupervised ML model for clustering. 
    Now inherits BaseAnalyticsModule to seamlessly switch between Local Database and BigQuery.
    """
    def __init__(self):
        super().__init__(module_name="SegmentationModel")
        self.n_clusters = config.KMEANS_CLUSTERS
        self.scaler = StandardScaler()
        self.model = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        self.model_save_path = os.path.join(config.STORAGE_DIR, 'segmentation_kmeans.pkl')

    def fetch_training_data(self) -> pd.DataFrame:
        query = """
            SELECT user_id, 
                   COUNT(timestamp) as frequency, 
                   SUM(amount) as monetary
            FROM events
            GROUP BY user_id
        """
        return self.execute_query(query)

    def train_and_predict(self) -> None:
        self.logger.info("Executing KMeans Segmentation Model...")
        df = self.fetch_training_data()
        
        if df.empty or len(df) < self.n_clusters:
            self.logger.warning("Insufficient samples.")
            return

        try:
            features = df[['frequency', 'monetary']].fillna(0)
            scaled_features = self.scaler.fit_transform(features)
            
            df['segment_id'] = self.model.fit_predict(scaled_features)
            monetary_means = df.groupby('segment_id')['monetary'].mean().sort_values()
            
            labels = {
                monetary_means.index[0]: 'Low Value',
                monetary_means.index[1]: 'Medium Value',
                monetary_means.index[2]: 'High Value'
            }
            
            df['segment_label'] = df['segment_id'].map(labels)
            
            # Save labeled outputs back to data warehouse (BQ or Local) via base class mapper
            self.save_metric_table(df, 'user_segments')
            
            joblib.dump(self.model, self.model_save_path)
            self.logger.info(f"Model saved -> {len(df)} users segmented.")
        except Exception as e:
            self.logger.error(f"Unsupervised Pipeline failure: {e}")

if __name__ == "__main__":
    segmenter = CustomerSegmentationModel()
    segmenter.train_and_predict()
