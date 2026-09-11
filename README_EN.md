<p align="center">

[中文](README.md) | **English**

</p>

# Welding Defect Automatic Detection and Assessment System Based on YOLOv8 and API 579 FFS

---

## 📖 Introduction

This project is an automated auxiliary system for **welding defect detection and engineering assessment**.

The system uses **YOLOv8** as the core machine vision model. Through a graphical user interface (GUI), users can select the defect type, specify the directory containing the inspection images, and enter relevant engineering parameters such as container wall thickness and original image dimensions.

The system processes grayscale images obtained from **X-ray inspection equipment**, automatically detects welding defects using YOLOv8, and then applies a **sliding-window algorithm** to further analyze the detected defect regions.

For applicable defect assessment, the system combines the detected geometric characteristics with relevant **API 579 Fitness-For-Service (FFS)** assessment methods to provide an engineering-oriented evaluation result.

Finally, the system generates annotated inspection images and can automatically generate a Word-format inspection report.

---

## ✨ Key Features

### 1. YOLOv8-based Defect Detection

The system uses trained YOLOv8 models to automatically detect welding defects from X-ray inspection images.

The detection process provides information such as:

- Defect location
- Bounding box coordinates
- Detection confidence

---

### 2. Sliding-Window Analysis

After a defect is detected by YOLOv8, the corresponding defect region can be further processed using a sliding-window algorithm.

The defect region is divided into multiple sub-regions, allowing the system to calculate relevant geometric characteristics for individual windows.

The parameters involved include:

- Defect length
- Defect width
- Defect area

---

### 3. API 579 FFS Assessment

The system integrates relevant **API 579 Fitness-For-Service** assessment procedures into the defect evaluation workflow.

The assessment uses information such as:

- Defect geometry
- Material parameters
- Engineering parameters
- Relevant assessment curves and data tables

For crack assessment, additional parameters are required, including:

- Steel material type
- API 579 assessment curve type
- Minimum Yield Strength (MYS)
- Other relevant engineering parameters

---

### 4. Graphical User Interface

The system uses **Tkinter** to provide a graphical interface.

Users can perform the following operations through the GUI:

- Select defect type
- Select the inspection image directory
- Enter image dimensions
- Enter wall thickness
- Enter material-related parameters
- Enter API 579 assessment parameters
- Start the detection process

No direct modification of the source code is required for normal operation.

---

### 5. Detection Result Visualization

The system uses OpenCV to annotate the original inspection images.

The output images can contain:

- Defect bounding boxes
- Defect dimensions
- Assessment results

The current visualization uses:

- 🟩 **Green:** Passed assessment
- 🟥 **Red:** Failed assessment

---

### 6. Automatic Word Report Generation

After image processing and assessment, the system can automatically generate a **Word-format inspection report**.

The report-generation functionality is implemented in:

```text
CrFrameAndReport.py
```

---

# 🏗️ System Architecture

The system currently uses both **procedural programming** and **object-oriented programming** approaches.

The overall workflow can be summarized as follows:

```text
                    X-ray Inspection Image
                              │
                              ▼
                  ┌──────────────────────┐
                  │   Defect Type        │
                  │      Selection       │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │       YOLOv8         │
                  │ Defect Detection     │
                  │ & Localization       │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Sliding Window     │
                  │   Region Analysis    │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Geometric Parameters │
                  │ Length / Width / Area│
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │     API 579 FFS      │
                  │      Assessment      │
                  └──────────┬───────────┘
                             │
                      ┌──────┴──────┐
                      ▼             ▼
                   Passed         Failed
                      │             │
                      └──────┬──────┘
                             ▼
                  ┌──────────────────────┐
                  │ Result Visualization │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Word Inspection     │
                  │       Report         │
                  └──────────────────────┘
```

---

# 🧩 Software Structure

## Procedural Modules

### `main_selector.py`

The main selection interface of the system.

Responsibilities include:

- Creating the defect-type selection GUI
- Starting the corresponding processing module according to the user's selection

---

### `input_dialog.py`

The parameter input dialog.

It is used to collect information such as:

- Inspection image directory
- Original image length
- Original image width
- Container wall thickness
- Other parameters required by the assessment process

---

### `label_LP.py`

Processing module for **Lack of Penetration (LP)**.

It handles the corresponding YOLO model and subsequent defect processing and assessment.

---

### `label_PO.py`

Processing module for **Porosity / Bubble (PO)**.

It handles the corresponding YOLO model and subsequent defect processing and assessment.

---

### `label_CR.py`

Processing module for **Crack (CR)**.

It is responsible for:

- YOLOv8 defect detection
- Calling the API 579 assessment functionality
- Result processing
- Output generation

---

# 🧱 Object-Oriented Modules

The crack assessment functionality is implemented using an object-oriented design.

## `CrApiAssisment.py`

The core API 579 assessment module.

Its main responsibilities include:

- Reading API 579-related data
- CSV and JSON data processing
- Receiving parameters from the main program
- Sliding-window assessment
- Defect assessment
- GUI-related parameter input

The general workflow is:

```text
YOLO Detection Results
          │
          ▼
 Defect Parameters
          │
          ▼
Engineering Parameters
          │
          ▼
 Sliding-Window Analysis
          │
          ▼
 API 579 Assessment
          │
          ▼
 Assessment Result
```

---

## `CrFrameAndReport.py`

The post-processing and report-generation module.

Its functions include:

- Individual defect annotation
- Result visualization
- Defect dimension annotation
- Word report generation

---

# 🧠 Core Algorithms

## 1. YOLOv8 Object Detection

The system loads trained YOLOv8 weights and performs inference on X-ray welding inspection images.

The detection process produces information including:

```text
Input Image
     │
     ▼
   YOLOv8
     │
     ▼
Defect Bounding Box
     │
     ├── Location
     └── Confidence
```

---

## 2. Sliding-Window Algorithm

The detected defect region can be further divided into multiple sub-windows.

Conceptually:

```text
┌──────────────────────────────┐
│                              │
│    ┌───────┐                 │
│    │   W1  │                 │
│    └───────┘                 │
│          ┌───────┐           │
│          │   W2  │           │
│          └───────┘           │
│                ┌───────┐     │
│                │   W3  │     │
│                └───────┘     │
│                              │
└──────────────────────────────┘
```

Each sub-window can be analyzed independently to obtain relevant geometric characteristics.

---

# 📐 API 579 Assessment Workflow

The API 579-related assessment is integrated after visual defect detection.

The workflow is:

```text
YOLOv8 Detection
       │
       ▼
Defect Region Extraction
       │
       ▼
Sliding-Window Processing
       │
       ▼
Geometric Feature Calculation
       │
       ├── Length
       ├── Width
       └── Area
       │
       ▼
Material / Engineering Parameters
       │
       ▼
API 579 Assessment
       │
       ▼
Pass / Fail
```

For crack assessment, the system also uses relevant material information and assessment curve/data-table information.

The user may need to provide:

- Material type
- Assessment curve type
- Minimum Yield Strength (MYS)
- Other relevant parameters

---

# 💻 Development Environment

## Operating System

- Windows 10
- Windows 11

## Python

```text
Python 3.8+
```

## Main Dependencies

The project uses the following main libraries and technologies:

- Ultralytics YOLO
- OpenCV
- Tkinter
- NumPy
- python-docx
- CSV
- JSON

For the complete dependency list, see:

```text
requirements.txt
```

---

# 📁 Project Structure

```text
Welding-Defect-Detection-System-Based-on-YOLO-v8-and-API-579/
│
├── config_and_data/
│   └── API 579 and related configuration/data files
│
├── models/
│   └── YOLOv8 model weights
│
├── CrApiAssisment.py
│   └── API 579 assessment class
│
├── CrFrameAndReport.py
│   └── Result post-processing and Word report generation
│
├── label_CR.py
│   └── Crack processing module
│
├── label_LP.py
│   └── Lack of Penetration processing module
│
├── label_PO.py
│   └── Porosity/Bubble processing module
│
├── input_dialog.py
│   └── GUI parameter input
│
├── main_selector.py
│   └── Main GUI selector
│
├── i18n.py
│   └── Internationalization / language-related functionality
│
├── requirements.txt
│   └── Python dependencies
│
└── README.md
    └── Chinese documentation
```

---

# 🚀 Installation

## 1. Clone the Repository

```bash
git clone https://github.com/ZihanZhang114514/Welding-Defect-Detection-System-Based-on-YOLO-v8-and-API-579.git
```

Enter the project directory:

```bash
cd Welding-Defect-Detection-System-Based-on-YOLO-v8-and-API-579
```

---

## 2. Install Dependencies

Python 3.8 or newer is recommended.

```bash
pip install -r requirements.txt
```

---

# ▶️ Run the Application

If `start.bat` is available, simply run:

```text
start.bat
```

Alternatively:

```bash
python main_selector.py
```

After launching, the main defect-type selection window will appear.

---

# 🧭 Usage Guide

## Step 1 — Select Defect Type

Select the defect type to be assessed.

The current system provides processing modules for:

- **CR — Crack**
- **LP — Lack of Penetration**
- **PO — Porosity / Bubble**

---

## Step 2 — Enter Parameters

After selecting the defect type, the corresponding assessment program will start and display the parameter input interface.

Depending on the assessment type, the user may need to enter:

```text
Inspection image directory
Original image length
Original image width
Container wall thickness
```

For crack assessment, additional parameters are required:

```text
Steel material type
API 579 assessment curve type
Minimum Yield Strength (MYS)
Other relevant engineering parameters
```

---

## Step 3 — Start Detection

After all required parameters have been entered, click:

```text
Start Detection
```

The system will automatically:

1. Read the images in the selected directory.
2. Load the corresponding YOLOv8 model.
3. Detect welding defects.
4. Obtain defect locations.
5. Process the detected regions.
6. Apply the sliding-window algorithm.
7. Perform the corresponding engineering assessment.
8. Draw the assessment results on the images.
9. Save the processed images.
10. Generate the inspection report.

---

# 📊 Output Results

After all images in the selected directory have been processed, the program displays a completion message.

The system provides information about:

- Output directory
- Processing time

The output directory can then be opened automatically.

---

## Result Visualization

The processed images contain the detection and assessment results.

### Passed Assessment

A **green bounding box** indicates that the corresponding region passed the assessment.

### Failed Assessment

A **red bounding box** indicates that the corresponding region failed the assessment.

---

# 📏 Defect Dimension Annotation

The system can annotate the dimensions of individual detected defects.

A simplified representation is:

```text
┌─────────────────────────────┐
│                             │
│        Defect Region        │
│     ←──── Length ────→      │
│             ↑               │
│             │ Width         │
│             ↓               │
│                             │
└─────────────────────────────┘
```

The obtained geometric information can be used in the subsequent assessment process.

---

# 📄 Word Inspection Report

The system supports automatic generation of a Word-format inspection report after the detection and assessment process.

The report is generated by:

```text
CrFrameAndReport.py
```

The report can be used to organize and preserve the detection and assessment results.

---

# 🔄 Complete Processing Pipeline

```text
             X-ray Inspection Image
                       │
                       ▼
              Defect Type Selection
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       ┌──────┐     ┌──────┐     ┌──────┐
       │  CR  │     │  LP  │     │  PO  │
       │Crack │     │  LOP │     │Porosity│
       └───┬──┘     └───┬──┘     └───┬──┘
           │            │            │
           └────────────┼────────────┘
                        ▼
                 ┌──────────────┐
                 │    YOLOv8    │
                 │   Detection  │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ Sliding      │
                 │ Window       │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ Geometric    │
                 │ Parameters   │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ API 579 FFS  │
                 │ Assessment   │
                 └──────┬───────┘
                        │
                 ┌──────┴──────┐
                 ▼             ▼
              Passed         Failed
                 │             │
                 └──────┬──────┘
                        ▼
                 Result Annotation
                        │
                        ▼
                 Word Inspection Report
```

---

# 🛠️ Technology Stack

| Category | Technology |
|---|---|
| Programming Language | Python |
| Deep Learning | YOLOv8 / Ultralytics |
| Image Processing | OpenCV |
| GUI | Tkinter |
| Numerical Processing | NumPy |
| Data Processing | CSV / JSON |
| Report Generation | python-docx |
| Engineering Assessment | API 579 FFS |
| Defect Analysis | Sliding-Window Algorithm |

---

# 🎯 Project Objective

The goal of this project is not simply to perform object detection.

Instead, it attempts to combine:

```text
Machine Vision
      +
Deep Learning Object Detection
      +
Defect Geometry Analysis
      +
API 579 FFS Assessment
      +
Automated Report Generation
```

into an integrated welding defect detection and assessment workflow.

The overall objective is:

> **To establish an automated auxiliary workflow from welding defect detection in X-ray inspection images, through defect-region analysis and engineering assessment, to result visualization and report generation.**

---

# 📌 Current Features

- [x] YOLOv8 welding defect detection
- [x] Defect-type selection GUI
- [x] Inspection image directory selection
- [x] Engineering parameter input
- [x] Sliding-window defect analysis
- [x] API 579-related assessment
- [x] Detection result visualization
- [x] Pass / Fail annotation
- [x] Defect dimension annotation
- [x] Automatic Word report generation
- [x] CSV / JSON data processing
- [x] Windows GUI application

---

# 🔮 Future Improvements

## Model Improvements

Potential future improvements include:

- Expanding the welding defect dataset
- Improving annotation and data quality
- Comparing different object detection models
- Improving detection of small defects
- Adding more comprehensive model evaluation and visualization

---

## Engineering Assessment

Potential improvements include:

- Supporting additional API 579 assessment scenarios
- Improving engineering parameter validation
- Displaying calculation procedures and intermediate results
- Improving handling of abnormal or invalid parameters

---

## Software Engineering

Potential improvements include:

- Improving the GUI
- Adding batch-processing task management
- Adding detection history
- Improving report templates
- Adding statistical summaries
- Adding a more comprehensive logging system

---

## Deployment

The application could potentially be packaged as an independent desktop application in the future to reduce the need for users to configure the Python environment manually.

---

# 📚 Documentation

The project includes a V1.0 user manual covering:

- System objectives
- System architecture
- Overall design
- Development environment
- Core algorithms
- GUI usage
- Output results
- Inspection report generation

---

# ⚠️ Disclaimer

This project is intended primarily for **research, educational, and engineering-assistance purposes**.

The accuracy of the detection results depends on the performance of the trained YOLOv8 models and the quality of the input inspection images.

API 579-related assessment results depend on the correctness of the input engineering and material parameters and the applicability of the selected assessment method.

The software should **not be used as the sole basis for real-world engineering safety decisions** without appropriate professional review and verification.

Actual Fitness-For-Service assessments should be performed and confirmed by qualified engineering professionals in accordance with applicable standards, engineering conditions, and inspection data.

---

# 👤 Author

**Zihan Zhang**

Process Equipment and Control Engineering  
Changzhou University

GitHub:

https://github.com/ZihanZhang114514

---

# ⭐ Acknowledgement

If you find this project useful for research or learning, feel free to Star or Fork the repository.

The project focuses on the intersection of:

- YOLOv8
- Computer Vision
- Welding Defect Detection
- X-ray Non-Destructive Testing
- API 579 FFS
- Industrial AI
- Engineering Integrity Assessment

---

<p align="center">

[中文 README](README.md) · [English README](README_EN.md)

</p>
