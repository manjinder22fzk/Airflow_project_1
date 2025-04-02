# Flight Booking Data Pipeline

## 📌 Project Overview
**Objective:** Built an automated pipeline to process flight booking data, generate business insights (route performance, booking trends), and load them into an analytics warehouse.

### 🔹 Key Components
- **Orchestration:** Apache Airflow (DAGs to manage workflows).
- **Processing:** PySpark on Dataproc Serverless (transformations, aggregations).
- **Storage:** Google Cloud Storage (raw data) + BigQuery (processed data).
- **Infrastructure:** Fully on GCP (Composer for Airflow, Dataproc for Spark).
- **CI/CD:** GitHub Actions (auto-deploy to dev/prod environments).

---

## ⚙️ Technical Deep Dive

### 🔄 A. Data Flow
#### **Ingestion**
- Airflow DAG starts when a new file (`flight_booking.csv`) lands in GCS (monitored via `GCSObjectExistenceSensor`).
- Environment-specific paths (dev/prod) resolved using Airflow Variables.

#### **Processing**
- PySpark job performs:
  - **Feature engineering:** Weekend flags, lead-time categories, success rates.
  - **Aggregations:** Route-level metrics (avg. flight duration, bookings) and origin-country insights.
  - **Optimization:** Used Dataproc Serverless to avoid cluster management.

#### **Loading**
- Results written to **BigQuery**:
  - Raw transformed data.
  - Two aggregated tables (**route insights, booking origin insights**).

### 🔧 B. Environment Management
- **Isolation:** Separate `variables.json` for dev/prod (different GCS paths, BigQuery datasets).
- **Safety:** CI/CD deploys to **prod only when merged to the main branch**.

### 🚀 C. Deployment (CI/CD)
- **GitHub Actions:**
  - Auto-deploys Airflow DAGs, Spark jobs, and variables to GCP.
  - Uses `gcloud CLI` to sync resources to Composer/Dataproc.
- **Secrets Management:** GCP credentials stored in GitHub Secrets.

---

## 💡 Key Technical Decisions
- **Why Airflow?** Chose for its native GCP integration (Composer), dependency management, and monitoring.
- **Why Dataproc Serverless?** Eliminated cluster overhead while retaining Spark’s power.
- **Why BigQuery?** Serverless, fast queries, and seamless Spark integration.

---

## 🔥 Challenges & Solutions
- **Challenge:** Avoiding dev/prod conflicts.  
  ✅ **Solution:** Isolated resources via Airflow Variables and separate GCS/BigQuery paths.
- **Challenge:** Handling large data volumes.  
  ✅ **Solution:** Spark optimizations (partitioning, predicate pushdown in BigQuery).

---

## 🛠 Skills Demonstrated
- **Cloud Platforms:** GCP (Composer, Dataproc, GCS, BigQuery, IAM).
- **Data Engineering:** PySpark, ETL design, partitioning strategies.
- **DevOps:** CI/CD (GitHub Actions), infra-as-code (YAML, CLI).
- **Observability:** Airflow logging, Spark UI debugging.

---

## 📊 Business Impact
- **Actionable Insights:** Teams can analyze route profitability and booking patterns.
- **Automation:** Reduced manual effort by **80%** (scheduled + trigger-based runs).
