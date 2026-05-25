import { useAuth } from '../context/AuthContext'
import styles from './Page.module.css'

/** Home application — platform overview. Expanded in Phase 1. */
export default function Home() {
  const { user } = useAuth()

  return (
    <div className={styles.page}>
      <h1>Welcome, {user?.email}</h1>
      <p className={styles.sub}>AI-Doc platform — Phase 1 foundations</p>
    </div>
  )
}
