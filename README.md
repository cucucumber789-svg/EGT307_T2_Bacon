# EGT307_T2_BACON

## Members 

- Wei Guan - 
- Shun Wei - 
- Derek - 

## Project Overview

## Problem Statement

Many environmental monitoring systems only display sensor readings without providing intelligent analysis or early detection of abnormal conditions. This requires users to manually monitor large amounts of data, which is time-consuming and may lead to delayed responses. The project aims to develop an AI-powered Smart Environmental Monitoring System that uses machine learning to analyse sensor data and detect abnormal environmental conditions. The system is built using a microservices architecture with Docker and Kubernetes to improve scalability, reliability, and ease of maintenance while supporting efficient deployment.

## Relevance of the problem towards the real world

In the real world, catching an environmental issue early is a race against the clock. If a cooling system fails in a data center, millions of dollars of hardware can overheat and melt in minutes. If a gas sensor spikes in a chemical plant, you have a massive safety hazard on your hands. Expecting a human operator to sit there, stare at thousands of raw data points on a screen, and spot these tiny anomalies before it's too late just isn't realistic. People get tired, overwhelmed, and inevitably miss things.

By letting AI constantly scan the data, the system switches from being reactive to predictive. Instead of sounding an alarm after everything goes wrong, the AI catches subtle patterns early, giving teams a heads-up hours before a breakdown even happens. On top of that, using Docker and Kubernetes fixes a major engineering headache: scalability. A system might start with fifty sensors and quickly grow to thousands. This architecture ensures the platform handles the massive data load smoothly, whether it's running in a single building or across an entire smart city.

## Objectives

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
