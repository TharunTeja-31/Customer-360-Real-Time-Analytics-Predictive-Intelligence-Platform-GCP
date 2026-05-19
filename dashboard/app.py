from flask import Flask, render_template
import sqlite3
import pandas as pd
import os
import sys

# Connect core configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from config import config
from utils.logger import get_logger

try:
    from google.cloud import bigquery
except ImportError:
    pass

app = Flask(__name__)
logger = get_logger("DashboardApp")

def fetch_table(query: str, as_dict: bool = True):
    """Facade for fetching tables irrespective of underlying DB environment (SQLite or GCP)."""
    if config.USE_GCP:
        try:
            client = bigquery.Client(project=config.GCP_PROJECT_ID)
            # Map simple table names to fully qualified BQ table IDs
            bq_query = query.replace('FROM events', f'FROM `{config.GCP_PROJECT_ID}.{config.GCP_BQ_DATASET}.events`')
            for target in ['ltv_metrics', 'funnel_metrics', 'user_segments', 'churn_metrics', 'cohort_metrics', 'retention_metrics']:
                bq_query = bq_query.replace(f'FROM {target}', f'FROM `{config.GCP_PROJECT_ID}.{config.GCP_BQ_DATASET}.{target}`')
            
            query_job = client.query(bq_query)
            df = query_job.to_dataframe()
            return df.to_dict(orient='records') if as_dict else df
        except Exception as e:
            logger.error(f"GCP BigQuery Access attempted but failed: {e}")
            logger.info("Falling back to local SQLite to avoid blocking.")

    # Standard local approach / Fallback
    if not os.path.exists(config.SQLITE_DB_PATH):
        raise FileNotFoundError(f"Local database file missing at {config.SQLITE_DB_PATH}")
    with sqlite3.connect(config.SQLITE_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        df = pd.read_sql(query, conn)
        return df.to_dict(orient='records') if as_dict else df

@app.route('/')
def index():
    logger.info("Handling Request: Dashboard Index")
    
    # Defaults
    stats = { 'total_users': 0, 'total_revenue': 0.0, 'total_events': 0 }
    top_customers = []
    funnel_data = []
    segment_data = []
    cohort_data = []
    retention_metrics = {'total_users': 0, 'retained_users': 0, 'retention_rate': 0.0}
    churn_metrics = {'at_risk_count': 0, 'total_evaluated': 0, 'churn_rate': 0.0}

    # Extract Stats
    try:
        stats_query = """
            SELECT 
                COUNT(DISTINCT user_id) as total_users,
                ROUND(SUM(amount), 2) as total_revenue,
                COUNT(*) as total_events
            FROM events
        """
        raw_stats = fetch_table(stats_query, as_dict=False)
        if not raw_stats.empty:
            stats = raw_stats.iloc[0].to_dict()
    except Exception as e:
        logger.warning(f"Global Stats missing: {e}")

    # Extract Top Customers (Already presented as "Top Customers Table")
    try:
        top_query = "SELECT user_id, total_ltv FROM ltv_metrics ORDER BY total_ltv DESC LIMIT 5"
        top_customers = fetch_table(top_query)
    except Exception:
        logger.debug("LTV Metrics Table missing.")

    # Extract Funnel
    try:
        funnel_query = "SELECT stage, user_count FROM funnel_metrics"
        funnel_data = fetch_table(funnel_query)
    except Exception:
        logger.debug("Funnel Metrics missing.")

    # Extract Segments
    try:
        segments_query = """
            SELECT segment_label as label, COUNT(user_id) as count
            FROM user_segments
            GROUP BY segment_label
        """
        segment_data = fetch_table(segments_query)
    except Exception:
        logger.debug("Segmentation mapping missing.")
        
    # Extract Cohorts
    try:
        cohort_query = "SELECT cohort_day, user_count FROM cohort_metrics ORDER BY cohort_day ASC"
        cohort_data = fetch_table(cohort_query)
    except Exception:
        logger.debug("Cohort Metrics missing.")

    # Extract Retention
    try:
        retention_query = "SELECT total_users, retained_users, retention_rate FROM retention_metrics"
        raw_retention = fetch_table(retention_query, as_dict=False)
        if not raw_retention.empty:
            retention_metrics = raw_retention.iloc[0].to_dict()
    except Exception:
        logger.debug("Retention Metrics missing.")
        
    # Extract Churn Metric counts for Dashboard rendering
    try:
        churn_query = "SELECT SUM(is_at_risk) as at_risk_count, COUNT(*) as total_evaluated FROM churn_metrics"
        raw_churn = fetch_table(churn_query, as_dict=False)
        if not raw_churn.empty:
            data = raw_churn.iloc[0]
            churn_metrics['at_risk_count'] = int(data['at_risk_count'])
            churn_metrics['total_evaluated'] = int(data['total_evaluated'])
            if churn_metrics['total_evaluated'] > 0:
                churn_metrics['churn_rate'] = round((churn_metrics['at_risk_count'] / churn_metrics['total_evaluated']) * 100, 2)
    except Exception as e:
        logger.debug(f"Churn missing: {e}")

    return render_template('index.html', 
                            stats=stats, 
                            top_customers=top_customers,
                            funnel_data=funnel_data,
                            segment_data=segment_data,
                            cohort_data=cohort_data,
                            retention_metrics=retention_metrics,
                            churn_metrics=churn_metrics,
                            platform_env="GCP cloud" if config.USE_GCP else "Local Storage")

if __name__ == '__main__':
    logger.info("Warming up Flask Dashboard...")
    app.run(host='0.0.0.0', port=5000, debug=True)
