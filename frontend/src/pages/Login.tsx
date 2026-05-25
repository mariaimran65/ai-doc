import styles from './Login.module.css'

/** Sign-in page. Clicking the button navigates the browser to the backend
 *  OAuth login endpoint, which redirects to Google's consent screen. */
export default function Login() {
  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1 className={styles.title}>AI-Doc</h1>
        <p className={styles.sub}>Sign in to continue</p>
        <a href="/api/auth/login" className={styles.button}>
          Sign in with Google
        </a>
      </div>
    </div>
  )
}
