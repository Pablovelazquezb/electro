// src/App.js
import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

const API_BASE = 'http://localhost:5001/api';

function App() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [alerts, setAlerts] = useState([]);
  
  // Form states
  const [newClient, setNewClient] = useState({ name: '', url: '' });
  const [extractModal, setExtractModal] = useState({
    show: false,
    client: null,
    startDate: '',
    endDate: '',
    deltaHours: 1
  });

  // Show alert
  const showAlert = useCallback((message, type = 'success') => {
    const id = Date.now();
    setAlerts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setAlerts(prev => prev.filter(alert => alert.id !== id));
    }, 5001);
  }, []);

  // Load clients - wrapped with useCallback to avoid infinite loops
  const loadClients = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/clients`);
      const result = await response.json();
      
      if (result.success) {
        setClients(result.data);
      } else {
        showAlert(result.error || 'Error loading clients', 'error');
      }
    } catch (error) {
      showAlert('Connection error', 'error');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  }, [showAlert]);

  // Load clients on mount
  useEffect(() => {
    loadClients();
  }, [loadClients]);

  // Add client
  const handleAddClient = async (e) => {
    e.preventDefault();
    
    if (!newClient.name || !newClient.url) {
      showAlert('Name and URL are required', 'error');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/clients`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newClient)
      });

      const result = await response.json();

      if (result.success) {
        showAlert(`Client "${newClient.name}" added successfully`, 'success');
        setNewClient({ name: '', url: '' });
        loadClients();
      } else {
        showAlert(result.error || 'Error adding client', 'error');
      }
    } catch (error) {
      showAlert('Connection error', 'error');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Delete client
  const handleDeleteClient = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete client "${name}"?`)) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/clients/${id}`, {
        method: 'DELETE'
      });

      const result = await response.json();

      if (result.success) {
        showAlert(`Client "${name}" deleted`, 'success');
        loadClients();
      } else {
        showAlert(result.error || 'Error deleting client', 'error');
      }
    } catch (error) {
      showAlert('Connection error', 'error');
      console.error('Error:', error);
    }
  };

  // Open extract modal
  const openExtractModal = (client) => {
    // Set default dates (last month)
    const today = new Date();
    const firstDayLastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    const lastDayLastMonth = new Date(today.getFullYear(), today.getMonth(), 0);
    
    setExtractModal({
      show: true,
      client: client,
      startDate: firstDayLastMonth.toISOString().split('T')[0],
      endDate: lastDayLastMonth.toISOString().split('T')[0],
      deltaHours: 1
    });
  };

  // Close extract modal
  const closeExtractModal = () => {
    setExtractModal({
      show: false,
      client: null,
      startDate: '',
      endDate: '',
      deltaHours: 1
    });
  };

  // Extract data
  const handleExtractData = async (e) => {
    e.preventDefault();

    if (!extractModal.client || !extractModal.startDate || !extractModal.endDate) {
      showAlert('All fields are required', 'error');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/data/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: extractModal.client.id,
          start_date: extractModal.startDate,
          end_date: extractModal.endDate,
          delta_hours: parseInt(extractModal.deltaHours)
        })
      });

      const result = await response.json();

      if (result.success) {
        showAlert(
          `✅ Data extracted: ${result.data.records_inserted} records in table "${result.data.table}"`,
          'success'
        );
        closeExtractModal();
        loadClients();
      } else {
        showAlert(result.error || 'Error extracting data', 'error');
      }
    } catch (error) {
      showAlert('Connection error', 'error');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <div className="container">
        <header>
          <h1>🔌 eGauge Management System</h1>
          <p className="subtitle">Manage your clients and extract energy data</p>
        </header>

        {/* Alerts */}
        <div className="alert-container">
          {alerts.map(alert => (
            <div key={alert.id} className={`alert alert-${alert.type}`}>
              <span>{alert.type === 'success' ? '✓' : '✕'}</span>
              <span>{alert.message}</span>
            </div>
          ))}
        </div>

        {/* Add Client Form */}
        <div className="card">
          <div className="card-header">
            <span>➕ Add New Client</span>
          </div>
          <form onSubmit={handleAddClient}>
            <div className="form-group">
              <label htmlFor="clientName">Client Name *</label>
              <input
                type="text"
                id="clientName"
                placeholder="e.g., Client 1, North Branch, etc."
                value={newClient.name}
                onChange={(e) => setNewClient({...newClient, name: e.target.value})}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="clientUrl">eGauge Device URL *</label>
              <input
                type="url"
                id="clientUrl"
                placeholder="https://egauge90707.egaug.es"
                value={newClient.url}
                onChange={(e) => setNewClient({...newClient, url: e.target.value})}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Adding...' : 'Add Client'}
            </button>
          </form>
        </div>

        {/* Clients List */}
        <div className="card">
          <div className="card-header">
            <span>👥 Registered Clients</span>
            <button className="btn btn-small btn-primary" onClick={loadClients} disabled={loading}>
              🔄 Refresh
            </button>
          </div>
          
          {loading && clients.length === 0 ? (
            <div className="loading-container">
              <div className="loading"></div>
            </div>
          ) : clients.length > 0 ? (
            <div className="clients-list">
              {clients.map(client => (
                <div key={client.id} className="client-item">
                  <div className="client-info">
                    <div className="client-name">{client.name}</div>
                    <div className="client-url">{client.url}</div>
                    <div className="client-table">Table: {client.data_table}</div>
                  </div>
                  <div className="client-actions">
                    <button
                      className="btn btn-small btn-success"
                      onClick={() => openExtractModal(client)}
                    >
                      📊 Extract Data
                    </button>
                    <button
                      className="btn btn-small btn-danger"
                      onClick={() => handleDeleteClient(client.id, client.name)}
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">📭</div>
              <p>No clients registered yet</p>
            </div>
          )}
        </div>

        {/* Extract Data Modal */}
        {extractModal.show && (
          <div className="modal-overlay" onClick={closeExtractModal}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="card">
                <div className="card-header">
                  <span>📊 Extract eGauge Data</span>
                  <button className="btn btn-small btn-danger" onClick={closeExtractModal}>
                    ✕ Close
                  </button>
                </div>
                <form onSubmit={handleExtractData}>
                  <div className="form-group">
                    <label>Client:</label>
                    <p style={{fontWeight: 600}}>{extractModal.client?.name}</p>
                  </div>
                  <div className="grid-2">
                    <div className="form-group">
                      <label htmlFor="startDate">Start Date *</label>
                      <input
                        type="date"
                        id="startDate"
                        value={extractModal.startDate}
                        onChange={(e) => setExtractModal({...extractModal, startDate: e.target.value})}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label htmlFor="endDate">End Date *</label>
                      <input
                        type="date"
                        id="endDate"
                        value={extractModal.endDate}
                        onChange={(e) => setExtractModal({...extractModal, endDate: e.target.value})}
                        required
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label htmlFor="deltaHours">Interval (hours) *</label>
                    <select
                      id="deltaHours"
                      value={extractModal.deltaHours}
                      onChange={(e) => setExtractModal({...extractModal, deltaHours: e.target.value})}
                      required
                    >
                      <option value="1">1 hour</option>
                      <option value="2">2 hours</option>
                      <option value="4">4 hours</option>
                      <option value="6">6 hours</option>
                      <option value="12">12 hours</option>
                      <option value="24">24 hours (1 day)</option>
                    </select>
                  </div>
                  <button type="submit" className="btn btn-success" disabled={loading}>
                    {loading ? 'Extracting...' : 'Extract and Save Data'}
                  </button>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
