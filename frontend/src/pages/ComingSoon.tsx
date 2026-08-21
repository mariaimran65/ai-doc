import { IconLock } from '@tabler/icons-react'
import styles from './ComingSoon.module.css'

interface Props {
  phase: number
  name: string
  description: string
}

export default function ComingSoon({ phase, name, description }: Props) {
  return (
    <div className={styles.page}>
      <div className={styles.lockWrap}>
        <IconLock size={28} />
      </div>
      <p className={styles.title}>{name}</p>
      <p className={styles.desc}>{description}</p>
      <span className={styles.badge}>Phase {phase} · Upcoming</span>
    </div>
  )
}
