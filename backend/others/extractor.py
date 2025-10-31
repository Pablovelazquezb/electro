import os
from egauge import webapi
from datetime import datetime
import traceback
from typing import Dict, Any

def extract_month_data(url: str, user: str, password: str, year: int, month: int) -> Dict[str, Any]:
    """
    Extracts data from first day/hour to last day/hour of specified month.
    Uses the proven method from original script.
    """
    from calendar import monthrange
    
    # Calculate first and last day of month
    last_day = monthrange(year, month)[1]
    
    start_date = datetime(year, month, 1, 0, 0, 0)
    end_date = datetime(year, month, last_day, 23, 0, 0)
    
    # Timestamps
    start_ts = int(start_date.timestamp())
    end_ts = int(end_date.timestamp())
    delta = 3600  # 1 hour
    time_param = f"{start_ts}:{delta}:{end_ts}"
    
    alias = url.split('/')[-1] if url.endswith('/') else url.split('/')[-1].split('.')[0]
    
    print(f"\n{'#'*80}")
    print(f"[{alias}] Extracting data: {start_date} to {end_date}")
    print(f"{'#'*80}")
    
    # 1. Connection and Authentication
    try:
        dev = webapi.device.Device(url, webapi.JWTAuth(user, password))
        rights = dev.get("/auth/rights").get("rights", [])
        print(f" ✓ Connected with user: {user}, Permissions: {rights}")
    except webapi.Error as e:
        print(f" ❌ Connection ERROR: {e}")
        return {"error": str(e), "url": url, "alias": alias}
    
    # 2. Data Retrieval
    try:
        delta_hours = delta // 3600
        print(f" ... Requesting data in {delta_hours} hour intervals")
        
        ret = webapi.device.Register(dev, {"time": time_param})
        rows = list(ret)
        total_intervals = len(rows) - 1
        
        print(f" ✓ Rows obtained: {len(rows)}, Intervals: {total_intervals}")
        
        if total_intervals == 0:
            return {"error": "Insufficient data", "url": url, "alias": alias}
        
    except Exception as e:
        print(f" ❌ Data retrieval ERROR: {e}")
        traceback.print_exc()
        return {"error": str(e), "url": url, "alias": alias}
    
    # 3. Data Processing
    processed_data = []
    
    try:
        # Get register names
        headers = ["Date", "Time", "Timestamp"]
        for regname in ret.regs:
            headers.append(f"{regname}")
        
        # Process each interval
        for i in range(len(rows)-1):
            delta_row = rows[i] - rows[i+1]
            timestamp = datetime.fromtimestamp(float(rows[i+1].ts))
            
            row_data = {
                "date": timestamp.strftime("%Y-%m-%d"),
                "time": timestamp.strftime("%H:%M:%S"),
                "timestamp": float(rows[i+1].ts)
            }
            
            for regname in ret.regs:
                accu = delta_row.pq_accu(regname)
                row_data[regname] = float(accu.value) if accu else 0
            
            processed_data.append(row_data)
        
        # 4. Period Summary
        delta_total = rows[0] - rows[-1]
        first_time = datetime.fromtimestamp(float(rows[-1].ts))
        last_time = datetime.fromtimestamp(float(rows[0].ts))
        
        summary = {}
        for regname in delta_total.regs:
            accu = delta_total.pq_accu(regname)
            if accu:
                summary[regname] = {
                    "value": float(accu.value),
                    "unit": accu.unit
                }
        
        print(f" ✓ Successful extraction: {total_intervals} intervals")
        
        return {
            "url": url,
            "alias": alias,
            "period": {
                "start": first_time.isoformat(),
                "end": last_time.isoformat()
            },
            "headers": headers,
            "data": processed_data,
            "summary": summary,
            "total_intervals": total_intervals
        }
        
    except Exception as e:
        print(f" ❌ Data processing ERROR: {e}")
        traceback.print_exc()
        return {"error": str(e), "url": url, "alias": alias}
