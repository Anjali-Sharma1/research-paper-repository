"""
scripts/seed_sample_data.py
Seeds 100+ realistic sample research papers into the RPRMS database.

Run from project root:
    python scripts/seed_sample_data.py

Safe to run multiple times — skips papers whose title already exists.
Creates real minimal PDF files so Download works immediately.
"""
import sys, os, datetime, bcrypt

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection

UPLOAD_DIR = "uploads/papers"
QR_DIR     = "uploads/qr"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(QR_DIR,     exist_ok=True)


# ── PDF helper ────────────────────────────────────────────────────────────────
def make_pdf(title: str, abstract: str, keywords: str, path: str):
    """Generate a valid sample PDF. Uses reportlab if installed, else pure-Python fallback."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import cm

        doc    = SimpleDocTemplate(path, pagesize=A4,
                                   leftMargin=2*cm, rightMargin=2*cm,
                                   topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story  = [
            Paragraph(title, styles["Title"]),
            Spacer(1, 0.4*cm),
            Paragraph("Abstract", styles["Heading2"]),
            Paragraph(abstract[:900] + "...", styles["BodyText"]),
            Spacer(1, 0.3*cm),
            Paragraph(f"<b>Keywords:</b> {keywords}", styles["BodyText"]),
            Spacer(1, 0.3*cm),
            Paragraph("<i>RPRMS Sample Paper — Research Paper Repository Management System</i>",
                      styles["Italic"]),
        ]
        doc.build(story)
    except ImportError:
        clean_title = title.replace("(", "").replace(")", "").replace("\\", "")
        clean_kw = keywords.replace("(", "").replace(")", "").replace("\\", "")
        clean_abs = (abstract[:400] + "...").replace("(", "").replace(")", "").replace("\\", "").replace("\n", " ")
        content = (
            f"BT /F1 14 Tf 50 770 Td ({clean_title[:80]}) Tj ET\n"
            f"BT /F1 10 Tf 50 740 Td (Keywords: {clean_kw[:80]}) Tj ET\n"
            f"BT /F1 11 Tf 50 710 Td (Abstract) Tj ET\n"
            f"BT /F1 9 Tf 50 690 Td ({clean_abs[:90]}) Tj ET\n"
            f"BT /F1 8 Tf 50 100 Td (RPRMS Sample Research Paper) Tj ET\n"
        )
        stream_bytes = content.encode("latin-1", "replace")
        pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
            b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
            b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>>>> endobj\n"
            b"4 0 obj <</Length " + str(len(stream_bytes)).encode("ascii") + b">> stream\n" +
            stream_bytes + b"\nendstream\nendobj\n"
            b"5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
            b"xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000240 00000 n \n0000000350 00000 n \n"
            b"trailer <</Size 6 /Root 1 0 R>>\nstartxref\n430\n%%EOF\n"
        )
        with open(path, "wb") as f:
            f.write(pdf)


# ── 100 sample papers ─────────────────────────────────────────────────────────
# (title, abstract, keywords, research_area, guide_name,
#  dept_keyword, pub_year, paper_type, status)
PAPERS = [
    # ARTIFICIAL INTELLIGENCE
    ("Deep Learning Approaches for Medical Image Segmentation",
     "This paper presents a deep learning framework using convolutional neural networks for automatic segmentation of medical images including MRI and CT scans. We propose a U-Net variant with attention mechanisms achieving state-of-the-art performance on benchmark datasets.",
     "deep learning, medical imaging, CNN, U-Net, segmentation",
     "Deep Learning", "Dr. Anita Sharma", "Computer", 2024, "journal", "approved"),

    ("A Survey of Transformer Models in Natural Language Processing",
     "We survey state-of-the-art transformer architectures including BERT, GPT, and T5 and analyze their performance across NLP benchmarks including sentiment analysis, question answering, and machine translation tasks.",
     "NLP, transformers, BERT, GPT, language models",
     "Natural Language Processing", "Dr. Rajesh Verma", "Computer", 2023, "journal", "approved"),

    ("Federated Learning for Privacy-Preserving Healthcare Analytics",
     "Federated learning enables distributed model training without sharing raw patient data. This paper evaluates federated approaches on healthcare datasets from multiple hospitals while maintaining HIPAA compliance.",
     "federated learning, privacy, distributed AI, healthcare",
     "Machine Learning", "Dr. Priya Gupta", "Computer", 2025, "conference", "approved"),

    ("Reinforcement Learning for Autonomous Vehicle Path Planning",
     "This paper applies deep Q-networks and policy gradient methods for path planning in autonomous vehicles in dynamic traffic environments with pedestrians and obstacles.",
     "reinforcement learning, autonomous vehicles, path planning, DQN",
     "Artificial Intelligence", "Dr. Arun Singh", "Computer", 2024, "conference", "approved"),

    ("Sentiment Analysis of Social Media Posts Using BERT Fine-Tuning",
     "We fine-tune BERT for multi-class sentiment classification on Twitter and Reddit datasets, achieving state-of-the-art results on the SemEval benchmark with 94.2% accuracy.",
     "sentiment analysis, BERT, social media, NLP, Twitter",
     "Natural Language Processing", "Dr. Kavita Rao", "Computer", 2023, "journal", "approved"),

    ("Graph Neural Networks for Drug-Drug Interaction Prediction",
     "A graph neural network model is proposed to predict drug-drug interactions using molecular structure graphs. Our model outperforms traditional ML methods on the DrugBank and TWOSIDES datasets.",
     "graph neural networks, drug interaction, healthcare, GNN, molecular",
     "Healthcare Technology", "Dr. Priya Gupta", "Computer", 2025, "journal", "approved"),

    ("Transfer Learning for Low-Resource Language Translation",
     "We explore transfer learning strategies for improving neural machine translation in low-resource Indian language pairs using multilingual pre-trained models like mBERT and XLM-R.",
     "transfer learning, machine translation, NLP, low-resource, Indian languages",
     "Natural Language Processing", "Dr. Rajesh Verma", "Computer", 2022, "conference", "approved"),

    ("Multi-Modal Emotion Recognition Using Attention Fusion",
     "This paper combines facial expression, speech, and text modalities for robust emotion recognition using attention-based fusion networks. Evaluated on IEMOCAP and MSP-IMPROV corpora.",
     "emotion recognition, multi-modal, deep learning, attention, affective computing",
     "Deep Learning", "Dr. Anita Sharma", "Computer", 2024, "journal", "approved"),

    ("Explainable AI for Credit Risk Assessment in Banking",
     "We develop an explainable AI model using LIME and SHAP to provide transparent credit scoring decisions for banking applications, improving customer trust and regulatory compliance.",
     "explainable AI, credit risk, XAI, banking, LIME, SHAP",
     "FinTech", "Dr. Meena Joshi", "Management", 2024, "journal", "approved"),

    ("Quantum Computing Algorithms for Optimization Problems",
     "An introduction to quantum computing algorithms including Grover's search and QAOA for solving combinatorial optimization problems, with benchmarks against classical algorithms.",
     "quantum computing, Grover, optimization, QAOA, quantum algorithms",
     "Artificial Intelligence", "Dr. Vikram Yadav", "Computer", 2024, "journal", "approved"),

    # CYBER SECURITY
    ("Zero-Day Vulnerability Detection Using Machine Learning",
     "We propose an ML-based system for detecting zero-day vulnerabilities by analyzing system call patterns and binary code features using random forests and gradient boosting.",
     "zero-day, vulnerability detection, machine learning, security, CVE",
     "Cyber Security", "Dr. Suresh Kumar", "Computer", 2024, "journal", "approved"),

    ("Phishing Detection Using Deep Learning and URL Analysis",
     "A deep learning model for phishing URL detection using character-level CNN and LSTM architectures. Our system achieves 98.7% detection rate on the PhishTank dataset.",
     "phishing, URL detection, deep learning, cyber security, CNN",
     "Cyber Security", "Dr. Suresh Kumar", "Computer", 2022, "journal", "approved"),

    ("Ransomware Behavior Analysis Using Dynamic API Features",
     "This paper analyzes ransomware behavior using dynamic API call sequences and file system monitoring patterns for early detection before encryption begins.",
     "ransomware, malware analysis, dynamic analysis, security, API calls",
     "Digital Forensics", "Dr. Meera Pillai", "Computer", 2023, "journal", "approved"),

    ("Comparative Study of Cryptographic Algorithms for Cloud Security",
     "We compare AES, RSA, and ECC cryptographic algorithms for cloud data protection, analyzing throughput, latency, and security tradeoffs at different data scales.",
     "cryptography, cloud security, AES, RSA, ECC, encryption",
     "Cloud Computing", "Dr. Arun Singh", "Computer", 2021, "journal", "approved"),

    ("DDoS Attack Mitigation Using Machine Learning in SDN",
     "A machine learning model deployed in an SDN controller to detect and mitigate DDoS attacks in real-time using random forest classifiers and automated traffic rerouting.",
     "DDoS, SDN, machine learning, network security, mitigation",
     "Cyber Security", "Dr. Suresh Kumar", "Computer", 2024, "journal", "approved"),

    ("Intrusion Detection System Using Hybrid CNN-LSTM",
     "A hybrid CNN-LSTM intrusion detection model trained on the NSL-KDD and UNSW-NB15 datasets, achieving 99.1% detection accuracy across multiple attack categories.",
     "intrusion detection, CNN, LSTM, cyber security, deep learning",
     "Cyber Security", "Dr. Suresh Kumar", "Computer", 2024, "journal", "approved"),

    ("Steganography Detection Using Statistical Steganalysis",
     "A statistical steganalysis framework for detecting hidden messages in digital images using chi-square, RS analysis, and deep learning feature extraction.",
     "steganography, steganalysis, digital forensics, image analysis, security",
     "Digital Forensics", "Dr. Meera Pillai", "Computer", 2022, "journal", "approved"),

    ("Cyber Threat Intelligence Sharing Using STIX and TAXII",
     "A framework for automated threat intelligence sharing using STIX data format and TAXII protocol between organizations to enable collaborative cyber defense.",
     "cyber threat intelligence, STIX, TAXII, information sharing, security",
     "Cyber Security", "Dr. Suresh Kumar", "Computer", 2023, "journal", "approved"),

    # CLOUD COMPUTING
    ("Microservices Architecture Performance Optimization",
     "This paper analyzes microservices communication patterns and proposes optimization strategies for latency reduction in containerized environments using Docker and Kubernetes.",
     "microservices, Docker, Kubernetes, performance, cloud, REST",
     "Cloud Computing", "Dr. Arun Singh", "Computer", 2024, "journal", "approved"),

    ("Serverless Computing Cost Optimization on AWS Lambda",
     "We analyze cost patterns in serverless deployments on AWS Lambda and Azure Functions and propose dynamic resource allocation strategies for cost reduction.",
     "serverless, cloud, AWS Lambda, Azure Functions, cost optimization",
     "Cloud Computing", "Dr. Kavita Rao", "Computer", 2023, "conference", "approved"),

    ("Fault Tolerance in Distributed Cloud Systems",
     "We design a self-healing distributed system architecture using Raft consensus algorithm and automatic failover mechanisms for high availability cloud services.",
     "fault tolerance, distributed systems, cloud, Raft consensus, high availability",
     "Cloud Computing", "Dr. Rajesh Verma", "Computer", 2022, "journal", "approved"),

    ("Container Orchestration with Kubernetes for ML Workflows",
     "A Kubernetes-based orchestration framework for scaling machine learning training workloads, featuring auto-scaling, GPU sharing, and distributed training support.",
     "Kubernetes, containers, ML pipeline, orchestration, GPU, training",
     "Cloud Computing", "Dr. Priya Gupta", "Computer", 2025, "conference", "approved"),

    ("Log Analysis for Cloud Infrastructure Anomaly Detection",
     "An ML-based log analysis system for detecting anomalies and predicting failures in cloud infrastructure using isolation forest and LSTM models.",
     "log analysis, cloud, monitoring, anomaly detection, ML",
     "Cloud Computing", "Dr. Arun Singh", "Computer", 2024, "journal", "approved"),

    # BLOCKCHAIN
    ("Smart Contract Vulnerability Analysis and Automated Repair",
     "We propose a static analysis tool for detecting Solidity smart contract vulnerabilities including reentrancy, integer overflow, and timestamp dependence.",
     "smart contracts, Solidity, vulnerability, blockchain, static analysis",
     "Blockchain", "Dr. Vikram Yadav", "Computer", 2024, "journal", "approved"),

    ("Decentralized Finance Protocol Security Analysis",
     "A systematic security analysis of DeFi protocols including flash loan attacks, reentrancy bugs, and oracle manipulation vulnerabilities in popular protocols.",
     "DeFi, blockchain, smart contracts, security, FinTech, flash loans",
     "FinTech", "Dr. Meena Joshi", "Management", 2023, "journal", "approved"),

    ("Blockchain for Supply Chain Transparency Using Hyperledger",
     "We implement a permissioned blockchain using Hyperledger Fabric for tracking food supply chains from farm to consumer with real-time traceability.",
     "blockchain, supply chain, agriculture, Hyperledger, traceability",
     "Blockchain", "Dr. Vikram Yadav", "Computer", 2023, "conference", "approved"),

    ("Blockchain for Academic Credential Verification",
     "A blockchain-based system for issuing and verifying academic degrees and certificates using Ethereum smart contracts, eliminating credential fraud.",
     "blockchain, academic credentials, verification, Ethereum, certificates",
     "Blockchain", "Dr. Vikram Yadav", "Computer", 2024, "journal", "approved"),

    ("Proof of Stake vs Proof of Work Energy Efficiency Analysis",
     "A comparative analysis of PoS and PoW consensus mechanisms evaluating energy consumption, security, decentralization, and transaction throughput.",
     "blockchain, proof of stake, proof of work, consensus, energy efficiency",
     "Blockchain", "Dr. Arun Singh", "Computer", 2024, "journal", "approved"),

    # IOT
    ("Smart Home Automation Using Raspberry Pi and IoT",
     "We design a low-cost smart home system integrating temperature, motion, and light sensors with remote control via a mobile application using MQTT protocol.",
     "IoT, smart home, Raspberry Pi, sensors, automation, MQTT",
     "Internet of Things", "Dr. Meera Pillai", "Electronics", 2023, "conference", "approved"),

    ("Predictive Maintenance in Industrial IoT Using Machine Learning",
     "A machine learning pipeline for predicting equipment failures in industrial settings using vibration, temperature, and acoustic sensor data from factory floor sensors.",
     "IoT, predictive maintenance, machine learning, industry 4.0, sensors",
     "Internet of Things", "Dr. Kavita Rao", "Electronics", 2024, "journal", "approved"),

    ("Energy Harvesting Techniques for Battery-Free IoT Sensors",
     "This paper reviews solar, thermal, piezoelectric, and RF energy harvesting methods for powering battery-free wireless sensor nodes in remote deployments.",
     "energy harvesting, IoT, wireless sensors, battery-free, solar",
     "Internet of Things", "Dr. Meera Pillai", "Electronics", 2022, "journal", "approved"),

    ("LoRaWAN for Long-Range Smart Agriculture Monitoring",
     "We evaluate LoRaWAN for low-power wide-area network applications in smart agriculture, monitoring soil moisture, temperature, and crop health over 10 km range.",
     "LoRaWAN, IoT, LPWAN, smart agriculture, wireless, soil monitoring",
     "Internet of Things", "Dr. Arun Singh", "Electronics", 2023, "conference", "approved"),

    ("Edge Computing Framework for Real-Time IoT Processing",
     "A framework for processing IoT sensor data at the edge using Apache Kafka and TensorFlow Lite to reduce latency and bandwidth in smart city applications.",
     "edge computing, IoT, real-time, smart city, Apache Kafka",
     "Internet of Things", "Dr. Vikram Yadav", "Computer", 2024, "journal", "approved"),

    ("IoT-Based Air Quality Monitoring in Urban Environments",
     "A low-cost IoT sensor network for continuous monitoring of PM2.5, PM10, CO2, and VOC levels in urban areas with real-time alerting and visualization.",
     "IoT, air quality, pollution monitoring, sensors, urban, PM2.5",
     "Internet of Things", "Dr. Meera Pillai", "Electronics", 2023, "journal", "approved"),

    # SOFTWARE ENGINEERING
    ("Agile vs Waterfall in Large-Scale Enterprise Projects",
     "We analyze 50 industry software projects comparing Agile and Waterfall methodologies in delivery time, software quality, stakeholder satisfaction, and project cost.",
     "software engineering, Agile, Waterfall, project management, enterprise",
     "Software Engineering", "Dr. Anita Sharma", "Computer", 2022, "journal", "approved"),

    ("API Security Best Practices for RESTful Web Services",
     "A comprehensive review of REST API security covering OAuth 2.0, JWT authentication, rate limiting, input validation, and OWASP API Top 10 vulnerabilities.",
     "REST API, security, OAuth, JWT, web services, OWASP",
     "Web Development", "Dr. Suresh Kumar", "Computer", 2023, "journal", "approved"),

    ("Test-Driven Development Impact on Software Quality",
     "An empirical study measuring TDD adoption impact on defect density, code coverage, and developer productivity across 30 software development teams.",
     "TDD, software testing, code quality, agile, development methodology",
     "Software Testing", "Dr. Meera Pillai", "Computer", 2022, "journal", "approved"),

    ("Automated Test Case Generation Using Genetic Algorithms",
     "A genetic algorithm approach for automatically generating test cases from UML activity diagrams and CFGs to maximize branch coverage and mutation score.",
     "test case generation, genetic algorithm, software testing, UML, coverage",
     "Software Testing", "Dr. Anita Sharma", "Computer", 2023, "journal", "approved"),

    ("Microfront-End Architecture for Scalable Web Applications",
     "This paper presents microfrontend architecture patterns using React and Module Federation for building independently deployable web application modules.",
     "microfrontend, React, web development, architecture, Module Federation",
     "Web Development", "Dr. Kavita Rao", "Computer", 2024, "conference", "approved"),

    ("Human-Computer Interaction Design Guidelines for Elderly Users",
     "Usability studies of digital interfaces for elderly users aged 60+ and evidence-based design guidelines for inclusive technology in healthcare apps.",
     "HCI, usability, elderly, accessibility, inclusive design, healthcare",
     "Software Engineering", "Dr. Meena Joshi", "Computer", 2022, "journal", "approved"),

    # DATABASE / BIG DATA
    ("Query Optimization Techniques for Large-Scale MongoDB",
     "We propose query optimization strategies for MongoDB including index selection, aggregation pipeline tuning, sharding, and query plan analysis.",
     "NoSQL, MongoDB, query optimization, database, scalability, indexing",
     "Database Management", "Dr. Priya Gupta", "Computer", 2023, "journal", "approved"),

    ("Real-Time Stream Processing with Apache Kafka and Flink",
     "A framework for processing high-velocity financial transaction streams using Apache Kafka for ingestion and Apache Flink for real-time aggregation and fraud detection.",
     "Apache Kafka, Apache Flink, stream processing, real-time, big data, fintech",
     "Big Data", "Dr. Rajesh Verma", "Computer", 2023, "conference", "approved"),

    ("Data Lake Architecture for Healthcare Analytics with Delta Lake",
     "We design a scalable data lake using Apache Spark and Delta Lake for managing electronic health records, enabling ACID transactions and time-travel queries.",
     "data lake, healthcare, Apache Spark, Delta Lake, analytics, EHR",
     "Big Data", "Dr. Priya Gupta", "Computer", 2024, "journal", "approved"),

    ("Natural Language Interfaces for Database Querying",
     "A natural language to SQL system using seq2seq transformer models allowing non-technical users to query relational databases in plain English.",
     "natural language interface, NLP, SQL, text-to-SQL, database, accessibility",
     "Database Management", "Dr. Priya Gupta", "Computer", 2023, "journal", "approved"),

    ("Hadoop vs Spark Performance for Large-Scale ETL Pipelines",
     "We benchmark Hadoop MapReduce and Apache Spark for ETL workloads on datasets ranging from 100 GB to 10 TB, analyzing throughput, latency, and cost.",
     "Hadoop, Spark, ETL, big data, performance, benchmarking",
     "Big Data", "Dr. Rajesh Verma", "Computer", 2022, "journal", "approved"),

    # COMPUTER VISION
    ("Object Detection Using YOLOv8 for Traffic Surveillance",
     "We implement YOLOv8 for real-time vehicle and pedestrian detection in traffic surveillance video streams, achieving 47 FPS on embedded NVIDIA Jetson hardware.",
     "YOLO, object detection, traffic, computer vision, deep learning, real-time",
     "Computer Vision", "Dr. Anita Sharma", "Computer", 2024, "journal", "approved"),

    ("Medical X-Ray Classification Using Transfer Learning",
     "VGG16 and ResNet50 are fine-tuned for classifying chest X-rays as normal, pneumonia, or COVID-19 using a dataset of 112,000 labeled X-ray images.",
     "X-ray, classification, transfer learning, healthcare, ResNet, VGG16",
     "Healthcare Technology", "Dr. Priya Gupta", "Computer", 2024, "journal", "approved"),

    ("Plant Disease Detection Using Smartphone Camera and MobileNet",
     "A lightweight deep learning application using MobileNetV3 for detecting plant leaf diseases from smartphone photos with 96.4% accuracy on PlantVillage dataset.",
     "plant disease, mobile, deep learning, MobileNet, agriculture, leaf",
     "Computer Vision", "Dr. Kavita Rao", "Computer", 2023, "conference", "approved"),

    ("Face Recognition System Under Varying Lighting Conditions",
     "A robust face recognition system using ArcFace loss and image preprocessing techniques to handle poor lighting, occlusions, and different camera angles.",
     "face recognition, ArcFace, computer vision, deep learning, biometrics",
     "Computer Vision", "Dr. Rajesh Verma", "Computer", 2023, "conference", "approved"),

    ("OCR for Handwritten Mathematical Formula Recognition",
     "An optical character recognition system for handwritten mathematical formulas using CNN-LSTM encoder-decoder architecture with attention mechanisms.",
     "OCR, handwriting, mathematics, CNN, LSTM, attention, formula",
     "Computer Vision", "Dr. Anita Sharma", "Computer", 2022, "journal", "approved"),

    # MOBILE / APP DEV
    ("Flutter vs React Native Performance Comparison",
     "A comprehensive comparison of Flutter and React Native for cross-platform mobile app development, measuring startup time, animation smoothness, memory usage, and app size.",
     "Flutter, React Native, mobile development, cross-platform, performance",
     "Mobile Application Development", "Dr. Rajesh Verma", "Computer", 2024, "journal", "approved"),

    ("Mobile Health App for Diabetes Chronic Disease Management",
     "Design and evaluation of a mobile application for diabetes management including blood glucose logging, medication reminders, diet tracking, and doctor communication.",
     "mobile health, mHealth, diabetes, chronic disease, healthcare app",
     "Healthcare Technology", "Dr. Meera Pillai", "Computer", 2023, "conference", "approved"),

    ("Offline-First Mobile Architecture Using SQLite Synchronization",
     "An offline-first mobile app architecture using SQLite local storage with background cloud synchronization for users with intermittent internet connectivity.",
     "offline-first, SQLite, mobile, sync, architecture, connectivity",
     "Mobile Application Development", "Dr. Kavita Rao", "Computer", 2022, "journal", "approved"),

    ("Augmented Reality Try-On Application for E-Commerce",
     "We design and evaluate an AR mobile application for virtual clothing and furniture try-on using ARKit and ARCore for iOS and Android platforms.",
     "augmented reality, AR, retail, mobile, shopping, ARKit, ARCore",
     "Mobile Application Development", "Dr. Rajesh Verma", "Computer", 2024, "conference", "approved"),

    # HEALTHCARE TECHNOLOGY
    ("Electronic Health Record Interoperability Using HL7 FHIR",
     "We analyze HL7 FHIR R4 implementation for EHR interoperability and identify technical and organizational barriers to seamless health data exchange.",
     "EHR, HL7, FHIR, interoperability, healthcare, electronic records",
     "Healthcare Technology", "Dr. Priya Gupta", "Computer", 2023, "journal", "approved"),

    ("AI-Assisted Diagnosis of Diabetic Retinopathy from Fundus Images",
     "A deep learning model using EfficientNet for automated screening of diabetic retinopathy from fundus photographs, graded against retinal specialist annotations.",
     "diabetic retinopathy, deep learning, fundus, AI diagnosis, ophthalmology",
     "Healthcare Technology", "Dr. Anita Sharma", "Computer", 2025, "journal", "approved"),

    ("Wearable IoT System for Continuous Patient Vital Monitoring",
     "A wearable IoT system for continuous monitoring of heart rate, SpO2, ECG, and body temperature with real-time cloud alerting for ICU patients.",
     "wearable, IoT, patient monitoring, healthcare, ECG, SpO2, vitals",
     "Healthcare Technology", "Dr. Meera Pillai", "Electronics", 2024, "journal", "approved"),

    ("Data Augmentation for Small Medical Imaging Datasets Using GANs",
     "We compare GAN-based, traditional, and mixup augmentation techniques for improving deep learning performance on small medical imaging datasets with limited labels.",
     "data augmentation, GAN, medical imaging, deep learning, small dataset",
     "Healthcare Technology", "Dr. Priya Gupta", "Computer", 2023, "journal", "approved"),

    # E-LEARNING
    ("Adaptive Learning Systems Using Multi-Armed Bandit Algorithms",
     "We build an adaptive learning platform that personalizes content difficulty and sequence using Thompson Sampling and UCB1 multi-armed bandit algorithms.",
     "adaptive learning, reinforcement learning, bandit algorithms, e-learning, personalization",
     "E-Learning", "Dr. Kavita Rao", "Computer", 2024, "journal", "approved"),

    ("Automated Essay Scoring Using BERT for Educational Assessment",
     "A BERT-based automated essay grading system fine-tuned on the ASAP dataset, achieving a quadratic weighted kappa of 0.88 across 8 essay prompts.",
     "automated grading, NLP, BERT, e-learning, essay scoring, education",
     "E-Learning", "Dr. Rajesh Verma", "Computer", 2023, "journal", "approved"),

    ("Gamification Impact on Student Engagement in Online Courses",
     "We conduct a 6-month controlled study measuring the impact of badges, leaderboards, and points on student engagement and completion rates in MOOCs.",
     "gamification, e-learning, MOOC, student engagement, completion rate",
     "E-Learning", "Dr. Meena Joshi", "Management", 2022, "journal", "approved"),

    ("Virtual Reality Laboratories for Chemistry Education",
     "A VR-based chemistry laboratory simulation allowing students to conduct experiments involving hazardous chemicals safely using Meta Quest headsets.",
     "VR, virtual reality, e-learning, chemistry education, simulation, Meta Quest",
     "E-Learning", "Dr. Arun Singh", "Computer", 2024, "conference", "approved"),

    # DATA SCIENCE / ANALYTICS
    ("LSTM and Transformer Models for Stock Price Forecasting",
     "We apply LSTM, Temporal Fusion Transformer, and N-BEATS models for stock price forecasting using OHLCV data and sentiment features from financial news.",
     "time series, stock prediction, LSTM, Transformer, FinTech, forecasting",
     "Data Analytics", "Dr. Meena Joshi", "Management", 2024, "journal", "approved"),

    ("Customer Churn Prediction Using XGBoost and SHAP Explanations",
     "An ensemble of XGBoost and LightGBM for telecom customer churn prediction with SHAP-based feature importance explanations for business stakeholders.",
     "customer churn, XGBoost, LightGBM, SHAP, machine learning, telecom",
     "Data Analytics", "Dr. Anita Sharma", "Management", 2023, "journal", "approved"),

    ("Dashboard Design Best Practices for Business Intelligence",
     "Evidence-based guidelines for designing effective BI dashboards using Tableau and Power BI, evaluated through eye-tracking studies with 120 business analysts.",
     "business intelligence, dashboard, data visualization, Tableau, Power BI",
     "Data Analytics", "Dr. Kavita Rao", "Management", 2023, "journal", "approved"),

    ("Social Network Analysis for Marketing Influence Maximization",
     "Graph-based algorithms for identifying key influencers in social networks using betweenness centrality and community detection for targeted marketing.",
     "social network analysis, graph, influence maximization, marketing, community detection",
     "Data Analytics", "Dr. Kavita Rao", "Computer", 2023, "conference", "approved"),

    ("Feature Engineering Strategies for Credit Card Fraud Detection",
     "Advanced feature engineering including behavioral aggregations, velocity features, and embedding representations for real-time credit card fraud detection.",
     "fraud detection, feature engineering, machine learning, FinTech, credit card",
     "FinTech", "Dr. Meena Joshi", "Management", 2024, "conference", "approved"),

    # COMPUTER NETWORKS
    ("Software-Defined Networking for Dynamic Load Balancing",
     "An SDN-based traffic management system using OpenFlow 1.5 for dynamic load balancing across enterprise network paths, reducing congestion by 43%.",
     "SDN, OpenFlow, network management, load balancing, traffic engineering",
     "Computer Networks", "Dr. Suresh Kumar", "Computer", 2023, "journal", "approved"),

    ("5G Network Slicing Architecture for Heterogeneous Services",
     "We propose a network slicing framework for 5G that dynamically allocates resources to guarantee different QoS levels for eMBB, URLLC, and mMTC services.",
     "5G, network slicing, QoS, wireless networks, eMBB, URLLC",
     "Computer Networks", "Dr. Meera Pillai", "Electronics", 2024, "journal", "approved"),

    ("Wireless Sensor Network Clustering Protocols Comparison",
     "We compare LEACH, PEGASIS, TEEN, and SEP energy-efficient clustering protocols for wireless sensor networks in different deployment scenarios.",
     "wireless sensor network, LEACH, energy efficiency, clustering, WSN",
     "Computer Networks", "Dr. Vikram Yadav", "Electronics", 2022, "conference", "approved"),

    # GREEN COMPUTING
    ("Energy-Efficient Task Scheduling in Green Data Centers",
     "A genetic algorithm approach for scheduling computational tasks to minimize energy consumption and carbon footprint while meeting SLA requirements.",
     "green computing, energy efficiency, data center, task scheduling, carbon",
     "Green Computing", "Dr. Meera Pillai", "Computer", 2023, "journal", "approved"),

    ("Carbon Footprint Estimation for Cloud Computing Workloads",
     "A model for estimating and optimizing the carbon footprint of cloud computing workloads by intelligent placement on renewable energy-powered servers.",
     "green computing, carbon footprint, cloud, sustainability, renewable energy",
     "Green Computing", "Dr. Kavita Rao", "Computer", 2024, "journal", "approved"),

    # ROBOTICS
    ("Vision-Based Robotic Arm Control Using YOLOv8 and RL",
     "A vision-based robotic arm control system combining YOLOv8 object detection with PPO reinforcement learning for grasping novel objects in unstructured environments.",
     "robotics, deep learning, YOLO, robotic arm, reinforcement learning, grasping",
     "Robotics", "Dr. Arun Singh", "Electronics", 2024, "journal", "approved"),

    ("Real-Time Path Planning for Mobile Robots in Dynamic Environments",
     "A D* Lite algorithm with dynamic obstacle prediction using LSTM for real-time path re-planning in autonomous mobile robots navigating crowded spaces.",
     "robotics, path planning, autonomous mobile robot, D* algorithm, LSTM",
     "Robotics", "Dr. Meera Pillai", "Electronics", 2023, "conference", "approved"),

    # DIGITAL FORENSICS
    ("Memory Forensics for Fileless Malware Detection",
     "We apply Volatility memory forensics framework to detect fileless malware in Windows memory dumps by analyzing process injection and code hooks.",
     "digital forensics, memory forensics, malware, Windows, Volatility, fileless",
     "Digital Forensics", "Dr. Suresh Kumar", "Computer", 2023, "journal", "approved"),

    # Additional diverse papers
    ("Ethical AI Framework for Bias Detection in Hiring Systems",
     "We study algorithmic bias in AI-powered hiring systems and propose fairness metrics including demographic parity, equalized odds, and calibration.",
     "ethical AI, bias, fairness, hiring, machine learning, algorithmic fairness",
     "Artificial Intelligence", "Dr. Anita Sharma", "Computer", 2024, "journal", "approved"),

    ("Deep Reinforcement Learning for Atari Game Playing",
     "Implementation and comparison of DQN, Double DQN, A3C, and PPO algorithms for training game-playing agents across 57 Atari 2600 environments.",
     "deep reinforcement learning, DQN, A3C, PPO, game AI, Atari",
     "Artificial Intelligence", "Dr. Arun Singh", "Computer", 2023, "journal", "approved"),

    ("Mutation Testing Effectiveness in Python Applications",
     "We evaluate mutation testing tools including mutmut and cosmic-ray for Python applications and analyze their effectiveness in revealing real production bugs.",
     "mutation testing, Python, software quality, testing tools, code coverage",
     "Software Testing", "Dr. Rajesh Verma", "Computer", 2022, "conference", "approved"),

    ("CNN-Based Offline Signature Verification System",
     "A siamese CNN network for offline signature verification trained on the CEDAR, SigNet, and ICDAR datasets, robust to skilled and random forgeries.",
     "CNN, signature verification, deep learning, biometrics, siamese network",
     "Computer Vision", "Dr. Anita Sharma", "Computer", 2022, "journal", "approved"),

    ("MLflow for End-to-End Machine Learning Pipeline Management",
     "We demonstrate end-to-end ML pipeline management using MLflow including experiment tracking, model registry, serving, and A/B testing deployment.",
     "MLflow, ML pipeline, automation, model management, MLOps, deployment",
     "Machine Learning", "Dr. Priya Gupta", "Computer", 2025, "conference", "approved"),

    ("Telemedicine Platform Design with End-to-End Encryption",
     "We design a HIPAA-compliant telemedicine video platform with WebRTC-based end-to-end encryption and evaluate security against OWASP threat models.",
     "telemedicine, HIPAA, security, healthcare, WebRTC, encryption",
     "Healthcare Technology", "Dr. Suresh Kumar", "Computer", 2022, "conference", "approved"),

    ("Blockchain-Based Identity Management for IoT Ecosystems",
     "A decentralized identity management system using Ethereum smart contracts and DID standards for authenticating and authorizing IoT devices at scale.",
     "blockchain, IoT, identity management, DID, smart contracts, decentralized",
     "IoT Security", "Dr. Vikram Yadav", "Computer", 2023, "conference", "approved"),

    ("Anomaly Detection in Network Traffic Using Variational Autoencoders",
     "We apply variational autoencoders for unsupervised anomaly detection in network traffic, achieving 97.8% detection rate on the CICIDS-2017 dataset.",
     "anomaly detection, variational autoencoder, VAE, network security, unsupervised",
     "Cyber Security", "Dr. Suresh Kumar", "Computer", 2023, "journal", "approved"),

    ("NLP-Based Automatic Resume Screening for Recruitment",
     "A BERT-based resume screening system that matches candidate qualifications to job requirements, reducing screening time by 78% in a pilot study.",
     "NLP, resume screening, BERT, HR, recruitment, text matching",
     "Natural Language Processing", "Dr. Kavita Rao", "Computer", 2024, "conference", "approved"),

    ("Microcontroller-Based ECG Signal Acquisition and Analysis",
     "An Arduino-based portable ECG acquisition system with real-time arrhythmia detection using a lightweight CNN deployed on the microcontroller.",
     "ECG, microcontroller, Arduino, arrhythmia, healthcare, embedded AI",
     "Healthcare Technology", "Dr. Meera Pillai", "Electronics", 2023, "journal", "approved"),

    ("Privacy-Preserving Data Mining Using Differential Privacy",
     "We apply differential privacy mechanisms (Laplace, Gaussian, exponential) to enable privacy-preserving data mining on sensitive government datasets.",
     "differential privacy, data mining, privacy, Laplace mechanism, Gaussian",
     "Data Science", "Dr. Priya Gupta", "Computer", 2023, "journal", "approved"),

    ("Web Scraping and Data Pipeline for Real Estate Analytics",
     "An automated web scraping pipeline using Scrapy and BeautifulSoup for collecting real estate listing data with PostgreSQL storage and Tableau dashboards.",
     "web scraping, Scrapy, data pipeline, real estate, analytics, ETL",
     "Data Analytics", "Dr. Anita Sharma", "Computer", 2022, "conference", "approved"),

    ("Green IoT: Energy-Efficient Protocols for Smart Cities",
     "A survey of energy-efficient communication protocols (Zigbee, Z-Wave, NB-IoT) for smart city IoT deployments with lifecycle carbon analysis.",
     "green IoT, smart city, energy efficiency, Zigbee, NB-IoT, sustainability",
     "Green Computing", "Dr. Vikram Yadav", "Electronics", 2024, "journal", "approved"),

    # Pending / non-approved papers for realism
    ("Generative AI for Automated Code Review and Bug Fixing",
     "We evaluate GPT-4, CodeLlama, and DeepSeek-Coder for automated code review, bug detection, and fix generation across Python, Java, and C++ codebases.",
     "generative AI, code review, LLM, software development, bug fixing",
     "Software Engineering", "Dr. Rajesh Verma", "Computer", 2025, "conference", "pending"),

    ("Multimodal Retrieval-Augmented Generation for Knowledge Bases",
     "A RAG system integrating text, image, and structured data for enterprise knowledge base question answering using LangChain and Pinecone vector database.",
     "RAG, multimodal, LLM, knowledge base, LangChain, vector database",
     "Natural Language Processing", "Dr. Kavita Rao", "Computer", 2025, "conference", "pending"),

    ("Neural Architecture Search for On-Device AI",
     "Automated neural architecture search using DARTS and ProxylessNAS for designing efficient models deployable on edge devices with <1W power budget.",
     "neural architecture search, NAS, edge AI, DARTS, efficient models",
     "Deep Learning", "Dr. Anita Sharma", "Computer", 2025, "journal", "pending"),

    ("Post-Quantum Cryptography NIST Standards Implementation",
     "Implementation and benchmarking of NIST post-quantum cryptography finalists CRYSTALS-Kyber and CRYSTALS-Dilithium on resource-constrained IoT devices.",
     "post-quantum cryptography, NIST, lattice cryptography, IoT, security",
     "Cyber Security", "Dr. Meera Pillai", "Computer", 2025, "journal", "pending"),

    ("Large Language Models for Automated Scientific Literature Review",
     "We develop a pipeline using GPT-4 and Claude for automated systematic literature review, citation graph analysis, and research gap identification.",
     "LLM, literature review, NLP, scientific text, automation, research",
     "Natural Language Processing", "Dr. Rajesh Verma", "Computer", 2025, "journal", "changes_requested"),
]


def run():
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)

    print("=" * 60)
    print("RPRMS Sample Data Seeder — 100 Research Papers")
    print("=" * 60)

    # ── Read departments ──────────────────────────────────────────────────────
    print("\n📂 Reading departments...")
    cur.execute("SELECT dept_id, dept_name FROM departments")
    all_depts = cur.fetchall()

    if not all_depts:
        print("❌  No departments found. Run:  python database/seed.py  first.")
        return

    for d in all_depts:
        print(f"   dept_id={d['dept_id']}  {d['dept_name']}")

    def find_dept(keyword: str) -> int:
        kw = keyword.lower()
        for d in all_depts:
            if kw in d["dept_name"].lower():
                return d["dept_id"]
        return all_depts[0]["dept_id"]  # fallback

    # ── Read / create faculty users ───────────────────────────────────────────
    print("\n👤 Checking faculty users...")
    cur.execute("SELECT user_id, full_name FROM users WHERE role='faculty' AND is_active=1")
    existing_faculty = {r["full_name"]: r["user_id"] for r in cur.fetchall()}

    needed = {p[4] for p in PAPERS}
    for guide in sorted(needed):
        if guide in existing_faculty:
            continue
        email = (guide.lower().replace("dr. ", "")
                              .replace(" ", ".") + "@rprms.edu")
        cur.execute("SELECT user_id FROM users WHERE email=%s", (email,))
        row = cur.fetchone()
        if row:
            existing_faculty[guide] = row["user_id"]; continue

        pw = bcrypt.hashpw(b"Faculty@123", bcrypt.gensalt()).decode()
        dept_id = all_depts[0]["dept_id"]
        cur.execute("""
            INSERT INTO users (full_name, email, password_hash, role, dept_id, is_active)
            VALUES (%s,%s,%s,'faculty',%s,1)
        """, (guide, email, pw, dept_id))
        conn.commit()
        existing_faculty[guide] = cur.lastrowid
        print(f"   ✅ Created: {guide}  ({email}  / Faculty@123)")

    # ── Get admin id for status history ──────────────────────────────────────
    cur.execute("SELECT user_id FROM users WHERE role='admin' LIMIT 1")
    row = cur.fetchone()
    admin_id = row["user_id"] if row else list(existing_faculty.values())[0]

    # ── Insert papers ─────────────────────────────────────────────────────────
    print(f"\n📄 Inserting {len(PAPERS)} sample papers...\n")
    inserted = skipped = failed = 0

    for idx, p in enumerate(PAPERS):
        (title, abstract, keywords, research_area,
         guide, dept_kw, pub_year, ptype, status) = p

        # Skip if title already exists
        cur.execute("SELECT paper_id FROM papers WHERE LOWER(title)=LOWER(%s)",
                    (title.strip(),))
        if cur.fetchone():
            skipped += 1
            continue

        dept_id     = find_dept(dept_kw)
        uploader_id = existing_faculty.get(guide, admin_id)

        # Create PDF
        tmp_code = f"RPRMS-SEED-{9000+idx:04d}"
        tmp_file = os.path.join(UPLOAD_DIR, f"{tmp_code}.pdf")
        try:
            make_pdf(title, abstract, keywords, tmp_file)
            fsize = os.path.getsize(tmp_file)
        except Exception as e:
            print(f"   ⚠ PDF failed for '{title[:40]}': {e}")
            failed += 1; continue

        try:
            cur.execute("""
                INSERT INTO papers
                    (paper_code, title, abstract, keywords, research_area,
                     guide_name, dept_id, pub_year, paper_type, uploaded_by,
                     file_name, file_path, file_size, status)
                VALUES ('TEMP',%s,%s,%s,%s,%s,%s,%s,%s,%s,'TEMP','TEMP',0,%s)
            """, (title.strip(), abstract.strip(), keywords.strip(),
                  research_area.strip(), guide.strip(), dept_id,
                  pub_year, ptype, uploader_id, status))
            conn.commit()
            paper_id = cur.lastrowid

            # Real paper code
            paper_code = f"RPRMS-{pub_year}-{paper_id:04d}"
            real_file  = f"{paper_code.replace('-','_')}.pdf"
            real_path  = os.path.join(UPLOAD_DIR, real_file)
            if os.path.exists(tmp_file):
                os.rename(tmp_file, real_path)

            cur.execute("""
                UPDATE papers SET paper_code=%s, file_name=%s, file_path=%s
                WHERE paper_id=%s
            """, (paper_code, real_file, real_path, paper_id))
            conn.commit()

            # Status history
            cur.execute("""
                INSERT INTO paper_status_history
                    (paper_id, old_status, new_status, changed_by, comments)
                VALUES (%s,NULL,'pending',%s,'Initial upload')
            """, (paper_id, uploader_id))

            if status == "approved":
                cur.execute("""
                    INSERT INTO paper_status_history
                        (paper_id, old_status, new_status, changed_by, comments)
                    VALUES (%s,'pending','approved',%s,'Approved — sample dataset')
                """, (paper_id, admin_id))
            elif status == "changes_requested":
                cur.execute("""
                    INSERT INTO paper_status_history
                        (paper_id, old_status, new_status, changed_by, comments)
                    VALUES (%s,'pending','changes_requested',%s,'Please revise methodology section')
                """, (paper_id, admin_id))
            conn.commit()

            # QR code for approved papers
            if status == "approved":
                try:
                    from services.qr_service import get_or_create_qr
                    get_or_create_qr(paper_id, paper_code)
                except Exception:
                    pass

            inserted += 1
            print(f"   ✅ [{inserted:3d}] {paper_code}  {title[:55]}")

        except Exception as e:
            conn.rollback()
            if os.path.exists(tmp_file): os.remove(tmp_file)
            print(f"   ❌ FAILED: {title[:40]} — {e}")
            failed += 1

    cur.close(); conn.close()

    print("\n" + "=" * 60)
    print(f"✅  Inserted  : {inserted} papers")
    print(f"⏭️  Skipped   : {skipped}  (already in DB)")
    print(f"❌  Failed    : {failed}")
    print("=" * 60)
    print("\n🎓 Student Panel is ready!")
    print("   Login: student@rprms.edu / Student@123")
    print("   Try searching: 'AI', 'Machine Learning', 'Blockchain', 'IoT'")
    print("   Run:  streamlit run app.py")
    print("=" * 60)


if __name__ == "__main__":
    run()
