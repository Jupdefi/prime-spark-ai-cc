"""
Airflow DAG: Edge to Cloud Data Synchronization
Syncs data from edge devices to cloud analytics database
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import json


default_args = {
    'owner': 'prime-spark-ai',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'edge_to_cloud_sync',
    default_args=default_args,
    description='Synchronize edge device data to cloud analytics',
    schedule_interval=timedelta(minutes=15),
    catchup=False,
    tags=['edge', 'sync', 'analytics'],
)


def extract_edge_metrics(**context):
    """Extract metrics from edge devices"""
    # This would actually pull from edge Redis/local storage
    # For now, returning mock data
    metrics = {
        'device_id': 'control-pc-1',
        'metrics': [
            {'name': 'cpu_usage', 'value': 45.2, 'timestamp': datetime.utcnow()},
            {'name': 'memory_usage', 'value': 60.5, 'timestamp': datetime.utcnow()},
            {'name': 'disk_usage', 'value': 70.1, 'timestamp': datetime.utcnow()},
        ]
    }

    # Push to XCom for next task
    context['task_instance'].xcom_push(key='metrics', value=json.dumps(metrics, default=str))
    return "Extracted metrics successfully"


def transform_metrics(**context):
    """Transform and validate metrics"""
    # Pull from XCom
    metrics_json = context['task_instance'].xcom_pull(key='metrics', task_ids='extract_edge_metrics')
    metrics = json.loads(metrics_json)

    # Transform/validate data
    transformed = {
        'device_id': metrics['device_id'],
        'metrics': [
            {
                **m,
                'timestamp': str(m['timestamp']),
                'validated': True
            }
            for m in metrics['metrics']
        ]
    }

    context['task_instance'].xcom_push(key='transformed_metrics', value=json.dumps(transformed))
    return "Transformed metrics successfully"


def load_to_timescaledb(**context):
    """Load metrics into TimescaleDB"""
    # Pull transformed metrics
    metrics_json = context['task_instance'].xcom_pull(key='transformed_metrics', task_ids='transform_metrics')
    metrics = json.loads(metrics_json)

    # Get PostgreSQL hook
    pg_hook = PostgresHook(postgres_conn_id='timescaledb')

    # Insert metrics
    for metric in metrics['metrics']:
        pg_hook.run("""
            INSERT INTO device_metrics (time, device_id, metric_name, value, tags)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (time, device_id, metric_name) DO UPDATE
            SET value = EXCLUDED.value;
        """, parameters=(
            metric['timestamp'],
            metrics['device_id'],
            metric['name'],
            metric['value'],
            json.dumps({'source': 'edge_sync'})
        ))

    return f"Loaded {len(metrics['metrics'])} metrics to TimescaleDB"


# Define tasks
extract_task = PythonOperator(
    task_id='extract_edge_metrics',
    python_callable=extract_edge_metrics,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_metrics',
    python_callable=transform_metrics,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_to_timescaledb',
    python_callable=load_to_timescaledb,
    dag=dag,
)

# Set dependencies
extract_task >> transform_task >> load_task
