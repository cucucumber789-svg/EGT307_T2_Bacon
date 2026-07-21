# EGT307_T2_BACON

## Task Assignment

| Name       | Task                                                 | Microservice             |
|------------|------------------------------------------------------|--------------------------|
| Wei Guan   | Notification Service, Frontend Dashboard             | notification-service     |
| Shun Wei   | Backend API, Docker & Kubernetes, Project Setup      | backend-api              |
| Derek      | Data Ingestion Service, Database Setup               | data-ingestion-service   |
| Louis      | ML Service                                           | ml-service               |

## Project Overview

## Problem Statement

Many environmental monitoring systems only display sensor readings without providing intelligent analysis or early detection of abnormal conditions. This requires users to manually monitor large amounts of data, which is time-consuming and may lead to delayed responses. The project aims to develop an AI-powered Smart Environmental Monitoring System that uses machine learning to analyse sensor data and detect abnormal environmental conditions. The system is built using a microservices architecture with Docker and Kubernetes to improve scalability, reliability, and ease of maintenance while supporting efficient deployment.

## Relevance of the problem towards the real world

In a nuclear plant, catching a sudden change in air quality is a race against an invisible hazard. Expecting a human operator to stare at screens and catch a tiny spike in gas levels or airborne particles among thousands of data points just isn't realistic—people get tired and miss things. By letting AI scan the data in the background, the plant can predict emergencies instead of just reacting to them. Smart environmental sensors sniff out tiny leaks and spot weird patterns, giving the safety team an early-warning notification hours before a real disaster hits.

## Objectives

1. Automated Analysis: Use machine learning to interpret sensor data instead of relying solely on raw readings

2. Early Detection: Identify abnormal environmental conditions (e.g., pollution spikes, temperature anomalies) before they escalate.

## Intended Benefits

1. Reduced Manual Monitoring: Eliminates the need for users to constantly track large datasets.
2. Timely Responses: Early warnings help prevent environmental hazards or mitigate their impact.
3. Scalability & Reliability: Kubernetes ensures the system can handle growing sensor networks and data streams.
4. Improved Accuracy: AI models can detect subtle anomalies that humans might miss.
5. Cross-Domain Applications: Supports monitoring of air quality, water pollution, biodiversity, and climate hazards.
6. Operational Efficiency: Microservices allow faster updates, easier maintenance, and resilience against failures.
7. Public Accountability: Provides transparent, scientifically valid insights for policymakers and communities.

## Data Source

## System Architecture

The Smart Environmental Monitoring System adopts a microservices architecture to provide scalable, reliable, and maintainable environmental monitoring. The system consists of four main components: a Frontend Dashboard, Backend API, Machine Learning Service, and Database, which communicate through RESTful APIs. This modular design enables independent development, deployment, and scaling of each service.

### Frontend Dashboard

The Frontend Dashboard provides a user-friendly interface for monitoring environmental conditions. It displays sensor data, anomaly detection results, and historical trends by sending REST API requests to the Backend API. Users can easily view environmental status and receive alerts without directly interacting with the database.

### Backend API Service

The Backend API Service acts as the central communication layer between all microservices. It receives requests from the frontend, retrieves and preprocesses the environmental dataset, communicates with the Machine Learning Service for predictions, and stores or retrieves data from the database before returning the results to the user.

### Machine Learning Service

The Machine Learning Service is responsible for analysing the environmental dataset and detecting abnormal conditions. It loads the trained machine learning model, processes the input data received from the Backend API, performs anomaly prediction, and returns the prediction results for storage and display.

### Database Service

The Database Service stores the imported environmental monitoring dataset, anomaly prediction results, and historical records. The Backend API retrieves data from the database for preprocessing and machine learning analysis, while prediction results are stored for future reference and visualisation. This provides persistent and centralized data storage, enabling efficient data management and historical analysis

## Docker Containerization

Each application component is packaged as a Docker container to provide a lightweight, portable, and consistent runtime environment across development, testing, and production. Docker eliminates dependency conflicts and ensures that the application behaves consistently regardless of the deployment platform.

## Kubernates Deployment

The containers are orchestrated using Kubernetes, which automates deployment, scaling, load balancing, and recovery of application services. Kubernetes continuously monitors the desired state of the system and automatically replaces failed Pods, ensuring high availability and fault tolerance. The orchestration platform also enables the application to scale horizontally by creating additional Pods when system workload increases.

## Issues and Limitations
