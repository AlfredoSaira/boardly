// Sprint numbering: 2-week sprints, Sprint 1 starts Jan 1 of the current
// year. This is a lightweight stand-in for a real sprint/iteration model —
// good enough for a summary header, not meant to survive year boundaries
// with custom start dates.

const SPRINT_LENGTH_DAYS = 14
const MS_PER_DAY = 24 * 60 * 60 * 1000

export function getCurrentSprint(referenceDate = new Date()) {
  const yearStart = new Date(referenceDate.getFullYear(), 0, 1)
  const daysSinceStart = Math.floor((referenceDate - yearStart) / MS_PER_DAY)
  const number = Math.floor(daysSinceStart / SPRINT_LENGTH_DAYS) + 1

  const start = new Date(yearStart)
  start.setDate(start.getDate() + (number - 1) * SPRINT_LENGTH_DAYS)

  const end = new Date(start)
  end.setDate(end.getDate() + SPRINT_LENGTH_DAYS - 1)

  return { number, start, end }
}

const dateFormatter = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' })

export function formatSprintRange({ start, end }) {
  return `${dateFormatter.format(start)} – ${dateFormatter.format(end)}, ${end.getFullYear()}`
}
