# backend/services/egauge_service.py
from datetime import datetime
from typing import Dict, Any, List
from egauge import webapi
import traceback
from config import Config
from utils.sanitizers import sanitize_column_name, make_columns_unique
from utils.tariff_classifier import TariffClassifier

class EGaugeService:
    """Service for eGauge device interactions"""
    
    def __init__(self):
        self.user = Config.EGAUGE_USER
        self.password = Config.EGAUGE_PASSWORD
    
    def extract_data(
        self,
        url: str,
        start_date: datetime,
        end_date: datetime,
        delta_hours: int = 1
    ) -> Dict[str, Any]:
        """Extract data from eGauge device"""
        try:
            print(f"\n{'='*60}")
            print(f"🔌 Connecting to eGauge: {url}")
            print(f"📅 Date range: {start_date} to {end_date}")
            print(f"⏱️  Interval: {delta_hours} hour(s)")
            print(f"{'='*60}")
            
            # Connect to device
            try:
                dev = webapi.device.Device(
                    url,
                    webapi.JWTAuth(self.user, self.password)
                )
                print("✅ Connected to device")
            except Exception as auth_error:
                print(f"❌ Authentication failed: {auth_error}")
                return {
                    'success': False,
                    'error': f'Authentication failed: {str(auth_error)}'
                }
            
            # Configure time range
            delta_seconds = delta_hours * 3600
            start_ts = int(start_date.timestamp())
            end_ts = int(end_date.timestamp())
            time_param = f"{start_ts}:{delta_seconds}:{end_ts}"
            
            print(f"📊 Time parameter: {time_param}")
            
            # Adjust if end date is in the future
            now = datetime.now()
            if end_date > now:
                print(f"⚠️  Warning: End date is in the future, adjusting to now")
                end_date = now
                end_ts = int(end_date.timestamp())
                time_param = f"{start_ts}:{delta_seconds}:{end_ts}"
            
            # Fetch data
            try:
                print("📥 Requesting data from device...")
                ret = webapi.device.Register(dev, {"time": time_param})
                rows = list(ret)
                print(f"✅ Received {len(rows)} data rows")
            except Exception as data_error:
                print(f"❌ Failed to read data: {data_error}")
                return {
                    'success': False,
                    'error': (
                        f'Failed to read data from device. The device may not have '
                        f'data for this period. Error: {str(data_error)}'
                    )
                }
            
            # Validate data
            if len(rows) < 2:
                return {
                    'success': False,
                    'error': (
                        f'Not enough data in the specified range. Received only '
                        f'{len(rows)} rows. The device may not have data for this period.'
                    )
                }
            
            # Extract column names - make them unique
            registers = list(ret.regs)
            sanitized_registers = make_columns_unique(registers)
            
            # Create mapping of original to sanitized names
            register_mapping = dict(zip(registers, sanitized_registers))
            
            columns = ['Date', 'Time', 'Timestamp'] + registers
            print(f"📋 Columns found: {', '.join(registers)}")
            print(f"📋 Sanitized columns: {', '.join(sanitized_registers)}")
            
            # Process data
            data = self._process_rows(rows, registers, register_mapping)
            
            print(f"✅ Successfully processed {len(data)} data points")
            print(f"{'='*60}\n")
            
            return {
                'success': True,
                'columns': columns,
                'sanitized_columns': sanitized_registers,
                'register_mapping': register_mapping,
                'data': data,
                'total_records': len(data)
            }
        
        except Exception as e:
            print(f"❌ Unexpected error extracting data: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def _process_rows(
        self,
        rows: List,
        registers: List[str],
        register_mapping: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Process raw eGauge rows into structured data with tariff classification"""
        data = []
        
        for i in range(len(rows) - 1):
            delta_row = rows[i] - rows[i + 1]
            timestamp_float = float(rows[i + 1].ts)
            timestamp = datetime.fromtimestamp(timestamp_float)
            
            # Classify tariff based on timestamp
            tariff = TariffClassifier.classify_tariff(timestamp)
            
            row = {
                'date': timestamp.strftime("%Y-%m-%d"),
                'time': timestamp.strftime("%H:%M:%S"),
                'timestamp': int(timestamp_float),
                'tariff': tariff  # Add tariff classification
            }
            
            # Add values for each register using sanitized names
            for regname in registers:
                accu = delta_row.pq_accu(regname)
                col_name = register_mapping[regname]
                row[col_name] = float(accu.value) if accu else 0.0
            
            data.append(row)
        
        return data
    
    @staticmethod
    def generate_table_sql(table_name: str, sanitized_columns: List[str]) -> str:
        """Generate SQL for creating a dynamic table"""
        columns_sql = [
            "id UUID PRIMARY KEY DEFAULT gen_random_uuid()",
            "date DATE NOT NULL",
            "time TIME NOT NULL",
            "timestamp_egauge BIGINT NOT NULL",
            "tariff VARCHAR(20)",  # Add tariff column
            "created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"
        ]
        
        # Add sanitized columns (they're already sanitized)
        for col in sanitized_columns:
            columns_sql.append(f"{col} FLOAT")
        
        return f"""
CREATE TABLE IF NOT EXISTS {table_name} (
    {',\n    '.join(columns_sql)},
    UNIQUE(timestamp_egauge)
);

CREATE INDEX IF NOT EXISTS idx_{table_name}_date ON {table_name}(date);
CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON {table_name}(timestamp_egauge);
CREATE INDEX IF NOT EXISTS idx_{table_name}_tariff ON {table_name}(tariff);
"""
