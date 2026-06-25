import { BrowserRouter, Outlet, Route, Routes } from 'react-router-dom'
import { HelmetProvider } from 'react-helmet-async'
import { AuthProvider } from './contexts/AuthContext'
import { SettingsProvider } from './contexts/SettingsContext'
import Layout from './components/layout/Layout'
import PanelLayout from './components/panel/PanelLayout'

// Pages — public
import HomePage from './pages/HomePage'
import SearchPage from './pages/SearchPage'
import PropertyDetailPage from './pages/PropertyDetailPage'
import ProjectsPage from './pages/ProjectsPage'
import ProjectDetailPage from './pages/ProjectDetailPage'
import AgenciesPage from './pages/AgenciesPage'
import AgencyDetailPage from './pages/AgencyDetailPage'
import BlogPage from './pages/BlogPage'
import PostPage from './pages/PostPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'

// Pages — agent panel
import AgentDashboard from './pages/agent/AgentDashboard'
import PropertyFormPage from './pages/agent/PropertyFormPage'
import LeadsPage from './pages/agent/LeadsPage'
import AgentProjectsPage from './pages/agent/ProjectsPage'
import ProjectFormPage from './pages/agent/ProjectFormPage'

// Pages — user
import FavoritesPage from './pages/FavoritesPage'

// Pages — admin panel
import AdminDashboard from './pages/admin/AdminDashboard'
import ModerationPage from './pages/admin/ModerationPage'
import BannersPage from './pages/admin/BannersPage'
import UsersPage from './pages/admin/UsersPage'
import FeaturedPage from './pages/admin/FeaturedPage'
import AdminAgenciesPage from './pages/admin/AgenciesPage'
import AdminPartnersPage from './pages/admin/PartnersPage'
import AdminBlogPage from './pages/admin/BlogPage'
import BrandingPage from './pages/admin/BrandingPage'

function NotFound() {
  return (
    <div style={{ textAlign: 'center', padding: '4rem' }}>
      <h1 style={{ fontSize: 48, color: '#e94560' }}>404</h1>
      <p style={{ color: '#666' }}>Página no encontrada</p>
    </div>
  )
}

// Public shell (header + footer) shared by every non-admin route.
function PublicShell() {
  return (
    <Layout>
      <Outlet />
    </Layout>
  )
}

export default function App() {
  return (
    <HelmetProvider>
      <AuthProvider>
        <SettingsProvider>
        <BrowserRouter>
          <Routes>
            {/* Back-office — single sidebar shell for agents & admins.
                Sections inside the sidebar are gated by permission. */}
            <Route element={<PanelLayout />}>
              {/* Agent workspace */}
              <Route path="/agente" element={<AgentDashboard />} />
              <Route path="/agente/nueva" element={<PropertyFormPage />} />
              <Route path="/agente/editar/:id" element={<PropertyFormPage />} />
              <Route path="/agente/leads" element={<LeadsPage />} />
              <Route path="/agente/proyectos" element={<AgentProjectsPage />} />
              <Route path="/agente/proyectos/nuevo" element={<ProjectFormPage />} />
              <Route path="/agente/proyectos/editar/:slug" element={<ProjectFormPage />} />

              {/* Admin area (guarded by role inside PanelLayout) */}
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/admin/moderacion" element={<ModerationPage />} />
              <Route path="/admin/banners" element={<BannersPage />} />
              <Route path="/admin/usuarios" element={<UsersPage />} />
              <Route path="/admin/destacados" element={<FeaturedPage />} />
              <Route path="/admin/inmobiliarias" element={<AdminAgenciesPage />} />
              <Route path="/admin/aliados" element={<AdminPartnersPage />} />
              <Route path="/admin/blog" element={<AdminBlogPage />} />
              <Route path="/admin/marca" element={<BrandingPage />} />
            </Route>

            {/* Public / user — header + footer shell */}
            <Route element={<PublicShell />}>
              {/* Public */}
              <Route path="/" element={<HomePage />} />
              <Route path="/propiedades" element={<SearchPage />} />
              <Route path="/propiedades/:slug" element={<PropertyDetailPage />} />
              <Route
                path="/usa"
                element={<SearchPage forced={{ country: 'us' }} title="Mercado USA" subtitle="Propiedades de inversión en Estados Unidos" />}
              />
              <Route path="/proyectos" element={<ProjectsPage />} />
              <Route path="/proyectos/:slug" element={<ProjectDetailPage />} />
              <Route path="/inmobiliarias" element={<AgenciesPage />} />
              <Route path="/inmobiliarias/:slug" element={<AgencyDetailPage />} />
              <Route path="/blog" element={<BlogPage />} />
              <Route path="/blog/:slug" element={<PostPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/registro" element={<RegisterPage />} />

              {/* User */}
              <Route path="/favoritos" element={<FavoritesPage />} />

              {/* Fallback */}
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </BrowserRouter>
        </SettingsProvider>
      </AuthProvider>
    </HelmetProvider>
  )
}
