import { Link } from 'react-router-dom'
import {
  IconHome2,
  IconBook2,
  IconMessageChatbot,
  IconRobot,
  IconDatabase,
  IconChartBar,
  IconLock,
} from '@tabler/icons-react'
import { useAuth } from '../context/AuthContext'
import { APP_REGISTRY, type AppEntry } from '../registry'
import styles from './Home.module.css'

const ICONS: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  Home: IconHome2,
  Docs: IconBook2,
  Chat: IconMessageChatbot,
  Agents: IconRobot,
  Knowledge: IconDatabase,
  Metrics: IconChartBar,
}

function AppCard({ app }: { app: AppEntry }) {
  const Icon = ICONS[app.name] ?? IconHome2
  const locked = !app.live

  const inner = (
    <>
      {locked && <IconLock size={14} className={styles.lockIcon} />}
      <div className={`${styles.icon} ${locked ? styles.iconLocked : ''}`}>
        <Icon size={22} />
      </div>
      <p className={styles.cardName}>{app.name}</p>
      <p className={styles.cardDesc}>{app.description}</p>
      <span className={`${styles.badge} ${locked ? styles.badgeLocked : styles.badgeLive}`}>
        Phase {app.phase} · {locked ? 'Upcoming' : 'Live'}
      </span>
    </>
  )

  if (locked) {
    return <div className={`${styles.card} ${styles.cardLocked}`}>{inner}</div>
  }
  return <Link to={app.path} className={styles.card}>{inner}</Link>
}

export default function Home() {
  const { user } = useAuth()
  const email = user?.email ?? ''
  const displayName = email.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())

  return (
    <div className={styles.page}>
      <p className={styles.eyebrow}>Welcome back</p>
      <p className={styles.name}>{displayName}</p>
      <p className={styles.sub}>{email}</p>
      <div className={styles.grid}>
        {APP_REGISTRY.map(app => (
          <AppCard key={app.path} app={app} />
        ))}
      </div>
    </div>
  )
}
