import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from transformations.base_transformer import BaseAnalyticsModule

class ChurnPredictionModel(BaseAnalyticsModule):
    """
    Churn heuristic calculation mapping logic.
    Inherits BaseAnalyticsModule to seamlessly switch between Local SQL and GCP BigQuery.
    """
    def __init__(self):
        super().__init__(module_name="ChurnModel")
        
    def fetch_transaction_behavior(self) -> pd.DataFrame:
        query = """
        SELECT user_id, 
               COUNT(timestamp) as event_count,
               SUM(CASE WHEN event_type='purchase' THEN 1 ELSE 0 END) as purchase_count
        FROM events
        GROUP BY user_id
        """
        return self.execute_query(query)

    def run_prediction(self) -> None:
        self.logger.info("Executing Churn Detection Pipeline...")
        df = self.fetch_transaction_behavior()
        
        if df.empty:
            self.logger.warning("Empty dataset. Skipping churn.")
            return

        try:
            # Map heuristics
            df['is_at_risk'] = ((df['event_count'] <= 2) & (df['purchase_count'] == 0)).astype(int)
            at_risk_count = int(df['is_at_risk'].sum())
            self.logger.info(f"Detected {at_risk_count} at-risk users.")
            
            # Push predictions to operational store natively via base function
            self.save_metric_table(df, 'churn_metrics')
            self.logger.info("Churn pipeline completed context injection.")
        except Exception as e:
            self.logger.error(f"Pipeline error: {e}")

if __name__ == "__main__":
    model = ChurnPredictionModel()
    model.run_prediction()
