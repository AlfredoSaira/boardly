import { useState } from 'react'

export default function CardModal({ initialTitle = '', initialDescription = '', onSave, onCancel }) {
  const [title, setTitle] = useState(initialTitle)
  const [description, setDescription] = useState(initialDescription)

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = title.trim()
    if (!trimmed) return
    onSave({ title: trimmed, description: description.trim() })
  }

  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h3>{initialTitle ? 'Edit card' : 'New card'}</h3>

        <label htmlFor="card-title">Title</label>
        <input
          id="card-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          autoFocus
          required
        />

        <label htmlFor="card-description">Description (optional)</label>
        <textarea
          id="card-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
        />

        <div className="modal__actions">
          <button type="button" onClick={onCancel}>
            Cancel
          </button>
          <button type="submit" className="modal__save">
            Save
          </button>
        </div>
      </form>
    </div>
  )
}
