import { useState, useRef, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { APP_REGISTRY } from '../registry'
import styles from './TopNav.module.css'

function initials(email: string): string {
  const name = email.split('@')[0]
  return name.slice(0, 2).toUpperCase()
}

export default function TopNav() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <nav className={styles.nav}>
      <NavLink to="/" className={styles.logo}>
        <span className={styles.logoDot} />
        AI-Doc
      </NavLink>

      <div className={styles.links}>
        {APP_REGISTRY.map(app => (
          <NavLink
            key={app.path}
            to={app.path}
            end={app.path === '/'}
            className={({ isActive }) =>
              isActive ? `${styles.link} ${styles.active}` : styles.link
            }
          >
            {app.name}
          </NavLink>
        ))}
      </div>

      <div className={styles.right}>
        <div className={styles.avatarMenu} ref={ref}>
          <button
            className={styles.avatar}
            onClick={() => setOpen(v => !v)}
            aria-label="User menu"
          >
            {user ? initials(user.email) : '?'}
          </button>
          {open && (
            <div className={styles.dropdown}>
              <p className={styles.dropdownEmail}>{user?.email}</p>
              <button className={styles.dropdownBtn} onClick={logout}>
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}
