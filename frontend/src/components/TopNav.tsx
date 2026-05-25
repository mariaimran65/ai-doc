import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { APP_REGISTRY } from '../registry'
import styles from './TopNav.module.css'

/**
 * Top navigation bar generated from APP_REGISTRY. Highlights the active app
 * and renders the signed-in user's email with a logout button.
 */
export default function TopNav() {
  const { user, logout } = useAuth()

  return (
    <nav className={styles.nav}>
      <div className={styles.apps}>
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
      <div className={styles.user}>
        <span>{user?.email}</span>
        <button onClick={logout} className={styles.logout}>Sign out</button>
      </div>
    </nav>
  )
}
