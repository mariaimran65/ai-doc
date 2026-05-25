import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import TopNav from './components/TopNav'
import Login from './pages/Login'

const Home = lazy(() => import('./pages/Home'))
const Docs = lazy(() => import('./pages/Docs'))
const ComingSoon = lazy(() => import('./pages/ComingSoon'))

/**
 * Redirects unauthenticated users to /login. Renders a blank screen while the
 * auth state is being resolved to avoid a flash of the login page.
 */
function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

/**
 * Authenticated shell: top nav + lazy-loaded app routes.
 * Adding an app to APP_REGISTRY automatically adds it to the nav via TopNav.
 */
function Shell() {
  return (
    <AuthGuard>
      <TopNav />
      <main>
        <Suspense fallback={null}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/docs/*" element={<Docs />} />
            <Route path="/chat/*" element={<ComingSoon phase={2} />} />
            <Route path="/agents/*" element={<ComingSoon phase={3} />} />
            <Route path="/knowledge/*" element={<ComingSoon phase={4} />} />
          </Routes>
        </Suspense>
      </main>
    </AuthGuard>
  )
}

/** Root of the application. Provides routing and auth context to the tree. */
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={<Shell />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
