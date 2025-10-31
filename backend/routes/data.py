# backend/routes/data.py
from flask import Blueprint, request, jsonify
from datetime import datetime
import traceback
from services.supabase_service import SupabaseService
from services.egauge_service import EGaugeService
from utils.validators import validate_date_range
from config import Config

data_bp = Blueprint('data', __name__)
supabase_service = SupabaseService()
egauge_service = EGaugeService()


@data_bp.route('/extract', methods=['POST'])
def extract_data():
    """Extract data from eGauge and save to Supabase"""
    try:
        data = request.json
        client_id = data.get('client_id')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        delta_hours = int(data.get('delta_hours', 1))
        
        # Validate required fields
        if not client_id or not start_date_str or not end_date_str:
            return jsonify({
                'success': False,
                'error': 'client_id, start_date and end_date are required'
            }), 400
        
        # Validate dates
        is_valid, error_msg, start_date, end_date = validate_date_range(
            start_date_str,
            end_date_str,
            Config.MAX_DAYS_HISTORY
        )
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Get client
        client = supabase_service.get_client_by_id(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        data_table = client['data_table']
        
        print(f"\n🚀 Starting data extraction for client: {client['name']}")
        print(f"   URL: {client['url']}")
        print(f"   Date range: {start_date_str} to {end_date_str}")
        
        # Extract data from eGauge
        result = egauge_service.extract_data(
            url=client['url'],
            start_date=start_date,
            end_date=end_date,
            delta_hours=delta_hours
        )
        
        if not result['success']:
            return jsonify(result), 400
        
        columns = result['columns']
        sanitized_columns = result['sanitized_columns']
        data_rows = result['data']
        
        # Check if table exists, if not create it
        print(f"\n🔍 Checking if table '{data_table}' exists...")
        
        if not supabase_service.table_exists(data_table):
            print(f"📝 Table doesn't exist. Creating table '{data_table}'...")
            
            # Create the table
            create_result = supabase_service.create_dynamic_table(data_table, sanitized_columns)
            
            if not create_result['success']:
                # Generate SQL for manual creation as fallback
                create_table_sql = egauge_service.generate_table_sql(data_table, sanitized_columns)
                
                return jsonify({
                    'success': False,
                    'error': f"Failed to create table automatically: {create_result.get('error')}",
                    'action_required': 'Please run the SQL below in Supabase SQL Editor',
                    'sql_to_run': create_table_sql,
                    'instructions': [
                        '1. Go to https://app.supabase.com',
                        '2. Select your project',
                        '3. Go to SQL Editor (left sidebar)',
                        '4. Click "New Query"',
                        '5. Copy and paste the SQL provided',
                        '6. Click "Run" or press Cmd/Ctrl + Enter',
                        '7. Try extracting data again'
                    ]
                }), 500
            
            print(f"✅ Table '{data_table}' created successfully!")
        else:
            print(f"✅ Table '{data_table}' already exists")
        
        # Prepare data for insertion
        print(f"\n💾 Preparing {len(data_rows)} records for insertion...")
        
        data_to_insert = []
        for row in data_rows:
            data_to_insert.append({
                'date': row['date'],
                'time': row['time'],
                'timestamp_egauge': row['timestamp'],
                'tariff': row['tariff'],
                **{k: v for k, v in row.items() if k not in ['date', 'time', 'timestamp', 'tariff']}
            })
        
        # Insert data
        try:
            print(f"💾 Inserting into table '{data_table}'...")
            records_inserted = supabase_service.insert_data_batch(
                data_table,
                data_to_insert,
                Config.BATCH_INSERT_SIZE
            )
        except Exception as insert_error:
            error_message = str(insert_error)
            print(f"❌ Error inserting data: {error_message}")
            
            # Generate SQL as fallback
            create_table_sql = egauge_service.generate_table_sql(data_table, sanitized_columns)
            
            return jsonify({
                'success': False,
                'error': f'Error inserting data: {error_message}',
                'sql_to_run': create_table_sql
            }), 500
        
        # Update client columns
        supabase_service.update_client(client_id, {
            'columns': columns,
            'updated_at': datetime.now().isoformat()
        })
        
        print(f"✅ Data extraction completed successfully!\n")
        
        return jsonify({
            'success': True,
            'message': 'Data extracted and inserted successfully',
            'data': {
                'client': client['name'],
                'table': data_table,
                'records_inserted': records_inserted,
                'columns': columns,
                'table_created': not supabase_service.table_exists(data_table),
                'range': f'{start_date_str} to {end_date_str}'
            }
        })
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500
