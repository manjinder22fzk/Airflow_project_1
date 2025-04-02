from datetime import datetime, timedelta
import uuid  # Import UUID for unique batch IDs
from airflow import DAG
from airflow.providers.google.cloud.operators.dataproc import DataprocCreateBatchOperator
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.models import Variable

# DAG default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 4, 1),
}

# Define the DAG
with DAG(
    dag_id="flight_booking_dataproc_bq_dag",
    default_args=default_args,
    schedule_interval=None,  # Trigger manually or on-demand
    catchup=False,
) as dag:

    # Fetch environment variables
    env = Variable.get("env", default_var="dev")
    gcs_bucket = Variable.get("gcs_bucket", default_var="money_airflow-projects-gds")
    bq_project = Variable.get("bq_project", default_var="airflow-shashank")
    bq_dataset = Variable.get("bq_dataset", default_var=f"flight_data_{env}")
    tables = Variable.get("tables", deserialize_json=True)

    # Extract table names from the 'tables' variable
    transformed_table = tables["transformed_table"]
    route_insights_table = tables["route_insights_table"]
    origin_insights_table = tables["origin_insights_table"]

    # Generate a unique batch ID using UUID
    batch_id = f"flight-booking-batch-{env}-{str(uuid.uuid4())[:8]}"  # Shortened UUID for brevity

    # # Task 1: File Sensor for GCS
    file_sensor = GCSObjectExistenceSensor(
        task_id="check_file_arrival",
        bucket=gcs_bucket,
        object=f"flight_project/source-{env}/flight_booking.csv",  # Full file path in GCS
        google_cloud_conn_id="google_cloud_default",  # GCP connection
        timeout=300,  # Timeout in seconds
        poke_interval=30,  # Time between checks
        mode="poke",  # Blocking mode
    )

    # Task 2: Submit PySpark job to Dataproc Serverless
    batch_details = {
        "pyspark_batch": {
            "main_python_file_uri": f"gs://{gcs_bucket}/flight_project/spark-job/spark_transformation_job.py",  # Main Python file
            "python_file_uris": [],  # Python WHL files
            "jar_file_uris": [],  # JAR files
            "args": [
                f"--env={env}",
                f"--bq_project={bq_project}",
                f"--bq_dataset={bq_dataset}",
                f"--transformed_table={transformed_table}",
                f"--route_insights_table={route_insights_table}",
                f"--origin_insights_table={origin_insights_table}",

                # "--conf", "spark.executor.instances=1",
                # "--conf", "spark.executor.cores=2",
                # "--conf", "spark.driver.cores=2",
                # "--conf", "spark.executor.memory=2g",
                # "--conf", "spark.driver.memory=2g",
                # "--conf", "spark.dynamicAllocation.enabled=false",  
                # "--conf", "spark.executor.memoryOverhead=512m",  
                # "--conf", "spark.driver.memoryOverhead=512m",  
                # "--conf", "spark.dataproc.allow.zero.workers=true",
                # "--conf", "spark.dataproc.resourceAllocationPolicy=NONE",  # Enforce manual allocation  
                # "--conf", "spark.yarn.executor.memoryOverhead=512m"  

            ]
        },
        "runtime_config": {
            "version": "2.2",  # Specify Dataproc version (if needed),
            "container_image": "europe-docker.pkg.dev/cloud-dataproc/spark/spark-2.4:2.4"
        },
        "environment_config": {
            "execution_config": {
                "service_account": "745219382502-compute@developer.gserviceaccount.com",
                "network_uri": "projects/airflow-shashank/global/networks/default",
                "subnetwork_uri": "projects/airflow-shashank/regions/europe-north1/subnetworks/default",
                # HARD LIMITS ▼
                "min_cpu_platform": "Automatic",
                "kms_key": "",  # Required field (can be empty)
                "network_tags": ["low-resource-job"],  # Helps identify
                "metadata": {
                    "spark-serverless-enforcement": "true",
                    "max-vcpu": "4",  # Hard cap (2 driver + 2 executor)
                    "max-memory-gb": "8"  # 4GB per core
                }
            }
        },
    }

    pyspark_task = DataprocCreateBatchOperator(
        task_id="run_spark_job_on_dataproc_serverless",
        batch=batch_details,
        batch_id=batch_id,
        project_id="airflow-shashank",
        region="europe-north1",
        gcp_conn_id="google_cloud_default",
    )

    # Task Dependencies
    file_sensor >> pyspark_task