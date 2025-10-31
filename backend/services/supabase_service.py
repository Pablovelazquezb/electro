# backend/services/supabase_service.py
from supabase import create_client, Client
from typing import List, Dict, Any, Optional
from config import Config

class SupabaseService:
    """Service for Supabase database operations"""
    
    def __init__(self):
        self.client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    def get_all_clients(self) -> List[Dict[str, Any]]:
        """Get all clients ordered by creation date"""
        response = self.client.table('clients').select('*').order('created_at', desc=True).execute()
        return response.data
    
    def get_client_by_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get a single client by ID"""
        response = self.client.table('clients').select('*').eq('id', client_id).execute()
        return response.data[0] if response.data else None
    
    def create_client(self, name: str, url: str, data_table: str) -> Dict[str, Any]:
        """Create a new client"""
        response = self.client.table('clients').insert({
            'name': name,
            'url': url,
            'data_table': data_table,
            'columns': None
        }).execute()
        return response.data[0]
    
    def update_client(self, client_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a client"""
        response = self.client.table('clients').update(update_data).eq('id', client_id).execute()
        return response.data[0]
    
    def delete_client(self, client_id: str) -> bool:
        """Delete a client"""
        self.client.table('clients').delete().eq('id', client_id).execute()
        return True
    
    def client_exists(self, name: str = None, data_table: str = None) -> bool:
        """Check if a client with the given name or table exists"""
        query = self.client.table('clients').select('*')
        
        conditions = []
        if name:
            conditions.append(f'name.eq.{name}')
        if data_table:
            conditions.append(f'data_table.eq.{data_table}')
        
        if conditions:
            query = query.or_(','.join(conditions))
            response = query.execute()
            return len(response.data) > 0
        
        return False
    
    def create_dynamic_table(self, table_name: str, columns: List[str]) -> Dict[str, Any]:
        """
        Create a dynamic table in Supabase using RPC function
        
        Args:
            table_name: Name of the table to create
            columns: List of column names (already sanitized)
            
        Returns:
            Dict with success status and message
        """
        try:
            # Build columns SQL string
            columns_sql = ', '.join([f"{col} FLOAT" for col in columns])
            
            print(f"📝 Creating table '{table_name}' with columns: {columns_sql}")
            
            # Call RPC function
            response = self.client.rpc('create_dynamic_table', {
                'p_table_name': table_name,
                'p_columns': columns_sql
            }).execute()
            
            if response.data:
                result = response.data
                if result.get('success'):
                    print(f"✅ Table '{table_name}' created successfully")
                    return {
                        'success': True,
                        'message': f"Table '{table_name}' created successfully"
                    }
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"❌ Failed to create table: {error}")
                    return {
                        'success': False,
                        'error': error
                    }
            else:
                return {
                    'success': False,
                    'error': 'No response from RPC function'
                }
                
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database
        """
        try:
            # Try to select from the table
            self.client.table(table_name).select('id').limit(1).execute()
            return True
        except Exception:
            return False
    
    def insert_data_batch(
        self,
        table_name: str,
        data: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> int:
        """Insert data in batches"""
        records_inserted = 0
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            self.client.table(table_name).upsert(
                batch,
                on_conflict='timestamp_egauge'
            ).execute()
            records_inserted += len(batch)
            print(f"   ✓ Inserted {records_inserted}/{len(data)} records")
        
        return records_inserted
    
    def get_client_data(
        self,
        table_name: str,
        limit: int = 100,
        offset: int = 0,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """Get data from a client's table"""
        query = self.client.table(table_name).select('*')
        
        if start_date:
            query = query.gte('date', start_date)
        if end_date:
            query = query.lte('date', end_date)
        
        query = query.order('timestamp_egauge', desc=True).range(offset, offset + limit - 1)
        
        response = query.execute()
        return response.data
