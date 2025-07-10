import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [incidents, setIncidents] = useState([]);
  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedIncident, setSelectedIncident] = useState(null);
  
  // Form states
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ username: '', email: '', password: '' });
  const [incidentForm, setIncidentForm] = useState({
    title: '',
    description: '',
    type: 'acidente',
    location: '',
    people_involved: '',
    severity: 'baixa'
  });
  const [isLogin, setIsLogin] = useState(true);

  // Initialize axios interceptor
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

  // Check if user is logged in
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const response = await axios.get(`${API_URL}/api/me`);
          setUser(response.data);
          await loadIncidents();
        } catch (error) {
          localStorage.removeItem('token');
          delete axios.defaults.headers.common['Authorization'];
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const loadIncidents = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/incidents`);
      setIncidents(response.data);
    } catch (error) {
      console.error('Error loading incidents:', error);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API_URL}/api/login`, loginForm);
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      await loadIncidents();
      setLoginForm({ username: '', password: '' });
    } catch (error) {
      alert('Erro no login: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API_URL}/api/register`, registerForm);
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      await loadIncidents();
      setRegisterForm({ username: '', email: '', password: '' });
    } catch (error) {
      alert('Erro no registro: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    setIncidents([]);
    setCurrentView('dashboard');
  };

  const handleCreateIncident = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/api/incidents`, incidentForm);
      await loadIncidents();
      setIncidentForm({
        title: '',
        description: '',
        type: 'acidente',
        location: '',
        people_involved: '',
        severity: 'baixa'
      });
      setCurrentView('dashboard');
      alert('Ocorrência registrada com sucesso!');
    } catch (error) {
      alert('Erro ao registrar ocorrência: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleUpdateStatus = async (incidentId, newStatus) => {
    try {
      await axios.put(`${API_URL}/api/incidents/${incidentId}/status`, { status: newStatus });
      await loadIncidents();
      alert('Status atualizado com sucesso!');
    } catch (error) {
      alert('Erro ao atualizar status: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('pt-BR');
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'nova': return 'bg-blue-100 text-blue-800';
      case 'em_andamento': return 'bg-yellow-100 text-yellow-800';
      case 'resolvida': return 'bg-green-100 text-green-800';
      case 'cancelada': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'nova': return 'Nova';
      case 'em_andamento': return 'Em Andamento';
      case 'resolvida': return 'Resolvida';
      case 'cancelada': return 'Cancelada';
      default: return status;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
              VB Soluções
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Livro de Ocorrência Online
            </p>
          </div>

          <div className="bg-white py-8 px-6 shadow rounded-lg">
            <div className="flex mb-4">
              <button
                onClick={() => setIsLogin(true)}
                className={`flex-1 py-2 px-4 text-center rounded-l-lg ${
                  isLogin ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
                }`}
              >
                Login
              </button>
              <button
                onClick={() => setIsLogin(false)}
                className={`flex-1 py-2 px-4 text-center rounded-r-lg ${
                  !isLogin ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
                }`}
              >
                Registrar
              </button>
            </div>

            {isLogin ? (
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Usuário
                  </label>
                  <input
                    type="text"
                    required
                    value={loginForm.username}
                    onChange={(e) => setLoginForm({...loginForm, username: e.target.value})}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Senha
                  </label>
                  <input
                    type="password"
                    required
                    value={loginForm.password}
                    onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Entrar
                </button>
              </form>
            ) : (
              <form onSubmit={handleRegister} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Usuário
                  </label>
                  <input
                    type="text"
                    required
                    value={registerForm.username}
                    onChange={(e) => setRegisterForm({...registerForm, username: e.target.value})}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Email
                  </label>
                  <input
                    type="email"
                    required
                    value={registerForm.email}
                    onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Senha
                  </label>
                  <input
                    type="password"
                    required
                    value={registerForm.password}
                    onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Registrar
                </button>
              </form>
            )}

            <div className="mt-6 p-4 bg-gray-50 rounded-md">
              <p className="text-sm text-gray-600 text-center">
                <strong>Conta de Teste:</strong><br />
                Usuário: admin | Senha: admin123
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">VB Soluções</h1>
              <span className="ml-2 text-sm text-gray-500">Livro de Ocorrência Online</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                {user.username} ({user.role === 'admin' ? 'Administrador' : 'Usuário'})
              </span>
              <button
                onClick={handleLogout}
                className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
              >
                Sair
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-blue-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setCurrentView('dashboard')}
              className={`py-4 px-3 border-b-2 text-sm font-medium ${
                currentView === 'dashboard' 
                  ? 'border-white text-white' 
                  : 'border-transparent text-blue-100 hover:text-white hover:border-blue-300'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setCurrentView('create')}
              className={`py-4 px-3 border-b-2 text-sm font-medium ${
                currentView === 'create' 
                  ? 'border-white text-white' 
                  : 'border-transparent text-blue-100 hover:text-white hover:border-blue-300'
              }`}
            >
              Nova Ocorrência
            </button>
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {currentView === 'dashboard' && (
          <div className="px-4 py-6 sm:px-0">
            <div className="mb-6">
              <h2 className="text-lg font-medium text-gray-900">
                {user.role === 'admin' ? 'Todas as Ocorrências' : 'Minhas Ocorrências'}
              </h2>
              <p className="text-sm text-gray-600">
                {incidents.length} ocorrência(s) encontrada(s)
              </p>
            </div>

            {incidents.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500">Nenhuma ocorrência encontrada.</p>
                <button
                  onClick={() => setCurrentView('create')}
                  className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  Registrar Nova Ocorrência
                </button>
              </div>
            ) : (
              <div className="bg-white shadow overflow-hidden sm:rounded-md">
                <ul className="divide-y divide-gray-200">
                  {incidents.map((incident) => (
                    <li key={incident.id} className="px-6 py-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <h3 className="text-lg font-medium text-gray-900 truncate">
                              {incident.title}
                            </h3>
                            <div className="flex items-center space-x-2">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(incident.status)}`}>
                                {getStatusText(incident.status)}
                              </span>
                              <span className="text-sm text-gray-500">
                                {incident.severity === 'baixa' ? 'Baixa' : 
                                 incident.severity === 'media' ? 'Média' : 'Alta'}
                              </span>
                            </div>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">
                            {incident.description.length > 100 
                              ? `${incident.description.substring(0, 100)}...` 
                              : incident.description}
                          </p>
                          <div className="mt-2 flex items-center text-sm text-gray-500">
                            <span className="mr-4">
                              Tipo: {incident.type}
                            </span>
                            <span className="mr-4">
                              Apartamento: {incident.location}
                            </span>
                            <span className="mr-4">
                              Bloco: {incident.people_involved}
                            </span>
                            <span>
                              {formatDate(incident.created_at)}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => setSelectedIncident(incident)}
                            className="text-blue-600 hover:text-blue-800 text-sm"
                          >
                            Ver Detalhes
                          </button>
                          {user.role === 'admin' && (
                            <div className="flex space-x-1">
                              <button
                                onClick={() => handleUpdateStatus(incident.id, 'em_andamento')}
                                className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded hover:bg-yellow-200"
                              >
                                Em Andamento
                              </button>
                              <button
                                onClick={() => handleUpdateStatus(incident.id, 'resolvida')}
                                className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded hover:bg-green-200"
                              >
                                Resolver
                              </button>
                              <button
                                onClick={() => handleUpdateStatus(incident.id, 'cancelada')}
                                className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded hover:bg-red-200"
                              >
                                Cancelar
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {currentView === 'create' && (
          <div className="px-4 py-6 sm:px-0">
            <div className="mb-6">
              <h2 className="text-lg font-medium text-gray-900">Nova Ocorrência</h2>
              <p className="text-sm text-gray-600">Registre uma nova ocorrência no sistema</p>
            </div>

            <div className="bg-white shadow sm:rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <form onSubmit={handleCreateIncident} className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Título da Ocorrência
                    </label>
                    <input
                      type="text"
                      required
                      value={incidentForm.title}
                      onChange={(e) => setIncidentForm({...incidentForm, title: e.target.value})}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Descrição Detalhada
                    </label>
                    <textarea
                      rows={4}
                      required
                      value={incidentForm.description}
                      onChange={(e) => setIncidentForm({...incidentForm, description: e.target.value})}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Tipo de Ocorrência
                      </label>
                      <select
                        value={incidentForm.type}
                        onChange={(e) => setIncidentForm({...incidentForm, type: e.target.value})}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="acidente">Acidente</option>
                        <option value="incidente">Incidente</option>
                        <option value="manutencao">Manutenção</option>
                        <option value="seguranca">Segurança</option>
                        <option value="outros">Outros</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Gravidade
                      </label>
                      <select
                        value={incidentForm.severity}
                        onChange={(e) => setIncidentForm({...incidentForm, severity: e.target.value})}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="baixa">Baixa</option>
                        <option value="media">Média</option>
                        <option value="alta">Alta</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Local da Ocorrência
                    </label>
                    <input
                      type="text"
                      required
                      value={incidentForm.location}
                      onChange={(e) => setIncidentForm({...incidentForm, location: e.target.value})}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Pessoas Envolvidas
                    </label>
                    <textarea
                      rows={3}
                      value={incidentForm.people_involved}
                      onChange={(e) => setIncidentForm({...incidentForm, people_involved: e.target.value})}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Descreva as pessoas envolvidas na ocorrência"
                    />
                  </div>

                  <div className="flex justify-end space-x-3">
                    <button
                      type="button"
                      onClick={() => setCurrentView('dashboard')}
                      className="py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      className="py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Registrar Ocorrência
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Incident Details Modal */}
      {selectedIncident && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Detalhes da Ocorrência
              </h3>
              <button
                onClick={() => setSelectedIncident(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-xl font-semibold text-gray-900">
                  {selectedIncident.title}
                </h4>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(selectedIncident.status)}`}>
                    {getStatusText(selectedIncident.status)}
                  </span>
                  <span className="text-sm text-gray-500">
                    {selectedIncident.severity === 'baixa' ? 'Baixa' : 
                     selectedIncident.severity === 'media' ? 'Média' : 'Alta'}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Tipo</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedIncident.type}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Local</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedIncident.location}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Registrado por</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedIncident.created_by_username}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Data de Criação</label>
                  <p className="mt-1 text-sm text-gray-900">{formatDate(selectedIncident.created_at)}</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Descrição</label>
                <p className="mt-1 text-sm text-gray-900">{selectedIncident.description}</p>
              </div>

              {selectedIncident.people_involved && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Pessoas Envolvidas</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedIncident.people_involved}</p>
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  onClick={() => setSelectedIncident(null)}
                  className="py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Fechar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;