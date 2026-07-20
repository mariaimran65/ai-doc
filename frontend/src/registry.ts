export type AppEntry = {
  name: string
  path: string
  phase: number
  description: string
  live: boolean
}

export const APP_REGISTRY: AppEntry[] = [
  {
    name: 'Home',
    path: '/',
    phase: 1,
    description: 'Platform overview and quick access to all applications.',
    live: true,
  },
  {
    name: 'Docs',
    path: '/docs',
    phase: 1,
    description: 'Architecture decisions, runbook, and API reference.',
    live: true,
  },
  {
    name: 'Chat',
    path: '/chat',
    phase: 2,
    description: 'LangChain-powered chatbot with tool use and memory.',
    live: true,
  },
  {
    name: 'Agents',
    path: '/agents',
    phase: 3,
    description: 'LangGraph multi-agent system with supervisor pattern.',
    live: true,
  },
  {
    name: 'Knowledge',
    path: '/knowledge',
    phase: 4,
    description: 'RAG pipeline with pgvector embeddings and retrieval.',
    live: true,
  },
]
