import { useEffect, useState } from 'react'
import * as api from './api'
import { API_BASE_URL } from './api'
import Board from './components/Board'
import CardModal from './components/CardModal'
import SummaryBar from './components/SummaryBar'
import './App.css'

export default function App() {
  const [columns, setColumns] = useState([])
  const [cards, setCards] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)
  const [actionError, setActionError] = useState(null)
  // { mode: 'create', column } | { mode: 'edit', card } | null
  const [modal, setModal] = useState(null)

  useEffect(() => {
    api
      .getBoard()
      .then(({ columns, cards }) => {
        setColumns(columns)
        setCards(cards)
      })
      .catch((err) => setLoadError(err.message))
      .finally(() => setLoading(false))
  }, [])

  function handleDragEnd(event) {
    const { active, over } = event
    if (!over) return
    const cardId = active.id
    const targetColumn = over.id
    const card = cards.find((c) => c.id === cardId)
    if (!card || card.column === targetColumn) return

    const previousColumn = card.column
    setCards((prev) => prev.map((c) => (c.id === cardId ? { ...c, column: targetColumn } : c)))
    api.moveCard(cardId, { column: targetColumn }).catch(() => {
      setCards((prev) => prev.map((c) => (c.id === cardId ? { ...c, column: previousColumn } : c)))
      setActionError("Couldn't move the card — check the backend and try again.")
    })
  }

  function handleAddCard(columnId) {
    setModal({ mode: 'create', column: columnId })
  }

  function handleEditCard(card) {
    setModal({ mode: 'edit', card })
  }

  async function handleDeleteCard(cardId) {
    const removed = cards.find((c) => c.id === cardId)
    setCards((prev) => prev.filter((c) => c.id !== cardId))
    try {
      await api.deleteCard(cardId)
    } catch {
      if (removed) setCards((prev) => [...prev, removed])
      setActionError("Couldn't delete the card — check the backend and try again.")
    }
  }

  async function handleSaveModal({ title, description }) {
    try {
      if (modal.mode === 'create') {
        const created = await api.createCard({ title, description, column: modal.column })
        setCards((prev) => [...prev, created])
      } else {
        const updated = await api.updateCard(modal.card.id, { title, description })
        setCards((prev) => prev.map((c) => (c.id === updated.id ? updated : c)))
      }
      setModal(null)
    } catch {
      setActionError("Couldn't save the card — check the backend and try again.")
    }
  }

  if (loading) {
    return <p className="loading">Loading board…</p>
  }

  if (loadError) {
    return (
      <div className="load-error">
        <h2>Can't reach the backend</h2>
        <p>{loadError}</p>
        <p>
          Make sure it's running at <code>{API_BASE_URL}</code>, then refresh this page.
        </p>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app__header">
        <h1>Boardly</h1>
      </header>

      {actionError && (
        <div className="banner banner--error">
          <span>{actionError}</span>
          <button type="button" onClick={() => setActionError(null)}>
            Dismiss
          </button>
        </div>
      )}

      <SummaryBar columns={columns} cards={cards} />

      <Board
        columns={columns}
        cards={cards}
        onDragEnd={handleDragEnd}
        onAddCard={handleAddCard}
        onEditCard={handleEditCard}
        onDeleteCard={handleDeleteCard}
      />

      {modal && (
        <CardModal
          initialTitle={modal.mode === 'edit' ? modal.card.title : ''}
          initialDescription={modal.mode === 'edit' ? modal.card.description : ''}
          onSave={handleSaveModal}
          onCancel={() => setModal(null)}
        />
      )}
    </div>
  )
}
