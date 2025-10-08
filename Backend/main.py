# main.py - GERÇEK VERİLİ API
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import numpy as np
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from typing import List, Optional
import io
import os

app = FastAPI(
    title="Turkey Agricultural Land API",
    description="Agricultural land suitability analysis for Turkey",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# MODELLER
class AnalysisRequest(BaseModel):
    coordinates: List[List[float]]
    max_areas: int = 100
    sample_size: int = 5000


class SingleCoordinateRequest(BaseModel):
    lat: float
    lon: float


class AreaDetail(BaseModel):
    rank: int
    coordinates: str
    score: int
    category: str
    water: str
    slope: str
    elevation: str
    soil: str
    precipitation: str
    sunshine: str
    details: str


class ComprehensiveResponse(BaseModel):
    success: bool
    message: str
    analysis_type: str
    summary: dict
    top_areas: List[AreaDetail]
    processing_time: float
    visual_output: str


# 🌊 GERÇEK SU KAYNAKLARI FONKSİYONLARI
def get_all_water_sources_from_osm():
    """Get all water sources in Turkey from OpenStreetMap"""
    print("🌊 Fetching water sources from OpenStreetMap...")

    # Önceden cache'lenmiş su kaynaklarını kontrol et
    cache_file = "turkiye_water_sources_cache.json"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                print(f"✅ {len(cached_data)} water sources loaded from cache!")
                return cached_data
        except:
            pass

    # Turkey bbox
    turkey_bbox = "26.0,36.0,45.0,42.0"

    # Query for all water sources
    water_query = f"""
    [out:json][timeout:180];
    (
      way["waterway"="river"]({turkey_bbox});
      way["waterway"="stream"]({turkey_bbox});
      relation["waterway"="river"]({turkey_bbox});
      way["natural"="water"]({turkey_bbox});
      way["water"="lake"]({turkey_bbox});
      way["water"="reservoir"]({turkey_bbox});
      relation["natural"="water"]({turkey_bbox});
      way["waterway"="dam"]({turkey_bbox});
    );
    out center;
    """

    try:
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=water_query,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=300
        )

        if response.status_code == 200:
            data = response.json()
            water_sources = []

            for element in data['elements']:
                if 'center' in element:
                    lat = element['center']['lat']
                    lon = element['center']['lon']

                    tags = element.get('tags', {})
                    water_type = ""
                    name = tags.get('name', 'Unnamed')

                    if 'waterway' in tags:
                        if tags['waterway'] == 'river':
                            water_type = "river"
                        elif tags['waterway'] == 'stream':
                            water_type = "stream"
                        elif tags['waterway'] == 'dam':
                            water_type = "dam"
                    elif 'natural' in tags and tags['natural'] == 'water':
                        water_type = "lake"
                    elif 'water' in tags:
                        if tags['water'] == 'lake':
                            water_type = "lake"
                        elif tags['water'] == 'reservoir':
                            water_type = "reservoir"

                    if water_type:
                        water_sources.append({
                            'lat': lat,
                            'lon': lon,
                            'name': name,
                            'type': water_type,
                            'source': 'OpenStreetMap'
                        })

            # Cache'e kaydet
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(water_sources, f, ensure_ascii=False, indent=2)
            except:
                pass

            print(f"✅ {len(water_sources)} water sources found!")
            return water_sources
        else:
            print(f"❌ OSM error: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ OSM connection error: {e}")
        return []


def calculate_distance_to_nearest_water(lat, lon, water_sources):
    """Calculate distance to nearest water source"""
    min_distance = float('inf')
    nearest_water = {"name": "unknown", "type": "unknown", "distance_km": 0}

    for water in water_sources:
        distance_km = np.sqrt((lat - water['lat']) ** 2 + (lon - water['lon']) ** 2) * 111
        if distance_km < min_distance:
            min_distance = distance_km
            nearest_water = {
                "name": water['name'],
                "type": water['type'],
                "distance_km": distance_km
            }

    return nearest_water


def get_climate_data(lat, lon):
    """Estimate climate data"""
    if lat < 37.0:
        return {
            "annual_precipitation_mm": 650,
            "sunshine_hours": 2950,
            "average_temperature": 18.5,
            "climate_type": "Mediterranean"
        }
    elif lat < 39.0:
        return {
            "annual_precipitation_mm": 380,
            "sunshine_hours": 2650,
            "average_temperature": 11.2,
            "climate_type": "Continental"
        }
    elif lat < 41.0:
        return {
            "annual_precipitation_mm": 850,
            "sunshine_hours": 1950,
            "average_temperature": 14.0,
            "climate_type": "Black Sea"
        }
    else:
        return {
            "annual_precipitation_mm": 450,
            "sunshine_hours": 2450,
            "average_temperature": 8.5,
            "climate_type": "Severe Continental"
        }


def estimate_soil_quality(lat, lon, elevation):
    """Estimate soil quality"""
    if elevation < 200:
        return {
            "soil_type": "Loamy",
            "soil_ph": 6.8,
            "organic_matter": 2.3,
            "productivity": "high"
        }
    elif elevation < 500:
        return {
            "soil_type": "Clay-Loamy",
            "soil_ph": 7.1,
            "organic_matter": 1.8,
            "productivity": "medium-high"
        }
    elif elevation < 1000:
        return {
            "soil_type": "Loamy-Sandy",
            "soil_ph": 6.5,
            "organic_matter": 1.2,
            "productivity": "medium"
        }
    else:
        return {
            "soil_type": "Stony-Sandy",
            "soil_ph": 5.8,
            "organic_matter": 0.7,
            "productivity": "low"
        }


def calculate_comprehensive_suitability(row):
    """Calculate comprehensive productivity score"""
    score = 0
    reasons = []
    details = []

    # WATER
    water_dist_km = row['water_distance_km']
    if water_dist_km <= 5:
        score += 25
        reasons.append("very close to water")
        details.append(f"💧 Water: {water_dist_km:.1f}km ({row['nearest_water_name']}) - EXCELLENT")
    elif water_dist_km <= 10:
        score += 18
        reasons.append("close to water")
        details.append(f"💧 Water: {water_dist_km:.1f}km ({row['nearest_water_name']}) - GOOD")

    # SLOPE
    slope = row['slope_percent']
    if slope <= 5:
        score += 20
        reasons.append("low slope")
        details.append(f"📐 Slope: {slope:.1f}% - EXCELLENT")
    elif slope <= 10:
        score += 15
        reasons.append("medium slope")
        details.append(f"📐 Slope: {slope:.1f}% - GOOD")

    # ELEVATION
    elevation = row['elevation_m']
    if elevation <= 800:
        score += 15
        reasons.append("low elevation")
        details.append(f"⛰ Elevation: {elevation}m - EXCELLENT")
    elif elevation <= 1500:
        score += 10
        reasons.append("medium elevation")
        details.append(f"⛰ Elevation: {elevation}m - GOOD")

    # SOIL
    soil_quality = row['soil_productivity']
    if soil_quality == "high":
        score += 10
        reasons.append("fertile soil")
        details.append(f"🌱 Soil: {row['soil_type']} (pH:{row['soil_ph']}) - EXCELLENT")
    elif soil_quality == "medium-high":
        score += 7
        reasons.append("good soil")
        details.append(f"🌱 Soil: {row['soil_type']} (pH:{row['soil_ph']}) - GOOD")

    # CLIMATE
    precipitation = row['annual_precipitation_mm']
    if 400 <= precipitation <= 800:
        score += 8
        reasons.append("ideal precipitation")
        details.append(f"🌧 Precipitation: {precipitation}mm - EXCELLENT")

    # SUNSHINE
    sunshine = row['sunshine_hours']
    if 1800 <= sunshine <= 2800:
        score += 7
        reasons.append("ideal sunshine")
        details.append(f"☀ Sunshine: {sunshine} hours - EXCELLENT")

    # LANDCOVER BONUS
    lc_type = str(row.get('landcover_type', '')).lower()
    if any(keyword in lc_type for keyword in ['farm', 'agricultural', 'orchard', 'vineyard']):
        score += 8
        reasons.append("existing agricultural land")
        details.append(f"🏞 Landcover: {lc_type} - BONUS")

    detailed_reason = " | ".join(details)
    return score, ", ".join(reasons), detailed_reason


def quick_elevation_estimate(lat, lon):
    if lat < 37.0:
        return np.random.uniform(50, 300)
    elif lat < 39.0:
        return np.random.uniform(800, 1200)
    elif lat < 41.0:
        return np.random.uniform(200, 800)
    else:
        return np.random.uniform(1000, 1800)


def quick_slope_estimate(elevation, lat, lon):
    if elevation < 200:
        return np.random.uniform(1, 3)
    elif elevation < 500:
        return np.random.uniform(2, 6)
    elif elevation < 1000:
        return np.random.uniform(5, 10)
    else:
        return np.random.uniform(8, 20)


def calculate_realistic_urban_distance(lat, lon):
    cities = [(39.9, 32.8), (41.0, 28.9), (38.4, 27.1), (36.9, 35.3)]
    min_dist = min([np.sqrt((lat - c[0]) ** 2 + (lon - c[1]) ** 2) * 111 for c in cities])
    return min_dist * 1000 * np.random.uniform(0.8, 1.2)


def categorize_suitability(score):
    if score >= 80:
        return "HIGHLY PRODUCTIVE"
    elif score >= 70:
        return "PRODUCTIVE"
    elif score >= 60:
        return "MODERATELY PRODUCTIVE"
    else:
        return "LOW PRODUCTIVITY"


def analyze_coordinate_with_real_water(coord_data, water_sources):
    """Coordinate analysis with real water sources"""
    lat, lon, original_data = coord_data

    if not (36.0 <= lat <= 42.0) and (26.0 <= lon <= 45.0):
        return None

    # Calculations
    elevation = quick_elevation_estimate(lat, lon)
    slope = quick_slope_estimate(elevation, lat, lon)

    # Real water distance
    nearest_water = calculate_distance_to_nearest_water(lat, lon, water_sources)

    # Urban distance
    urban_dist_km = calculate_realistic_urban_distance(lat, lon) / 1000

    # Climate and soil data
    climate_data = get_climate_data(lat, lon)
    soil_data = estimate_soil_quality(lat, lon, elevation)

    # Prepare data
    enhanced_row = {
        'latitude': lat,
        'longitude': lon,
        'elevation_m': round(elevation),
        'slope_percent': round(slope, 1),
        'water_distance_km': round(nearest_water['distance_km'], 1),
        'nearest_water_name': nearest_water['name'],
        'nearest_water_type': nearest_water['type'],
        'urban_distance_km': round(urban_dist_km, 1),
        'soil_type': soil_data['soil_type'],
        'soil_ph': soil_data['soil_ph'],
        'soil_productivity': soil_data['productivity'],
        'annual_precipitation_mm': climate_data['annual_precipitation_mm'],
        'sunshine_hours': climate_data['sunshine_hours'],
        'climate_type': climate_data['climate_type'],
        'landcover_type': original_data.get('type', 'agriculture'),
        'region_name': original_data.get('name', ''),
        'data_source': original_data.get('source', 'OSM')
    }

    # Comprehensive suitability score
    score, reasons, detailed_reasons = calculate_comprehensive_suitability(enhanced_row)
    enhanced_row['suitability_score'] = score
    enhanced_row['suitability_reasons'] = reasons
    enhanced_row['detailed_reasons'] = detailed_reasons
    enhanced_row['suitability_category'] = categorize_suitability(score)

    return enhanced_row


# 🌟 RENKLİ ÇIKTI OLUŞTURMA
def create_visual_output(analysis_result):
    output = "🌾 COMPREHENSIVE AGRICULTURAL PRODUCTIVITY ANALYSIS\n"
    output += "=" * 65 + "\n"

    summary = analysis_result["summary"]
    output += f"📊 COMPREHENSIVE PRODUCTIVITY REPORT:\n"
    output += f"Total analyzed: {summary['total_analyzed']}\n"
    output += f"Productive areas: {summary['productive_areas']}\n"
    output += f"Success rate: {summary['success_rate']}%\n\n"

    output += "🏆 TOP 3 MOST PRODUCTIVE AREAS:\n\n"

    for area in analysis_result["top_areas"][:3]:
        output += f"📍 {area['rank']}. {area['coordinates']}\n"
        output += f"   🎯 PRODUCTIVITY SCORE: {area['score']}/100\n"
        output += f"   📈 CATEGORY: {area['category']}\n"
        output += f"   💧 WATER: {area['water']}\n"
        output += f"   📐 SLOPE: {area['slope']}\n"
        output += f"   ⛰ ELEVATION: {area['elevation']}\n"
        output += f"   🌱 SOIL: {area['soil']}\n"
        output += f"   🌧 PRECIPITATION: {area['precipitation']}\n"
        output += f"   ☀ SUNSHINE: {area['sunshine']}\n"
        output += f"   📝 DETAILS: {area['details']}\n\n"

    output += f"⏱ Total time: {analysis_result['processing_time']} seconds\n"
    return output


# 📊 CSV'DEN GERÇEK VERİ OKUMA
def load_coordinates_from_csv():
    """CSV dosyalarından gerçek koordinatları yükle"""
    csv_files = [
        "osm_tarim_alanlari.csv",
        "turkiye_detayli_tarim_alanlari.csv",
        "AKILLI_tarimsal_analiz.csv"
    ]

    all_coordinates = []

    for csv_file in csv_files:
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file, encoding='utf-8')
                print(f"✅ {len(df)} coordinates loaded from {csv_file}")

                # Farklı kolon isimlerini kontrol et
                if 'lat' in df.columns and 'lon' in df.columns:
                    for _, row in df.iterrows():
                        all_coordinates.append([row['lat'], row['lon']])
                elif 'latitude' in df.columns and 'longitude' in df.columns:
                    for _, row in df.iterrows():
                        all_coordinates.append([row['latitude'], row['longitude']])

            except Exception as e:
                print(f"❌ Error reading {csv_file}: {e}")

    # Eğer CSV'den koordinat bulunamazsa, örnek koordinatlar kullan
    if not all_coordinates:
        print("⚠️ No CSV files found, using sample coordinates")
        all_coordinates = [
            [39.9334, 32.8597], [41.0082, 28.9784], [38.4237, 27.1428],
            [36.9864, 35.3253], [40.1885, 29.0610], [37.9144, 40.2306],
            [41.2867, 36.3300], [36.8000, 34.6333], [39.0571, 36.1713],
            [40.7214, 41.8005], [40.7522, 41.8280]
        ]

    return all_coordinates


# 🚀 GERÇEK VERİLİ ANALİZ ENDPOINT'İ
@app.post("/api/comprehensive-real-analysis")
async def comprehensive_real_analysis(max_areas: int = 100, sample_size: int = 5000):
    """Gerçek su kaynakları ve CSV verileri ile analiz"""
    try:
        start_time = time.time()

        print("🌊 Fetching real water sources...")
        water_sources = get_all_water_sources_from_osm()
        if not water_sources:
            return {
                "success": False,
                "message": "Water sources could not be retrieved"
            }

        print("📊 Loading coordinates from CSV files...")
        coordinates = load_coordinates_from_csv()

        # Örnekleme
        if len(coordinates) > sample_size:
            coordinates = coordinates[:sample_size]

        print(f"🔍 Analyzing {len(coordinates)} coordinates with real water data...")

        suitable_areas = []
        processed = 0

        # Paralel analiz
        with ThreadPoolExecutor(max_workers=6) as executor:
            coord_list = [(lat, lon, {}) for lat, lon in coordinates]
            future_to_coord = {
                executor.submit(analyze_coordinate_with_real_water, coord, water_sources): coord
                for coord in coord_list
            }

            for future in as_completed(future_to_coord):
                processed += 1
                result = future.result()

                if result and result['suitability_score'] >= 60:
                    suitable_areas.append(result)
                    if len(suitable_areas) >= max_areas:
                        break

                if processed % 50 == 0:
                    print(f"📍 {processed}/{len(coordinates)} processed - {len(suitable_areas)} productive areas")

        processing_time = time.time() - start_time

        # Format results
        top_areas_formatted = []
        for i, area in enumerate(suitable_areas[:10], 1):
            top_areas_formatted.append({
                "rank": i,
                "coordinates": f"{area['latitude']:.4f}, {area['longitude']:.4f}",
                "score": area['suitability_score'],
                "category": area['suitability_category'],
                "water": f"{area['water_distance_km']}km ({area['nearest_water_name']})",
                "slope": f"{area['slope_percent']}%",
                "elevation": f"{area['elevation_m']}m",
                "soil": f"{area['soil_type']} (pH:{area['soil_ph']})",
                "precipitation": f"{area['annual_precipitation_mm']}mm",
                "sunshine": f"{area['sunshine_hours']} hours",
                "details": area['detailed_reasons']
            })

        analysis_data = {
            "summary": {
                "total_analyzed": processed,
                "productive_areas": len(suitable_areas),
                "success_rate": round((len(suitable_areas) / processed * 100), 2) if processed > 0 else 0
            },
            "top_areas": top_areas_formatted,
            "processing_time": round(processing_time, 2)
        }

        # Renkli çıktı oluştur
        visual_output = create_visual_output(analysis_data)

        return {
            "success": True,
            "message": "Comprehensive real-data analysis completed",
            "analysis_type": "REAL_DATA_ANALYSIS",
            "summary": analysis_data["summary"],
            "top_areas": top_areas_formatted,
            "processing_time": processing_time,
            "visual_output": visual_output
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Real data analysis error: {str(e)}"
        }


# 📋 DİĞER ENDPOINT'LER
@app.get("/")
async def root():
    return {"status": "active", "message": "Turkey Agricultural Land Analysis API with Real Data"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/api/water-sources")
async def get_water_sources():
    """Su kaynaklarını getir"""
    water_sources = get_all_water_sources_from_osm()
    return {
        "success": True,
        "water_sources_count": len(water_sources),
        "water_sources": water_sources[:100]  # İlk 100'ü göster
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)