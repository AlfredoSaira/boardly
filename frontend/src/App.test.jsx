import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import * as api from './api'

vi.mock('./api', async (importOriginal) => ({
  ...(await importOriginal()),
  getBoard: vi.fn(),
  createCard: vi.fn(),
  updateCard: vi.fn(),
  moveCard: vi.fn(),
  deleteCard: vi.fn(),
}))

const COLUMNS = [
  { id: 'new', title: 'New' },
  { id: 'todo', title: 'To Do' },
  { id: 'in_progress', title: 'In Progress' },
  { id: 'done', title: 'Done' },
]

beforeEach(() => {
  vi.resetAllMocks()
})

describe('App', () => {
  it('renders the four columns and the cards from the backend', async () => {
    api.getBoard.mockResolvedValue({
      columns: COLUMNS,
      cards: [{ id: '1', title: 'Write specs', description: '', column: 'todo' }],
    })
    render(<App />)

    expect(await screen.findByText('Write specs')).toBeInTheDocument()
    for (const column of COLUMNS) {
      expect(screen.getAllByText(column.title).length).toBeGreaterThan(0)
    }
  })

  it('shows a clear error when the backend is unreachable', async () => {
    api.getBoard.mockRejectedValue(new Error('API error 502 on /board'))
    render(<App />)
    expect(await screen.findByText("Can't reach the backend")).toBeInTheDocument()
  })

  it('creates a card through the modal and shows it on the board', async () => {
    const user = userEvent.setup()
    api.getBoard.mockResolvedValue({ columns: COLUMNS, cards: [] })
    api.createCard.mockResolvedValue({ id: '9', title: 'New idea', description: '', column: 'new' })
    render(<App />)

    const addButtons = await screen.findAllByRole('button', { name: /add/i })
    await user.click(addButtons[0])
    await user.type(screen.getByLabelText('Title'), '  New idea  ')
    await user.click(screen.getByRole('button', { name: 'Save' }))

    expect(api.createCard).toHaveBeenCalledWith({ title: 'New idea', description: '', column: 'new' })
    expect(await screen.findByText('New idea')).toBeInTheDocument()
  })

  it('puts a card back and warns the user when a delete fails', async () => {
    const user = userEvent.setup()
    api.getBoard.mockResolvedValue({
      columns: COLUMNS,
      cards: [{ id: '1', title: 'Keep me', description: '', column: 'new' }],
    })
    api.deleteCard.mockRejectedValue(new Error('API error 500'))
    render(<App />)

    const card = (await screen.findByText('Keep me')).closest('.card')
    await user.click(within(card).getByRole('button', { name: 'Delete card' }))

    expect(await screen.findByText(/Couldn't delete the card/)).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Keep me')).toBeInTheDocument())
  })
})
