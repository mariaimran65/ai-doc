import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import TopNav from './components/TopNav'
import Login from './pages/Login'
import ComingSoon from './pages/ComingSoon'
import { APP_REGISTRY } from './registry'

const Home = lazy(() => import('./pages/Home'))
const Docs = lazy(() => import('./pages/Docs'))
const Chat = lazy(() => import('./pages/Chat'))
const Agents = lazy(() => import('./pages/Agents'))
const Knowledge = lazy(() => import('./pages/Knowledge'))
const Metrics = lazy(() => import('./pages/Metrics'))

function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function Shell() {
  return (
    <AuthGuard>
      <TopNav />
      <main>
        <Suspense fallback={null}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/docs/*" element={<Docs />} />
            <Route path="/chat/*" element={<Chat />} />
            <Route path="/agents/*" element={<Agents />} />
            <Route path="/knowledge/*" element={<Knowledge />} />
            <Route path="/metrics/*" element={<Metrics />} />
            {APP_REGISTRY.filter(a => !a.live && a.path !== '/').map(app => (
              <Route
                key={app.path}
                path={`${app.path}/*`}
                element={<ComingSoon phase={app.phase} name={app.name} description={app.description} />}
              />
            ))}
          </Routes>
        </Suspense>
      </main>
    </AuthGuard>
  )
}

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
