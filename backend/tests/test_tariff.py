# backend/test_tariff.py
from datetime import datetime
from utils.tariff_classifier import TariffClassifier

# Test cases
test_cases = [
    datetime(2025, 10, 30, 8, 0),   # Thursday 8 AM - Intermedio
    datetime(2025, 10, 30, 12, 0),  # Thursday 12 PM - Base
    datetime(2025, 10, 30, 19, 0),  # Thursday 7 PM - Punta
    datetime(2025, 10, 30, 23, 0),  # Thursday 11 PM - Intermedio
    datetime(2025, 11, 2, 12, 0),   # Saturday 12 PM - Base (weekend)
    datetime(2025, 11, 3, 19, 0),   # Sunday 7 PM - Base (weekend)
]

print("Tariff Classification Tests:\n")
for dt in test_cases:
    tariff = TariffClassifier.classify_tariff(dt)
    day_name = dt.strftime("%A")
    time_str = dt.strftime("%I:%M %p")
    print(f"{day_name} {time_str} → {tariff}")
