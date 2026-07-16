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

### Frontend Service

The frontend provides a web-based dashboard that allows users to monitor real-time environmental conditions, view historical sensor data, receive anomaly alerts, and visualize prediction results. User requests are sent to the Backend API through RESTful HTTP communication.

### Backend API Service

The Backend API acts as the central communication layer of the system. It receives sensor readings, validates incoming data, communicates with the machine learning service, stores information in the database, and returns processed results to the frontend. This service also exposes REST API endpoints for all client requests.

### Machine Learning Service

The Machine Learning Service performs data preprocessing and anomaly detection using the trained machine learning model. Incoming sensor readings are cleaned, transformed, and analysed to determine whether environmental conditions are normal or abnormal. The prediction results are then returned to the Backend API for storage and presentation.

### Database Service

The database stores sensor readings, prediction results, historical records, and application data. Persistent storage is provided using Kubernetes Volumes to ensure that data remains available even if application Pods are restarted or replaced.

## Docker Containerization

## Kubernates Deployment

## Issues and Limitations
