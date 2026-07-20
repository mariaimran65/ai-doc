import { useRef, useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import {
  IconSparkles,
  IconHome2,
  IconBook2,
  IconMessageChatbot,
  IconRobot,
  IconDatabase,
  IconChartBar,
  IconLogout,
  IconChevronDown,
} from '@tabler/icons-react'
import { useAuth } from '../context/AuthContext'
import { APP_REGISTRY } from '../registry'
import styles from './Sidebar.module.css'

const ICONS: Record<string, React.ComponentType<{ size?: number }>> = {
  Home: IconHome2,
  Docs: IconBook2,
  Chat: IconMessageChatbot,
  Agents: IconRobot,
  Knowledge: IconDatabase,
  Metrics: IconChartBar,
}

function initials(email: string): string {
  return email.split('@')[0].slice(0, 2).toUpperCase()
}

function displayName(email: string): string {
  return email
    .split('@')[0]
    .replace(/[._]/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

export default function Sidebar() {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <aside className={styles.sidebar}>
      {/* Brand */}
      <div className={styles.brand}>
        <div className={styles.brandIcon}>
          <IconSparkles size={15} />
        </div>
        <span className={styles.brandName}>AI-Doc</span>
      </div>

      {/* Navigation */}
      <nav className={styles.nav}>
        <p className={styles.navLabel}>Platform</p>
        {APP_REGISTRY.map(app => {
          const Icon = ICONS[app.name] ?? IconHome2
          return (
            <NavLink
              key={app.path}
              to={app.path}
              end={app.path === '/'}
              className={({ isActive }) =>
                isActive ? `${styles.link} ${styles.linkActive}` : styles.link
              }
            >
              <Icon size={15} />
              <span className={styles.linkText}>{app.name}</span>
              <span className={styles.phaseBadge}>P{app.phase}</span>
            </NavLink>
          )
        })}
      </nav>

      {/* User section */}
      <div className={styles.bottom} ref={menuRef}>
        <button
          className={styles.userBtn}
          onClick={() => setMenuOpen(v => !v)}
          aria-label="User menu"
        >
          <div className={styles.avatar}>
            {user ? initials(user.email) : '?'}
          </div>
          <div className={styles.userInfo}>
            <p className={styles.userName}>{user ? displayName(user.email) : ''}</p>
            <p className={styles.userEmail}>{user?.email}</p>
          </div>
          <IconChevronDown size={13} className={`${styles.chevron} ${menuOpen ? styles.chevronOpen : ''}`} />
        </button>

        {menuOpen && (
          <div className={styles.userMenu}>
            <button className={styles.signOutBtn} onClick={logout}>
              <IconLogout size={13} />
              Sign out
            </button>
          </div>
        )}
      </div>
    </aside>
  )
}
