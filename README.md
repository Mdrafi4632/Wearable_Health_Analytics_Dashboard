# Wearable Health Analytics Dashboard

### Health Analytics Dashboard Using MongoDB: A NoSQL Approach to Multi-Source Wearable Data Integration

**Author:** Md Rafiul Islam Rafi  
**Course:** CISC 5640 - NoSQL Database Systems  
**Instructor:** Kyle Dent  
**Institution:** Fordham University

Website URL: https://mdrafi4632-health-analytics-dashboard-final-projectapp-eovewu.streamlit.app/

             https://share.streamlit.io/
             
             https://cloud.mongodb.com/v2/690cdc6f5c5ecd05203dc4e3#/clusters


## Overview

This project builds an interactive health analytics dashboard that brings together **Fitbit public data** and **personal WHOOP data** using **MongoDB Atlas, Python, and Streamlit**. It explores activity, sleep, recovery, and physiological trends while demonstrating how a document-oriented database can accommodate wearable datasets with different structures.

The system performs four main tasks:

1. **Multi-Source Data Integration** - process CSV exports from Fitbit and WHOOP while preserving source-specific fields.
2. **Data Cleaning and Transformation** - standardize dates, handle missing values, and compute analytical metrics through a Python ETL pipeline.
3. **Interactive Visualization** - explore activity, sleep, and physiological measurements through six Streamlit tabs.
4. **Comparative and Longitudinal Analysis** - examine differences between datasets and visualize approximately 2.5 years of personal WHOOP history.

**Project links supplied in the report:** [Streamlit Dashboard](https://mdrafi4632-health-analytics-dashboard-.streamlit.app) | [GitHub Repository](https://github.com/Mdrafi4632/health_analytics_dashboard)

## Data

The project combines two sources with different participants, observation periods, and measurement conventions.

| Source | Coverage reported in the paper | Main measurements |
| --- | --- | --- |
| Fitbit public dataset | 35 anonymized users over approximately two months in 2016 | Steps, calories, activity intensity, and sleep |
| Personal WHOOP exports | One user's approximately 2.5-year history | HRV, resting heart rate, strain, recovery, sleep, and workouts |

**Public dataset:** [Fitbit Fitness Tracker Data on Kaggle](https://www.kaggle.com/datasets/arashnic/fitbit)

### Input Files

| Source | Files listed in the report |
| --- | --- |
| Fitbit | `daily_activity.csv`, `sleep_day.csv` |
| WHOOP | `Physiological_rafi.csv`, `Sleeps_rafi.csv`, `workouts_rafi.csv` |

These filenames describe the report's inputs; the public dataset's original export names may differ.

## Methods and Tools

- **Language:** Python
- **Data processing:** Pandas
- **Database:** MongoDB Atlas
- **Database access:** PyMongo
- **Application framework:** Streamlit
- **Visualization:** Altair
- **Input format:** CSV exports
- **Deployment:** Streamlit Cloud with GitHub integration, as described in the report

## System Architecture

```text
Fitbit CSV Exports          WHOOP CSV Exports
          |                        |
          +-----------+------------+
                      |
           Python / Pandas ETL
                      |
                MongoDB Atlas
             Five Collections
                      |
                PyMongo Queries
                      |
        Pandas Transformations and Aggregation
                      |
             Streamlit Dashboard
                Altair Charts
```

The IEEE report describes a MongoDB Atlas cluster deployed as a **three-node replica set on AWS in `us-east-1`**. Source data is stored in separate MongoDB collections. The application retrieves relevant records and uses Pandas for date-based merging, grouping, and metric computation before rendering visualizations.

## ETL Pipeline

The report describes the following extract, transform, and load workflow:

1. **Extract** Fitbit and WHOOP records from CSV exports.
2. **Normalize dates** from source-specific timestamp formats into consistent date keys.
3. **Clean records** by removing irrelevant columns and imputing or flagging missing values.
4. **Derive metrics** such as daily averages, sleep efficiency, strain-normalized recovery scores, and six-month aggregates.
5. **Load documents** into the appropriate MongoDB collections.
6. **Prepare chart data** through application-level aggregation and reshaping.

The report defines sleep efficiency as:

```text
Sleep Efficiency (%) = (Total Minutes Asleep / Total Minutes in Bed) × 100
```

Sleep efficiency and WHOOP sleep performance are different metrics and should be interpreted separately.

## MongoDB Collection Design

| Collection | Source | Purpose |
| --- | --- | --- |
| `daily_activity` | Fitbit | Daily steps, calories, and activity intensity |
| `sleep_day` | Fitbit | Sleep duration and related daily measurements |
| `physiologicals_rafi` | WHOOP | Physiological measurements and recovery-related data |
| `sleeps_rafi` | WHOOP | Sleep measurements and performance |
| `workouts_rafi` | WHOOP | Workout type, duration, and strain |

Keeping each data stream separate preserves differences in fields and document structure. Analytical alignment happens in the application rather than through a single enforced database schema.

## Dashboard Features

The dashboard is organized into six interactive tabs:

| Tab | Features |
| --- | --- |
| **Project Overview** | Project context, data sources, and system overview |
| **Fitbit Activity** | User selection, steps, calories, intensity composition, and summaries |
| **Fitbit Sleep Activity** | Sleep duration, weekday/weekend comparisons, efficiency, and daily patterns |
| **WHOOP Activity** | HRV and resting heart rate trends, monthly averages, strain, and workout intensity |
| **WHOOP Sleep Activity** | Sleep performance, monthly trends, and longer-term summaries |
| **Comparisons** | Side-by-side summaries of calories and sleep measurements across datasets |

The Fitbit views support selecting individual users. WHOOP views focus on a single user's longitudinal history, including monthly and six-month summaries.

## Results and Findings

The report presents exploratory findings rather than predictive model evaluation.

| Analysis area | Observations reported |
| --- | --- |
| Fitbit activity | Daily step counts and estimated calorie expenditure show a positive association; low-intensity and sedentary time account for much of recorded activity time |
| Fitbit sleep | The examined users show longer sleep on weekends than weekdays, alongside day-to-day variation; no formal significance test was performed |
| WHOOP physiology | HRV varies over time, while average resting heart rate is reported at approximately **53 bpm** |
| WHOOP workouts | Endurance activities show higher recorded strain than recreational activities in the analyzed data |
| WHOOP sleep | Average device-estimated sleep need is **9.3 hours**, with average sleep performance of **61%** |
| Cross-source summaries | The personal WHOOP dataset shows slightly higher average calorie expenditure, while the Fitbit cohort shows longer average sleep duration |

These observations come from the accompanying report and have not been independently recomputed. Cross-source differences reflect different users, periods, and device algorithms; they do not establish device accuracy or causal relationships.

### WHOOP Sleep Summary

| Metric | Value reported in the paper |
| --- | ---: |
| Average device-estimated sleep need | 9.3 hours |
| Average sleep performance | 61% |
| Best nightly sleep performance | 100% |
| Worst nightly sleep performance | 7% |

Six-month summaries show higher sleep duration during the second half of 2024 and the first half of 2025, followed by a decline in mid-2025. These are descriptive observations from one user's history.

## Evaluation Approach

The report evaluates the implementation against three criteria:

1. Store Fitbit and WHOOP records in a shared database environment.
2. Produce activity, sleep, and physiological analysis through the dashboard.
3. Demonstrate the practical suitability of a document-oriented design for heterogeneous wearable data.

This is an implementation-focused evaluation. It does not include a controlled database performance benchmark.

## Technical Contributions

- Integrates heterogeneous wearable exports into a shared MongoDB Atlas backend.
- Preserves source-specific document structures across five collections.
- Connects cloud storage to an interactive Streamlit application using PyMongo.
- Converts query results into Pandas dataframes for aggregation and Altair visualization.
- Provides multi-user Fitbit exploration and multi-year personal WHOOP analysis.

## Limitations

- **Different populations:** The Fitbit cohort and personal WHOOP history are not paired measurements of the same participants.
- **Different time periods:** Fitbit records are from 2016, while WHOOP records cover a separate multi-year period. Calendar overlap must be checked before any date-aligned cross-source analysis.
- **Metric definitions:** Sleep performance, sleep efficiency, calorie estimates, and other device measurements are not automatically interchangeable.
- **Evaluation scope:** The report does not provide a controlled relational-database benchmark or query-latency measurements, so no quantitative database performance advantage is claimed here.
- **Ingestion:** The described implementation relies on CSV exports; API ingestion is future work.

## Future Work

- Automate ingestion through Fitbit and WHOOP APIs.
- Move suitable computations into MongoDB aggregation pipelines.
- Explore predictive modeling for recovery and sleep trends.
- Incorporate additional sources such as Apple Health and Garmin Connect.
- Add authentication and separate access to each user's data.
- Benchmark the implementation against a relational database baseline.

## Running the Project

The report identifies Python, Pandas, PyMongo, Streamlit, Altair, and a MongoDB Atlas connection as the main components. Exact dependency versions, application entry points, connection settings, and import commands should be documented after checking the source files.

Only the report was supplied when preparing this README; installation and execution commands have not been verified.

## Technical Report

**Health Analytics Dashboard Using MongoDB: A NoSQL Approach to Multi-Source Wearable Data Integration** provides the architecture, implementation details, dashboard examples, and analysis in IEEE format. Include `Health_Analytics_IEEE.pdf` in the repository to accompany the code.

## Acknowledgments

- **Fordham University, CISC 5640** - academic context
- **Kyle Dent** - course instructor
- **Fitbit Fitness Tracker Data / Kaggle** - public dataset
- **WHOOP personal exports** - longitudinal wearable data
