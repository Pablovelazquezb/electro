# backend/routes/clients.py
from flask import Blueprint, request, jsonify
from datetime import datetime
from services.supabase_service import SupabaseService
from utils.sanitizers import sanitize_table_name

clients_bp = Blueprint('clients', __name__)
supabase_service = SupabaseService()


@clients_bp.route('', methods=['GET'])  # Changed from '/' to ''
def get_clients():
    """Get all clients"""
    try:
        clients = supabase_service.get_all_clients()
        return jsonify({
            'success': True,
            'data': clients
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('', methods=['POST'])  # Changed from '/' to ''
def create_client():
    """Create a new client"""
    try:
        data = request.json
        name = data.get('name')
        url = data.get('url')
        
        if not name or not url:
            return jsonify({
                'success': False,
                'error': 'Name and URL are required'
            }), 400
        
        # Generate table name
        data_table = sanitize_table_name(name)
        
        # Check if already exists
        if supabase_service.client_exists(name=name, data_table=data_table):
            return jsonify({
                'success': False,
                'error': 'A client with that name or table already exists'
            }), 400
        
        # Create client
        client = supabase_service.create_client(name, url, data_table)
        
        return jsonify({
            'success': True,
            'data': client,
            'message': f'Client created. Table: {data_table}'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<client_id>', methods=['PUT'])
def update_client(client_id):
    """Update a client"""
    try:
        data = request.json
        update_data = {}
        
        if 'name' in data:
            update_data['name'] = data['name']
        if 'url' in data:
            update_data['url'] = data['url']
        
        if not update_data:
            return jsonify({
                'success': False,
                'error': 'No data to update'
            }), 400
        
        update_data['updated_at'] = datetime.now().isoformat()
        client = supabase_service.update_client(client_id, update_data)
        
        return jsonify({
            'success': True,
            'data': client
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<client_id>', methods=['DELETE'])
def delete_client(client_id):
    """Delete a client"""
    try:
        client = supabase_service.get_client_by_id(client_id)
        
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        supabase_service.delete_client(client_id)
        
        return jsonify({
            'success': True,
            'message': 'Client deleted successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<client_id>/data', methods=['GET'])
def get_client_data(client_id):
    """Get data from a specific client"""
    try:
        client = supabase_service.get_client_by_id(client_id)
        
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        # Query parameters
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        data = supabase_service.get_client_data(
            client['data_table'],
            limit,
            offset,
            start_date,
            end_date
        )
        
        return jsonify({
            'success': True,
            'data': data,
            'client': client['name'],
            'table': client['data_table']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
