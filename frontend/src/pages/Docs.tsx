import styles from './Page.module.css'

/** Docs application — architecture, decisions, runbook, API reference.
 *  Sub-pages and content added through Phase 1. */
export default function Docs() {
  return (
    <div className={styles.page}>
      <h1>Docs</h1>
      <p className={styles.sub}>Architecture, decisions, runbook, and API reference.</p>
    </div>
  )
}
