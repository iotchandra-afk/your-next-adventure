import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const app = await readFile(new URL('./App.tsx', import.meta.url), 'utf8')

test('every required cockpit surface is wired to an in-context drill-down', () => {
  for (const target of [
    "onDrill('tier_1'",
    "onDrill('tier_2'",
    "onDrill('monitor'",
    "onDrill('gray'",
    "['discovered', 'Signals discovered'",
    "['canonical', 'Canonical roles'",
    "['eligible', 'Executive eligible'",
    "['relevant', 'Relevant'",
    "['priority', 'Priority'",
    "onDrill('clear_no'",
    "onDrill('needs_data'",
    'onSource(source)',
    'onCompany(company)',
    'onOpen(event)',
  ]) {
    assert.match(app, new RegExp(target.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))
  }

  for (const drawer of ['OpportunitySetDrawer', 'SourceDrawer', 'CompanyDrawer', 'ActivitySetDrawer', 'ActivityDrawer', 'DecisionDrawer']) {
    assert.match(app, new RegExp(`function ${drawer}\\(`))
  }
})

test('drill-down surfaces preserve keyboard close and explicit failure feedback', () => {
  assert.match(app, /event\.key === 'Escape'/)
  assert.match(app, /previousFocus\?\.focus\(\)/)
  assert.match(app, /closeRef\.current\?\.focus\(\)/)
  assert.match(app, /role="dialog"/)
  assert.match(app, /role="alert"/)
  assert.match(app, /Drill-down unavailable/)
  assert.match(app, /opportunitySet && !detail && !overlayBusy/)
  assert.match(app, /Open posting ↗/)
  assert.match(app, /Open canonical posting ↗/)
  assert.match(app, /Source URL unavailable/)
  assert.match(app, /opportunity_sources\(is_primary,source_record:source_records\(canonical_url\)\)/)
})
