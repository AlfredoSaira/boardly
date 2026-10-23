import { describe, expect, it } from 'vitest'
import { formatSprintRange, getCurrentSprint } from './sprint'

describe('getCurrentSprint', () => {
  it('starts sprint 1 on January 1st', () => {
    const sprint = getCurrentSprint(new Date(2026, 0, 1))
    expect(sprint.number).toBe(1)
    expect(sprint.start).toEqual(new Date(2026, 0, 1))
    expect(sprint.end).toEqual(new Date(2026, 0, 14))
  })

  it('moves to the next sprint every 14 days', () => {
    expect(getCurrentSprint(new Date(2026, 0, 14)).number).toBe(1)
    expect(getCurrentSprint(new Date(2026, 0, 15)).number).toBe(2)
  })

  it('formats the sprint range for the summary bar', () => {
    expect(formatSprintRange(getCurrentSprint(new Date(2026, 0, 1)))).toBe('Jan 1 – Jan 14, 2026')
  })
})
