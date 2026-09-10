import assert from 'node:assert/strict'
import test from 'node:test'
import { groupCompanies } from './cockpit-model.ts'

test('groups only surfaced inputs by stable company id and attaches the latest supplied trajectory', () => {
  const trajectory = { company_id: 'company-a', capability: 'COMPANY_TRAJECTORY', marker: 'latest' }
  const groups = groupCompanies([
    { company_id: 'company-b', company: { display_name: 'Beta' }, role: 'One' },
    { company_id: 'company-a', company: { display_name: 'Alpha' }, role: 'Two' },
    { company_id: 'company-a', company: { display_name: 'Alpha' }, role: 'Three' },
    { company_id: null, company: null, role: 'Unresolved' },
  ], [
    trajectory,
    { company_id: 'company-b', capability: 'CORE_X', marker: 'wrong capability' },
  ])

  assert.deepEqual(groups.map((group) => [group.id, group.opportunities.length]), [
    ['company-a', 2],
    ['company-b', 1],
  ])
  assert.equal(groups[0].trajectory, trajectory)
  assert.equal(groups[1].trajectory, null)
})
