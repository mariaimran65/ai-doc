import styles from './Page.module.css'

/** Placeholder rendered for applications not yet built.
 *
 * @param phase - The phase number in which this application is introduced.
 */
export default function ComingSoon({ phase }: { phase: number }) {
  return (
    <div className={styles.page}>
      <h1>Coming in Phase {phase}</h1>
      <p className={styles.sub}>This application is built in Phase {phase} of the programme.</p>
    </div>
  )
}
