# EGT307_T2_BACON

## Task Assignment

| Name       | Task                                                                           | Microservice             |
|------------|--------------------------------------------------------------------------------|--------------------------|
| Wei Guan   | Notification Service, Frontend Dashboard                                       | notification-service     |
| Shun Wei   | Backend API, Docker & Kubernetes, System Architecture, System Integration      | backend-api              |
| Derek      | Data Ingestion Service, Database Setup                                         | data-ingestion-service   |
| Louis      | ML Service                                                                     | ml-service               |

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

The Smart Environmental Monitoring System uses a microservices architecture to provide a flexible and reliable solution for monitoring environmental conditions. The system consists of six services: the Data Ingestion Service, which collects sensor data; the Machine Learning Service, which analyses the data and detects abnormal conditions; the Notification Service, which sends Telegram alerts when abnormal readings are detected; the Backend API, which manages communication between services; the Database, which stores sensor data and prediction results; and the Frontend Dashboard, where users can view live data, AI predictions, and notifications.

Using a microservices architecture improves modularity by giving each service a specific responsibility, making it easier to develop and maintain. It also improves scalability, as each service can be deployed or scaled independently based on demand. Since the services operate separately, the system is also more fault tolerant, as a failure in one service is less likely to affect the others, allowing the rest of the application to continue running.

### Data Ingestion

The Data Ingestion Service is responsible for collecting environmental sensor data and transferring it to the system for processing. It receives real-time readings such as temperature, humidity, CO2 concentration, and air quality from IoT sensors through REST APIs. The service validates and formats the incoming data before storing it in the database and forwarding it to the Machine Learning Service for analysis. By separating data collection into its own microservice, the system achieves better scalability, reliability, and maintainability, allowing new sensors or data sources to be integrated with minimal changes to the overall application.

### Database Service

The Database Service stores the imported environmental monitoring dataset, anomaly prediction results, and historical records. The Backend API retrieves data from the database for preprocessing and machine learning analysis, while prediction results are stored for future reference and visualisation. This provides persistent and centralized data storage, enabling efficient data management and historical analysis.

### Backend API Service

The Backend API Service acts as the communication layer between all microservices. It receives requests from the Frontend Dashboard, retrieves sensor data from the database, sends data to the Machine Learning Service for prediction, stores the prediction results, and returns the processed information to the user.

### Machine Learning Service

The Machine Learning Service receives validated sensor data from the Backend API, analyses it using the trained model, and returns prediction results. If an abnormal condition is detected, the Backend API stores the result in the database and triggers the Notification Service to send a Telegram alert.

### Notification Service

The Notification Service is used to send alerts when the system detects abnormal environmental conditions. After the AI model analyses the sensor data, the service checks whether any readings, such as temperature, humidity, CO2, or air quality, exceed the predefined threshold. If an abnormal condition is detected, an alert is automatically sent to a Telegram bot using the Telegram Bot API. This allows users to receive notifications instantly on their phones and take action as soon as possible. Separating the notification feature into its own microservice also makes it easier to maintain, update, and scale without affecting the other services in the system.

### Frontend Dashboard

The Frontend Dashboard provides a user-friendly interface for monitoring environmental conditions. It displays sensor data, anomaly detection results, and historical trends by sending REST API requests to the Backend API. Users can easily view environmental status and receive alerts without directly interacting with the database.

## Docker Containerization

Each application component is packaged as a Docker container to provide a lightweight, portable, and consistent runtime environment across development, testing, and production. Docker eliminates dependency conflicts and ensures that the application behaves consistently regardless of the deployment platform.

## Kubernates Deployment

The containers are orchestrated using Kubernetes, which automates deployment, scaling, load balancing, and recovery of application services. Kubernetes continuously monitors the desired state of the system and automatically replaces failed Pods, ensuring high availability and fault tolerance. The orchestration platform also enables the application to scale horizontally by creating additional Pods when system workload increases.

## Issues and Limitations
