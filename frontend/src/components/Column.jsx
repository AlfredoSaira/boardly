import { useDroppable } from '@dnd-kit/core'
import Card from './Card'

export default function Column({ column, cards, onAddCard, onEditCard, onDeleteCard }) {
  const { setNodeRef, isOver } = useDroppable({ id: column.id })

  return (
    <div className={`column${isOver ? ' column--over' : ''}`}>
      <div className="column__header">
        <h2>{column.title}</h2>
        <span className="column__count">{cards.length}</span>
      </div>

      <div ref={setNodeRef} className="column__cards">
        {cards.map((card) => (
          <Card key={card.id} card={card} onEdit={onEditCard} onDelete={onDeleteCard} />
        ))}
      </div>

      <button type="button" className="column__add" onClick={() => onAddCard(column.id)}>
        + Add card
      </button>
    </div>
  )
}
