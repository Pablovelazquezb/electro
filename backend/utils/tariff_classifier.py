# backend/utils/tariff_classifier.py
from datetime import datetime, time
from typing import Literal

TariffType = Literal["Base", "Intermedio", "Punta"]

class TariffClassifier:
    """
    Classifies energy consumption into CFE (Comisión Federal de Electricidad) tariff periods
    based on Mexican electricity tariff schedules.
    
    Tariff Types:
    - Base: Off-peak hours (lowest rate)
    - Intermedio: Intermediate hours (medium rate)
    - Punta: Peak hours (highest rate)
    """
    
    # CFE Tariff Schedule (GDMTH - Gran Demanda en Media Tensión Horaria)
    # These times may vary by region - adjust as needed
    
    @staticmethod
    def classify_tariff(timestamp: datetime) -> TariffType:
        """
        Classify a timestamp into a tariff period
        
        Args:
            timestamp: DateTime to classify
            
        Returns:
            Tariff type: "Base", "Intermedio", or "Punta"
        """
        hour = timestamp.hour
        minute = timestamp.minute
        day_of_week = timestamp.weekday()  # 0 = Monday, 6 = Sunday
        
        # Convert to time for easier comparison
        current_time = time(hour, minute)
        
        # Check if it's a weekend (Saturday=5, Sunday=6)
        is_weekend = day_of_week >= 5
        
        if is_weekend:
            # Weekends: All hours are BASE
            return "Base"
        
        # Weekdays (Monday-Friday) schedule
        return TariffClassifier._classify_weekday(current_time)
    
    @staticmethod
    def _classify_weekday(current_time: time) -> TariffType:
        """
        Classify weekday hours into tariff periods
        
        Standard GDMTH Schedule (may vary by region):
        - Punta (Peak): 18:00 - 22:00 (6 PM - 10 PM)
        - Intermedio (Intermediate): 
            * Morning: 06:00 - 10:00 (6 AM - 10 AM)
            * Evening: 22:00 - 00:00 (10 PM - 12 AM)
        - Base (Off-peak): All other hours
        """
        
        # Define time periods
        # Peak hours: 6 PM to 10 PM
        peak_start = time(18, 0)
        peak_end = time(22, 0)
        
        # Intermediate periods
        intermediate_morning_start = time(6, 0)
        intermediate_morning_end = time(10, 0)
        intermediate_evening_start = time(22, 0)
        intermediate_evening_end = time(23, 59, 59)
        
        # Base period (rest of the hours)
        base_night_end = time(6, 0)
        base_day_start = time(10, 0)
        base_day_end = time(18, 0)
        
        # Check PUNTA (Peak)
        if peak_start <= current_time < peak_end:
            return "Punta"
        
        # Check INTERMEDIO (Intermediate)
        if (intermediate_morning_start <= current_time < intermediate_morning_end or
            intermediate_evening_start <= current_time <= intermediate_evening_end):
            return "Intermedio"
        
        # Everything else is BASE (Off-peak)
        return "Base"
    
    @staticmethod
    def get_tariff_info(tariff: TariffType) -> dict:
        """
        Get information about a tariff type
        
        Args:
            tariff: Tariff type
            
        Returns:
            Dict with tariff information
        """
        tariff_info = {
            "Base": {
                "name": "Base",
                "description": "Off-peak hours",
                "typical_rate": 1.20,  # Example rate in MXN/kWh
                "color": "#4CAF50"  # Green
            },
            "Intermedio": {
                "name": "Intermedio",
                "description": "Intermediate hours",
                "typical_rate": 1.98,  # Example rate in MXN/kWh
                "color": "#FF9800"  # Orange
            },
            "Punta": {
                "name": "Punta",
                "description": "Peak hours",
                "typical_rate": 2.32,  # Example rate in MXN/kWh
                "color": "#F44336"  # Red
            }
        }
        
        return tariff_info.get(tariff, {})


# Convenience function
def classify_tariff(timestamp: datetime) -> TariffType:
    """Shortcut function to classify a tariff"""
    return TariffClassifier.classify_tariff(timestamp)
