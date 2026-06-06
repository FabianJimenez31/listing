import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { HelmetProvider } from 'react-helmet-async'
import { AuthProvider } from './contexts/AuthContext'
import Layout from './components/layout/Layout'

// Pages — public
import HomePage from './pages/HomePage'
import SearchPage from './pages/SearchPage'
import PropertyDetailPage from './pages/PropertyDetailPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'

// Pages — agent panel
import AgentDashboard from './pages/agent/AgentDashboard'
import PropertyFormPage from './pages/agent/PropertyFormPage'
import LeadsPage from './pages/agent/LeadsPage'

// Pages — admin panel
import AdminDashboard from './pages/admin/AdminDashboard'
import ModerationPage from './pages/admin/ModerationPage'

function NotFound() {
  return (
    <div style={{ textAlign: 'center', padding: '4rem' }}>
      <h1 style={{ fontSize: 48, color: '#e94560' }}>404</h1>
      <p style={{ color: '#666' }}>Página no encontrada</p>
    </div>
  )
}

export default function App() {
  return (
    <HelmetProvider>
      <AuthProvider>
        <BrowserRouter>
          <Layout>
            <Routes>
              {/* Public */}
              <Route path="/" element={<HomePage />} />
              <Route path="/propiedades" element={<SearchPage />} />
              <Route path="/propiedades/:slug" element={<PropertyDetailPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/registro" element={<RegisterPage />} />

              {/* Agent panel */}
              <Route path="/agente" element={<AgentDashboard />} />
              <Route path="/agente/nueva" element={<PropertyFormPage />} />
              <Route path="/agente/editar/:id" element={<PropertyFormPage />} />
              <Route path="/agente/leads" element={<LeadsPage />} />

              {/* Admin panel */}
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/admin/moderacion" element={<ModerationPage />} />

              {/* Fallback */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </AuthProvider>
    </HelmetProvider>
  )
}
