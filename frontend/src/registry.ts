/** A registered application in the platform shell. */
export type AppEntry = {
  name: string
  path: string
  phase: number
}

/**
 * Central list of all applications. The top nav and routing are both generated
 * from this array — adding an entry here automatically adds it to both.
 */
export const APP_REGISTRY: AppEntry[] = [
  { name: 'Home', path: '/', phase: 1 },
  { name: 'Docs', path: '/docs', phase: 1 },
  { name: 'Chat', path: '/chat', phase: 2 },
  { name: 'Agents', path: '/agents', phase: 3 },
  { name: 'Knowledge', path: '/knowledge', phase: 4 },
]
