import { getCurrentSprint, formatSprintRange } from '../sprint'

export default function SummaryBar({ columns, cards }) {
  const sprint = getCurrentSprint()

  return (
    <div className="summary">
      <div className="summary__sprint">
        <span className="summary__sprint-number">Sprint {sprint.number}</span>
        <span className="summary__sprint-range">{formatSprintRange(sprint)}</span>
      </div>

      <div className="summary__stats">
        {columns.map((column) => (
          <div key={column.id} className="summary__stat">
            <span className="summary__stat-value">
              {cards.filter((c) => c.column === column.id).length}
            </span>
            <span className="summary__stat-label">{column.title}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
