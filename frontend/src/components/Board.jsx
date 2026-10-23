import { DndContext } from '@dnd-kit/core'
import Column from './Column'

export default function Board({ columns, cards, onDragEnd, onAddCard, onEditCard, onDeleteCard }) {
  return (
    <DndContext onDragEnd={onDragEnd}>
      <div className="board">
        {columns.map((column) => (
          <Column
            key={column.id}
            column={column}
            cards={cards.filter((c) => c.column === column.id)}
            onAddCard={onAddCard}
            onEditCard={onEditCard}
            onDeleteCard={onDeleteCard}
          />
        ))}
      </div>
    </DndContext>
  )
}
