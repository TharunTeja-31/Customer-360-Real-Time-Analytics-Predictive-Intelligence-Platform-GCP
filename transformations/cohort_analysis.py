import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transformations.base_transformer import BaseAnalyticsModule

class CohortAnalysisJob(BaseAnalyticsModule):
    """
    Groups users by precise sign-up timeframe cohorts.
    Used for studying how customer behavior differs depending on when they arrived.
    """
    def __init__(self):
        super().__init__(module_name="Cohort_Analysis")
        
    def run_analysis(self):
        self.logger.info("Initiating Time-Series Cohort Mapping...")
        
        # Determine the earliest seen event time for each user
        query = """
            SELECT user_id, MIN(timestamp) as signup_date
            FROM events
            GROUP BY user_id
        """
        
        df = self.execute_query(query)
        if df.empty:
            self.logger.warning("No tracking data available for Cohort Mapping.")
            return

        try:
            # Cast using pandas for robust datetime formatting handling
            df['signup_date'] = pd.to_datetime(df['signup_date'])
            df['cohort_day'] = df['signup_date'].dt.strftime('%Y-%m-%d')
            
            # Aggregate cohort volume
            cohort_summary = df.groupby('cohort_day').size().reset_index(name='user_count')
            
            self.logger.info(f"Identified {len(cohort_summary)} distinct daily cohorts.")
            self.save_metric_table(cohort_summary, 'cohort_metrics')
        except Exception as e:
            self.logger.error(f"Pandas transformation logic failed during Cohort aggregation: {e}")

if __name__ == "__main__":
    job = CohortAnalysisJob()
    job.run_analysis()
