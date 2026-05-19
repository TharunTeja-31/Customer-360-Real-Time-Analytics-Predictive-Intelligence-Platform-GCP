import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transformations.base_transformer import BaseAnalyticsModule

class RetentionAnalysisJob(BaseAnalyticsModule):
    """
    Computes User Retention scoring across tracking lifecycle.
    """
    def __init__(self):
        super().__init__(module_name="Retention_Analysis")
        # Define a "Sticky User" structurally tracking > 3 meaningful interactions
        self.retention_event_threshold = 3
        
    def run_analysis(self):
        self.logger.info("Initiating Engagement and Retention Calculation...")
        
        query = """
            SELECT user_id, 
                   COUNT(DISTINCT event_type) as unique_actions, 
                   COUNT(timestamp) as total_interactions
            FROM events
            GROUP BY user_id
        """
        
        df = self.execute_query(query)
        if df.empty:
            self.logger.warning("Insufficient baseline data for Retention calculation.")
            return

        total_users = len(df)
        retained_df = df[df['total_interactions'] > self.retention_event_threshold]
        retained_users = len(retained_df)
        
        retention_rate = 0.0
        if total_users > 0:
            retention_rate = round((retained_users / total_users) * 100, 2)
        
        self.logger.info(f"Total Cohort: {total_users} | Retained: {retained_users} ({retention_rate}%)")
        
        retention_df = pd.DataFrame([{
            'total_users': total_users,
            'retained_users': retained_users,
            'retention_rate': retention_rate
        }])
        
        self.save_metric_table(retention_df, 'retention_metrics')

if __name__ == "__main__":
    job = RetentionAnalysisJob()
    job.run_analysis()
