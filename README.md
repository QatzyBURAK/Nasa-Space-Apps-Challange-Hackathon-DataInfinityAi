# Nasa-Space-Apps-Challange-Hackathon-DataInfinityAi
AI system that analyzes NASA and global geospatial data to detect unused lands and evaluate their agricultural productivity. Helps governments identify sustainable development zones and optimize land use. 
# 🌍 DataInfinityAI  
**AI-Driven Earth Observation & Agricultural Productivity Analysis**  
### NASA Space Apps Challenge 2025 — Project: DATAFARM  
🔗 [Live Website](https://datainfinityai.com)

---

## 🧠 Overview
**DataInfinityAI** is an AI-powered Earth observation platform that analyzes NASA and global geospatial datasets to detect **unused or underutilized lands** and evaluate **their agricultural productivity potential**.  
By merging environmental data and AI-driven analytics, the system helps governments and organizations identify **sustainable development zones** and **optimize land use** for food production and climate resilience.

---

## 🚀 Key Features
- 🌊 **Water Source Detection** via OpenStreetMap (OSM)  
- 🛰 **Integration with NASA Satellite Data**  
- 🤖 **AI-Based Productivity Evaluation** using:
  - Water proximity  
  - Slope & elevation  
  - Soil pH & fertility  
  - Precipitation & sunshine hours  
  - Landcover classification  
- ⚙️ **Automated Data Processing** with FastAPI backend  
- 📁 **Detailed CSV & JSON Reports**  
- 🌐 **Modern Interactive Frontend Interface**  
- 🧩 **Scalable Architecture** ready for global agricultural and sustainability applications  

---

## 🏗️ System Architecture

hackatlon/
├── backend/
│ ├── main.py
│ ├── model.py
│ ├── data/
│ │ ├── AKILLI_tarimsal_analiz.csv
│ │ ├── HIZLI_tarimsal_uygunluk_analizi.csv
│ │ ├── KAPSAMLI_tarimsal_verimlilik.csv
│ │ ├── COMPREHENSIVE_agricultural_productivity.csv
│ │ ├── osm_tarim_alanlari.csv
│ │ └── turkiye_detayli_tarim_alanlari.csv
│ ├── cache/
│ │ └── turkiye_water_sources_cache.json
│ └── results/
│ └── productivity_report.json
│
└── frontend/
├── index.html
├── proje_detay.html
├── iletisim.html
└── assets/
├── nasa1.jpg
├── nasa2.jpg
├── nasa3.jpg
├── nasa4.jpg
└── data2.jpg


---

## 🧩 Tech Stack

| Layer | Technologies |
|-------|---------------|
| **Backend** | Python, FastAPI, Pandas, NumPy |
| **Frontend** | HTML, CSS, JavaScript |
| **Data Sources** | NASA Earth Data, OpenStreetMap, FAO Soil & Water Data |
| **Output** | CSV, JSON, Web Reports |
| **Deployment** | [datainfinityai.com](https://datainfinityai.com) |

---

## 🌾 Sample Analysis Output

🌾 COMPREHENSIVE AGRICULTURAL PRODUCTIVITY ANALYSIS
🌊 Fetching water sources from OpenStreetMap...
✅ 158099 water sources found!
📊 97450 coordinates loaded
⚡ First 2000 records analyzed
✅ 100 productive areas found!

📊 COMPREHENSIVE PRODUCTIVITY REPORT:
Total analyzed: 1997
Productive areas: 100
Success rate: 5.0%

🏆 TOP 3 MOST PRODUCTIVE AREAS:
📍 (39.0571, 36.1713) — Score: 87/100
📍 (40.7214, 41.8005) — Score: 87/100
📍 (40.7522, 41.8280) — Score: 87/100

---

## 🌐 Website Pages

| Page | Description |
|------|--------------|
| `index.html` | Interactive project homepage with animations & login system |
| `proje_detay.html` | Project details and AI analysis visualization |
| `iletisim.html` | Contact page showing global organization references (WHO, FAO, UNEP, etc.) |

---

## 🧭 Vision
DataInfinityAI aims to **empower sustainable agriculture** through intelligent data processing.  
The project focuses on identifying land potential globally — promoting efficient farming, environmental sustainability, and responsible use of natural resources.

---

## 🪐 Credits
Developed by **Team DataInfinity** for the **NASA Space Apps Challenge 2025**.  
All data sourced from **NASA**, **OpenStreetMap**, and public Earth observation datasets.  

---

## ⚖️ License
This project is licensed under the **MIT License** — free to use, modify, and share with attribution.

---

🌍 *“Empowering humanity through intelligent Earth data.”*  
🚀 **DataInfinityAI — AI for Sustainable Planet**
