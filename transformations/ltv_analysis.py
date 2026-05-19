import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transformations.base_transformer import BaseAnalyticsModule

class LTVAnalysisJob(BaseAnalyticsModule):
    """
    Calculates Customer Lifetime Value (LTV) across all historical transactions.
    """
    def __init__(self):
        super().__init__(module_name="LTV_Analysis")
        
    def run_analysis(self):
        self.logger.info("Initiating LTV Analysis Calculation...")
        
        query = """
            SELECT user_id, SUM(amount) as total_ltv, COUNT(user_id) as event_count
            FROM events
            GROUP BY user_id
            HAVING total_ltv > 0
            ORDER BY total_ltv DESC
        """
        
        df = self.execute_query(query)
        if df.empty:
            self.logger.warning("No purchase data available for LTV Calculation.")
            return

        self.logger.info(f"Analyzed LTV for {len(df)} purchasing customers.")
        self.save_metric_table(df, 'ltv_metrics')

if __name__ == "__main__":
    job = LTVAnalysisJob()
    job.run_analysis()
