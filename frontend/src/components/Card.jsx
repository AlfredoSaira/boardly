import { useDraggable } from '@dnd-kit/core'

export default function Card({ card, onEdit, onDelete }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: card.id,
  })

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        zIndex: 10,
      }
    : undefined

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`card${isDragging ? ' card--dragging' : ''}`}
    >
      <div className="card__drag-handle" {...listeners} {...attributes}>
        <span className="card__title">{card.title}</span>
        {card.description && <p className="card__description">{card.description}</p>}
      </div>
      <div className="card__actions">
        <button type="button" onClick={() => onEdit(card)} aria-label="Edit card">
          Edit
        </button>
        <button type="button" onClick={() => onDelete(card.id)} aria-label="Delete card">
          Delete
        </button>
      </div>
    </div>
  )
}
