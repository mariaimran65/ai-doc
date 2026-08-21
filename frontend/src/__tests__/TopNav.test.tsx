/**
 * Tests for TopNav — verifies the nav renders every entry in APP_REGISTRY.
 */
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import TopNav from '../components/TopNav'
import { APP_REGISTRY } from '../registry'

// Stub useAuth so TopNav renders without a real AuthContext provider
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ user: { email: 'test@example.com' }, logout: vi.fn() }),
}))

describe('TopNav', () => {
  it('renders a nav link for every app in APP_REGISTRY', () => {
    render(
      <MemoryRouter>
        <TopNav />
      </MemoryRouter>,
    )

    APP_REGISTRY.forEach(app => {
      expect(screen.getByText(app.name)).toBeInTheDocument()
    })
  })
})
