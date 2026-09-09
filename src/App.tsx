import { FormEvent, useEffect, useMemo, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import { supabase } from './lib/supabase'

type Page = 'Home' | 'Intake' | 'Opportunities' | 'Companies'
type Summary = {
  discovered: number
  canonical: number
  executive_eligible: number
  clear_no: number
  possible_fit: number
  relevant: number
  tier_1: number
  tier_2: number
  monitor: number
  needs_data: number
}
type Opportunity = {
  id: string
  title: string
  location: string | null
  priority_class: string | null
  current_reason_text: string | null
  current_confidence: number | null
  first_seen_at: string
  company: { display_name: string } | null
}
type Source = {
  id: string
  display_name: string
  source_family: string
  health: string
  last_success_at: string | null
}
type Activity = {
  id: string
  severity: string
  message: string
  created_at: string
}

const emptySummary: Summary = {
  discovered: 0,
  canonical: 0,
  executive_eligible: 0,
  clear_no: 0,
  possible_fit: 0,
  relevant: 0,
  tier_1: 0,
  tier_2: 0,
  monitor: 0,
  needs_data: 0,
}

function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [email, setEmail] = useState('')
  const [authMessage, setAuthMessage] = useState('')
  const [page, setPage] = useState<Page>('Home')
  const [summary, setSummary] = useState<Summary>(emptySummary)
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [activity, setActivity] = useState<Activity[]>([])
  const [grayZoneCount, setGrayZoneCount] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session))
    const { data: listener } = supabase.auth.onAuthStateChange((_event, next) => setSession(next))
    return () => listener.subscription.unsubscribe()
  }, [])

  useEffect(() => {
    if (!session) {
      setLoading(false)
      return
    }
    void refresh()
  }, [session])

  async function refresh() {
    setLoading(true)
    const [summaryResult, oppResult, sourceResult, activityResult, grayResult] = await Promise.all([
      supabase.rpc('intake_summary', { hours_back: 24 }),
      supabase.from('opportunities').select('id,title,location,priority_class,current_reason_text,current_confidence,first_seen_at,company:companies(display_name)').eq('visibility', 'SURFACED').order('first_seen_at', { ascending: false }).limit(50),
      supabase.from('source_registry').select('id,display_name,source_family,health,last_success_at').eq('enabled', true).order('display_name'),
      supabase.from('activity_events').select('id,severity,message,created_at').order('created_at', { ascending: false }).limit(20),
      supabase.from('opportunities').select('id', { count: 'exact', head: true }).eq('visibility', 'GRAY_ZONE'),
    ])

    if (summaryResult.data?.[0]) setSummary(summaryResult.data[0] as Summary)
    setOpportunities((oppResult.data ?? []) as unknown as Opportunity[])
    setSources((sourceResult.data ?? []) as Source[])
    setActivity((activityResult.data ?? []) as Activity[])
    setGrayZoneCount(grayResult.count ?? 0)
    setLoading(false)
  }

  async function sendMagicLink(event: FormEvent) {
    event.preventDefault()
    setAuthMessage('Sending sign-in link...')
    const redirectTo = `${window.location.origin}/your-next-adventure/`
    const { error } = await supabase.auth.signInWithOtp({ email, options: { emailRedirectTo: redirectTo } })
    setAuthMessage(error ? error.message : 'Check your email for the sign-in link.')
  }

  const companies = useMemo(() => {
    const map = new Map<string, number>()
    for (const role of opportunities) {
      const name = role.company?.display_name ?? 'Unknown company'
      map.set(name, (map.get(name) ?? 0) + 1)
    }
    return [...map.entries()].sort((a, b) => b[1] - a[1])
  }, [opportunities])

  if (!session) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <div className="eyebrow">PRIVATE COCKPIT</div>
          <h1>YourNextAdventure</h1>
          <p>Executive opportunity intelligence, screened before it reaches your attention.</p>
          <form onSubmit={sendMagicLink}>
            <label htmlFor="email">Owner email</label>
            <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <button type="submit">Send sign-in link</button>
          </form>
          {authMessage && <p className="muted">{authMessage}</p>}
        </section>
      </main>
    )
  }

  return (
    <div className="shell">
      <header>
        <div>
          <div className="eyebrow">YOURNEXTADVENTURE</div>
          <h1>Opportunity Cockpit</h1>
        </div>
        <div className="header-actions">
          <span className="status-dot" /> Live
          <button className="ghost" onClick={() => void refresh()}>Refresh</button>
          <button className="ghost" onClick={() => void supabase.auth.signOut()}>Sign out</button>
        </div>
      </header>

      <nav>
        {(['Home', 'Intake', 'Opportunities', 'Companies'] as Page[]).map((item) => (
          <button key={item} className={page === item ? 'active' : ''} onClick={() => setPage(item)}>{item}</button>
        ))}
      </nav>

      <div className="workspace">
        <main className="content">
          {loading ? <p className="muted">Loading current state...</p> : null}
          {!loading && page === 'Home' && <Home summary={summary} opportunities={opportunities} grayZoneCount={grayZoneCount} />}
          {!loading && page === 'Intake' && <Intake summary={summary} sources={sources} opportunities={opportunities} grayZoneCount={grayZoneCount} />}
          {!loading && page === 'Opportunities' && <OpportunityList opportunities={opportunities} />}
          {!loading && page === 'Companies' && <CompanyList companies={companies} />}
        </main>
        <ActivityRail activity={activity} />
      </div>
    </div>
  )
}

function Home({ summary, opportunities, grayZoneCount }: { summary: Summary; opportunities: Opportunity[]; grayZoneCount: number }) {
  return (
    <>
      <section className="hero-row">
        <div>
          <div className="eyebrow">WHAT MATTERS NOW</div>
          <h2>{summary.relevant} relevant opportunities surfaced in the last 24 hours</h2>
          <p className="muted">Broad discovery is screened below the glass. Only plausible executive opportunities are surfaced here.</p>
        </div>
        <div className="needs-me"><strong>{summary.needs_data + grayZoneCount}</strong><span>Needs clarification</span></div>
      </section>
      <div className="metric-grid">
        <Metric label="Tier 1" value={summary.tier_1} />
        <Metric label="Tier 2" value={summary.tier_2} />
        <Metric label="Monitor" value={summary.monitor} />
        <Metric label="Gray zone" value={grayZoneCount} />
      </div>
      <section className="panel">
        <div className="panel-title"><h3>Priority opportunities</h3><span>{opportunities.length} visible</span></div>
        <OpportunityRows opportunities={opportunities.slice(0, 8)} />
      </section>
    </>
  )
}

function Intake({ summary, sources, opportunities, grayZoneCount }: { summary: Summary; sources: Source[]; opportunities: Opportunity[]; grayZoneCount: number }) {
  const funnel = [
    ['Signals discovered', summary.discovered],
    ['Canonical roles', summary.canonical],
    ['Executive eligible', summary.executive_eligible],
    ['Relevant', summary.relevant],
    ['Priority', summary.tier_1 + summary.tier_2],
  ] as const
  return (
    <>
      <div className="eyebrow">SCREENING CONTROL</div>
      <h2>Broad discovery. Narrow human attention.</h2>
      <p className="muted">The raw universe remains auditable, but is hidden by default. Hard rejects require high confidence; ambiguous roles remain in the gray zone instead of disappearing.</p>
      <section className="panel funnel">
        {funnel.map(([label, value], index) => <div className="funnel-step" key={label}><span>{label}</span><strong>{value}</strong>{index < funnel.length - 1 && <i>→</i>}</div>)}
      </section>
      <div className="split-grid">
        <section className="panel">
          <div className="panel-title"><h3>Source health</h3><span>{sources.length} enabled</span></div>
          {sources.length === 0 ? <p className="muted">Source adapters have not completed their first run yet.</p> : sources.map((source) => (
            <div className="source-row" key={source.id}><div><strong>{source.display_name}</strong><small>{source.source_family}</small></div><span className={`health ${source.health.toLowerCase()}`}>{source.health}</span></div>
          ))}
        </section>
        <section className="panel">
          <div className="panel-title"><h3>Screening outcomes</h3><span>last 24h</span></div>
          <StatRow label="Clear no, retained but hidden" value={summary.clear_no} />
          <StatRow label="Possible fit / gray zone" value={Math.max(summary.possible_fit, grayZoneCount)} />
          <StatRow label="Relevant and surfaced" value={summary.relevant} />
          <StatRow label="Needs more data" value={summary.needs_data} />
        </section>
      </div>
      <section className="panel">
        <div className="panel-title"><h3>Roles that cleared relevance screening</h3><span>{opportunities.length}</span></div>
        <OpportunityRows opportunities={opportunities} />
      </section>
    </>
  )
}

function OpportunityList({ opportunities }: { opportunities: Opportunity[] }) {
  return <><div className="eyebrow">PURSUIT PORTFOLIO</div><h2>Opportunities</h2><p className="muted">This is not the internet. These roles have already cleared relevance screening.</p><section className="panel"><OpportunityRows opportunities={opportunities} /></section></>
}

function CompanyList({ companies }: { companies: [string, number][] }) {
  return <><div className="eyebrow">AGGREGATION LENS</div><h2>Companies</h2><p className="muted">Shared intelligence compounds across multiple opportunities at the same company.</p><section className="panel">{companies.length === 0 ? <p className="muted">No surfaced company opportunities yet.</p> : companies.map(([name, count]) => <div className="company-row" key={name}><strong>{name}</strong><span>{count} relevant role{count === 1 ? '' : 's'}</span></div>)}</section></>
}

function OpportunityRows({ opportunities }: { opportunities: Opportunity[] }) {
  if (opportunities.length === 0) return <p className="muted">No roles have cleared the relevance gate yet.</p>
  return <div>{opportunities.map((role) => <div className="opportunity-row" key={role.id}><div><div className="role-title">{role.title}</div><div className="role-meta">{role.company?.display_name ?? 'Company pending'}{role.location ? ` · ${role.location}` : ''}</div>{role.current_reason_text && <div className="reason">{role.current_reason_text}</div>}</div><span className={`priority ${(role.priority_class ?? 'needs_data').toLowerCase()}`}>{(role.priority_class ?? 'NEEDS_DATA').replace('_', ' ')}</span></div>)}</div>
}

function ActivityRail({ activity }: { activity: Activity[] }) {
  return <aside><div className="panel-title"><h3>Activity</h3><span>system</span></div>{activity.length === 0 ? <p className="muted">Waiting for first autonomous run.</p> : activity.map((event) => <div className="activity-item" key={event.id}><span className={`activity-mark ${event.severity.toLowerCase()}`} /><div><strong>{event.message}</strong><small>{new Date(event.created_at).toLocaleString()}</small></div></div>)}</aside>
}

function Metric({ label, value }: { label: string; value: number }) { return <div className="metric"><span>{label}</span><strong>{value}</strong></div> }
function StatRow({ label, value }: { label: string; value: number }) { return <div className="stat-row"><span>{label}</span><strong>{value}</strong></div> }

export default App
