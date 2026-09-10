import { FormEvent, useEffect, useMemo, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import { supabase } from './lib/supabase'
import { groupCompanies } from './cockpit-model'

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
  company_id: string | null
  title: string
  location: string | null
  priority_class: string | null
  screening_stage: string
  current_reason_code: string | null
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
  last_error: string | null
}
type Activity = {
  id: string
  severity: string
  message: string
  created_at: string
  entity_type: string | null
  entity_id: string | null
}
type DecisionEvidence = {
  mandate_summary?: string
  supporting_factors?: string[]
  constraints?: string[]
  material_unknowns?: string[]
  authority_signals?: string[]
  candidate_path?: string
  candidate_truth_version?: string
  pursuit_policy_version?: string
  sources?: Array<{
    source_family?: string
    source_name?: string
    external_id?: string
    canonical_url?: string
    state?: string
    content_hash?: string
    is_primary?: boolean
  }>
}
type Decision = {
  id: string
  stage: string
  outcome: string
  reason_code: string | null
  reason_text: string | null
  confidence: number | null
  evidence: DecisionEvidence | null
  policy_version: string | null
  evaluator_type: string
  model_class: string | null
  model_id: string | null
  trace_id: string | null
  created_at: string
}
type ModelRun = {
  model_id: string
  reasoning_effort: string
  policy_version: string
  status: string
  input_tokens: number | null
  output_tokens: number | null
  estimated_cost_usd: number | null
  web_search_calls?: number | null
  tool_cost_usd?: number | null
}
type IntelligenceEvidence = { url?: string; title?: string; type?: string }
type IntelligenceRecord = {
  id: string
  company_id: string | null
  opportunity_id: string | null
  capability: string
  capability_version: string
  payload: Record<string, unknown>
  evidence: IntelligenceEvidence[] | null
  confidence: number | null
  policy_version: string
  model_id: string | null
  reasoning_effort: string | null
  trace_id: string | null
  created_at: string
}
type OpportunityDetail = {
  opportunity: Opportunity
  decision: Decision | null
  modelRun: ModelRun | null
  intelligence: IntelligenceRecord[]
}

type CompanyView = {
  id: string
  name: string
  opportunities: Opportunity[]
  trajectory: IntelligenceRecord | null
}

type Stakeholder = {
  identity?: string
  title?: string
  role_in_decision?: string
  likely_interest?: string
  likely_objection?: string
  relationship_to_role?: string
  verification_status?: string
  evidence_urls?: string[]
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

const intelligenceSelect = 'id,company_id,opportunity_id,capability,capability_version,payload,evidence,confidence,policy_version,model_id,reasoning_effort,trace_id,created_at'

function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [email, setEmail] = useState('')
  const [authMessage, setAuthMessage] = useState('')
  const [page, setPage] = useState<Page>('Home')
  const [summary, setSummary] = useState<Summary>(emptySummary)
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [companyIntelligence, setCompanyIntelligence] = useState<IntelligenceRecord[]>([])
  const [activity, setActivity] = useState<Activity[]>([])
  const [grayZoneCount, setGrayZoneCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [detail, setDetail] = useState<OpportunityDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState('')

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
    setLoadError('')
    const [summaryResult, oppResult, sourceResult, activityResult, grayResult, companyIntelResult] = await Promise.all([
      supabase.rpc('intake_summary', { hours_back: 24 }),
      supabase.from('opportunities')
        .select('id,company_id,title,location,priority_class,screening_stage,current_reason_code,current_reason_text,current_confidence,first_seen_at,company:companies(display_name)')
        .eq('visibility', 'SURFACED')
        .order('first_seen_at', { ascending: false })
        .limit(50),
      supabase.from('source_registry')
        .select('id,display_name,source_family,health,last_success_at,last_error')
        .eq('enabled', true)
        .order('display_name'),
      supabase.from('activity_events')
        .select('id,severity,message,created_at,entity_type,entity_id')
        .order('created_at', { ascending: false })
        .limit(24),
      supabase.from('opportunities').select('id', { count: 'exact', head: true }).eq('visibility', 'GRAY_ZONE'),
      supabase.from('intelligence_records')
        .select(intelligenceSelect)
        .is('opportunity_id', null)
        .eq('status', 'COMPLETED')
        .order('created_at', { ascending: false })
        .limit(100),
    ])

    const firstError = [summaryResult.error, oppResult.error, sourceResult.error, activityResult.error, grayResult.error, companyIntelResult.error].find(Boolean)
    if (firstError) setLoadError(firstError.message)
    if (summaryResult.data?.[0]) setSummary(summaryResult.data[0] as Summary)
    setOpportunities((oppResult.data ?? []) as unknown as Opportunity[])
    setSources((sourceResult.data ?? []) as Source[])
    setActivity((activityResult.data ?? []) as Activity[])
    setCompanyIntelligence((companyIntelResult.data ?? []) as unknown as IntelligenceRecord[])
    setGrayZoneCount(grayResult.count ?? 0)
    setLoading(false)
  }

  async function openOpportunity(role: Opportunity) {
    setDetailLoading(true)
    setDetail(null)
    setDetailError('')
    const roleIntelQuery = supabase.from('intelligence_records')
      .select(intelligenceSelect)
      .eq('opportunity_id', role.id)
      .eq('status', 'COMPLETED')
      .order('created_at', { ascending: false })
      .limit(40)
    const companyIntelQuery = role.company_id
      ? supabase.from('intelligence_records')
          .select(intelligenceSelect)
          .eq('company_id', role.company_id)
          .is('opportunity_id', null)
          .eq('status', 'COMPLETED')
          .order('created_at', { ascending: false })
          .limit(20)
      : Promise.resolve({ data: [], error: null })

    const [decisionResult, roleIntelResult, companyIntelResult] = await Promise.all([
      supabase.from('screening_decisions')
        .select('id,stage,outcome,reason_code,reason_text,confidence,evidence,policy_version,evaluator_type,model_class,model_id,trace_id,created_at')
        .eq('opportunity_id', role.id)
        .order('created_at', { ascending: false })
        .limit(1)
        .maybeSingle(),
      roleIntelQuery,
      companyIntelQuery,
    ])

    const detailQueryError = [decisionResult.error, roleIntelResult.error, companyIntelResult.error].find(Boolean)
    if (detailQueryError) {
      setDetailError(detailQueryError.message)
      setDetailLoading(false)
      return
    }

    const decision = (decisionResult.data ?? null) as Decision | null
    let modelRun: ModelRun | null = null
    if (decision?.trace_id) {
      const modelResult = await supabase.from('model_runs')
        .select('model_id,reasoning_effort,policy_version,status,input_tokens,output_tokens,estimated_cost_usd,web_search_calls,tool_cost_usd')
        .eq('trace_id', decision.trace_id)
        .order('finished_at', { ascending: false })
        .limit(1)
        .maybeSingle()
      if (modelResult.error) {
        setDetailError(modelResult.error.message)
        setDetailLoading(false)
        return
      }
      modelRun = (modelResult.data ?? null) as ModelRun | null
    }

    const allIntel = [
      ...((roleIntelResult.data ?? []) as unknown as IntelligenceRecord[]),
      ...((companyIntelResult.data ?? []) as unknown as IntelligenceRecord[]),
    ]
    setDetail({ opportunity: role, decision, modelRun, intelligence: latestByCapability(allIntel) })
    setDetailLoading(false)
  }

  async function sendMagicLink(event: FormEvent) {
    event.preventDefault()
    setAuthMessage('Sending sign-in link...')
    const redirectTo = `${window.location.origin}/your-next-adventure/`
    const { error } = await supabase.auth.signInWithOtp({ email, options: { emailRedirectTo: redirectTo } })
    setAuthMessage(error ? error.message : 'Check your email for the sign-in link.')
  }

  const companies = useMemo<CompanyView[]>(() => groupCompanies(opportunities, companyIntelligence), [companyIntelligence, opportunities])

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

  const actionRequired = activity.filter((event) => event.severity === 'ACTION_REQUIRED').length
  const runtimeHealthy = !loadError && sources.length > 0 && sources.every((source) => source.health === 'HEALTHY')

  return (
    <div className="shell">
      <header>
        <div>
          <div className="eyebrow">YOURNEXTADVENTURE</div>
          <h1>Opportunity Cockpit</h1>
        </div>
        <div className="header-actions">
          <span className={`status-dot ${runtimeHealthy ? '' : 'attention'}`} /> {runtimeHealthy ? 'Live' : 'Needs attention'}
          <button className="ghost" onClick={() => void refresh()}>Refresh</button>
          <button className="ghost" onClick={() => void supabase.auth.signOut()}>Sign out</button>
        </div>
      </header>

      <nav>
        {(['Home', 'Intake', 'Opportunities', 'Companies'] as Page[]).map((item) => (
          <button key={item} className={page === item ? 'active' : ''} aria-current={page === item ? 'page' : undefined} onClick={() => setPage(item)}>{item}</button>
        ))}
      </nav>

      <div className="workspace">
        <main className="content">
          {loading && <p className="muted" aria-live="polite">Loading current state...</p>}
          {loadError && <div className="error-banner" role="alert">Live data error: {loadError}</div>}
          {!loading && page === 'Home' && <Home summary={summary} opportunities={opportunities} grayZoneCount={grayZoneCount} actionRequired={actionRequired} onOpen={openOpportunity} />}
          {!loading && page === 'Intake' && <Intake summary={summary} sources={sources} opportunities={opportunities} grayZoneCount={grayZoneCount} onOpen={openOpportunity} />}
          {!loading && page === 'Opportunities' && <OpportunityList opportunities={opportunities} onOpen={openOpportunity} />}
          {!loading && page === 'Companies' && <CompanyList companies={companies} onOpen={openOpportunity} />}
        </main>
        <ActivityRail activity={activity} />
      </div>
      {detailLoading && <div className="drawer-backdrop"><section className="decision-drawer"><p className="muted">Loading decision trace...</p></section></div>}
      {detailError && <div className="drawer-backdrop" onMouseDown={() => setDetailError('')}><section className="decision-drawer" role="dialog" aria-modal="true" aria-label="Decision detail error" onMouseDown={(e) => e.stopPropagation()}><div className="drawer-head"><h2>Decision detail unavailable</h2><button className="close" aria-label="Close error" onClick={() => setDetailError('')}>×</button></div><div className="error-banner" role="alert">{detailError}</div></section></div>}
      {detail && <DecisionDrawer detail={detail} onClose={() => setDetail(null)} />}
    </div>
  )
}

function Home({ summary, opportunities, grayZoneCount, actionRequired, onOpen }: { summary: Summary; opportunities: Opportunity[]; grayZoneCount: number; actionRequired: number; onOpen: (role: Opportunity) => void }) {
  return (
    <>
      <section className="hero-row">
        <div>
          <div className="eyebrow">WHAT MATTERS NOW</div>
          <h2>{summary.relevant} relevant opportunities surfaced in the last 24 hours</h2>
          <p className="muted">Broad discovery stays below the glass. Only roles that clear mandate-aware relevance screening enter this view.</p>
        </div>
        <div className="needs-me"><strong>{actionRequired}</strong><span>Needs me</span></div>
      </section>
      <div className="metric-grid">
        <Metric label="Tier 1" value={summary.tier_1} />
        <Metric label="Tier 2" value={summary.tier_2} />
        <Metric label="Monitor" value={summary.monitor} />
        <Metric label="Gray zone · system-held" value={grayZoneCount} />
      </div>
      <section className="panel">
        <div className="panel-title"><h3>Priority opportunities</h3><span>{opportunities.length} visible</span></div>
        <OpportunityRows opportunities={opportunities.slice(0, 8)} onOpen={onOpen} />
      </section>
    </>
  )
}

function Intake({ summary, sources, opportunities, grayZoneCount, onOpen }: { summary: Summary; sources: Source[]; opportunities: Opportunity[]; grayZoneCount: number; onOpen: (role: Opportunity) => void }) {
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
      <p className="muted">The raw universe remains auditable but hidden by default. Hard rejects require high confidence. Ambiguous roles stay in the gray zone for system follow-up instead of disappearing.</p>
      <section className="panel funnel">
        {funnel.map(([label, value], index) => <div className="funnel-step" key={label}><span>{label}</span><strong>{value}</strong>{index < funnel.length - 1 && <i>→</i>}</div>)}
      </section>
      <div className="split-grid">
        <section className="panel">
          <div className="panel-title"><h3>Source health</h3><span>{sources.length} enabled</span></div>
          {sources.length === 0 ? <p className="muted">No source state available.</p> : sources.map((source) => (
            <div className="source-row" key={source.id}>
              <div><strong>{source.display_name}</strong><small>{source.source_family} · {source.last_success_at ? `healthy ${relativeTime(source.last_success_at)}` : 'awaiting first success'}</small>{source.last_error && <small className="source-error">{source.last_error}</small>}</div>
              <span className={`health ${source.health.toLowerCase()}`}>{source.health}</span>
            </div>
          ))}
        </section>
        <section className="panel">
          <div className="panel-title"><h3>Screening outcomes</h3><span>last 24h</span></div>
          <StatRow label="Clear no, retained but hidden" value={summary.clear_no} />
          <StatRow label="Possible / gray zone" value={Math.max(summary.possible_fit, grayZoneCount)} />
          <StatRow label="Relevant and surfaced" value={summary.relevant} />
          <StatRow label="Needs data" value={summary.needs_data} />
        </section>
      </div>
      <section className="panel">
        <div className="panel-title"><h3>Roles that cleared relevance screening</h3><span>{opportunities.length}</span></div>
        <OpportunityRows opportunities={opportunities} onOpen={onOpen} />
      </section>
    </>
  )
}

function OpportunityList({ opportunities, onOpen }: { opportunities: Opportunity[]; onOpen: (role: Opportunity) => void }) {
  return <><div className="eyebrow">PURSUIT PORTFOLIO</div><h2>Opportunities</h2><p className="muted">This is not the internet. Every role here has already cleared mandate-aware relevance screening.</p><section className="panel"><OpportunityRows opportunities={opportunities} onOpen={onOpen} /></section></>
}

function CompanyList({ companies, onOpen }: { companies: CompanyView[]; onOpen: (role: Opportunity) => void }) {
  return <><div className="eyebrow">AGGREGATION LENS</div><h2>Companies</h2><p className="muted">Reusable company intelligence and surfaced mandates stay together without turning the product into a CRM.</p><div className="company-grid">{companies.length === 0 ? <section className="panel"><p className="muted">No surfaced company opportunities yet.</p></section> : companies.map((company) => {
    const trajectory = company.trajectory
    return <section className="panel company-card" key={company.id}>
      <div className="panel-title"><h3>{company.name}</h3><span>{company.opportunities.length} relevant role{company.opportunities.length === 1 ? '' : 's'}</span></div>
      {trajectory ? <div className="company-intelligence">
        <div className="intel-head"><strong>{payloadText(trajectory, 'current_health') ?? 'Current health not established.'}</strong><Confidence value={trajectory.confidence} /></div>
        <p>{payloadText(trajectory, 'why_now_for_role') ?? payloadList(trajectory, 'biggest_pain_points')[0] ?? 'No company-level why-now conclusion yet.'}</p>
        <IntelligenceSources sources={trajectory.evidence ?? []} />
      </div> : <p className="muted">Company-level trajectory is not established yet.</p>}
      <div className="company-opportunities"><span>Surfaced mandates</span><OpportunityRows opportunities={company.opportunities} onOpen={onOpen} /></div>
    </section>
  })}</div></>
}

function OpportunityRows({ opportunities, onOpen }: { opportunities: Opportunity[]; onOpen: (role: Opportunity) => void }) {
  if (opportunities.length === 0) return <p className="muted">No roles have cleared the relevance gate yet.</p>
  return <div>{opportunities.map((role) => (
    <button className="opportunity-row opportunity-button" key={role.id} onClick={() => onOpen(role)}>
      <div>
        <div className="role-title">{role.title}</div>
        <div className="role-meta">{role.company?.display_name ?? 'Company pending'}{role.location ? ` · ${role.location}` : ''}</div>
        {role.current_reason_text && <div className="reason">{role.current_reason_text}</div>}
      </div>
      <div className="role-actions"><span className={`priority ${(role.priority_class ?? 'needs_data').toLowerCase()}`}>{(role.priority_class ?? 'NEEDS_DATA').replace('_', ' ')}</span><span className="inspect">Inspect →</span></div>
    </button>
  ))}</div>
}

function DecisionDrawer({ detail, onClose }: { detail: OpportunityDetail; onClose: () => void }) {
  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [onClose])

  const { opportunity, decision, modelRun, intelligence } = detail
  const evidence = decision?.evidence ?? {}
  const sources = evidence.sources ?? []
  const intel = new Map(intelligence.map((record) => [record.capability, record]))
  const core = intel.get('CORE_X')
  const native = intel.get('NATIVE_CANDIDATE')
  const pressure = intel.get('COMMERCIAL_PRESSURE')
  const twoNotch = intel.get('TWO_NOTCH_UP')
  const stakeholders = intel.get('STAKEHOLDER_CONTEXT')
  const trajectory = intel.get('COMPANY_TRAJECTORY')

  return (
    <div className="drawer-backdrop" onMouseDown={onClose}>
      <section className="decision-drawer" role="dialog" aria-modal="true" aria-labelledby="decision-title" onMouseDown={(e) => e.stopPropagation()}>
        <div className="drawer-head"><div><div className="eyebrow">DECISION GLASS</div><h2 id="decision-title">{opportunity.title}</h2><p className="muted">{opportunity.company?.display_name}{opportunity.location ? ` · ${opportunity.location}` : ''}</p></div><button className="close" aria-label="Close decision details" onClick={onClose}>×</button></div>

        {core && <section className="intelligence-verdict">
          <span>CORE X</span>
          <strong>{payloadText(core, 'statement') ?? 'Core X is not established.'}</strong>
          {payloadText(core, 'why_now') && <p>{payloadText(core, 'why_now')}</p>}
          <Confidence value={core.confidence} />
        </section>}

        {!decision ? <p className="muted">No persisted screening decision trace is available yet.</p> : <>
          <div className="decision-verdict"><span>{decision.outcome.replaceAll('_', ' ')}</span><strong>{decision.reason_text}</strong></div>
          {evidence.mandate_summary && <DetailBlock title="Mandate"><p>{evidence.mandate_summary}</p></DetailBlock>}
          <div className="detail-grid">
            <DetailList title="Why it survived" items={evidence.supporting_factors ?? []} />
            <DetailList title="Constraints" items={evidence.constraints ?? []} />
          </div>
          <DetailList title="Material unknowns" items={evidence.material_unknowns ?? []} empty="No material unknowns recorded." />
          <DetailList title="Authority signals" items={evidence.authority_signals ?? []} empty="No authority signal established yet." />
        </>}

        {native && <DetailBlock title="Native candidate / winability">
          <div className="intel-head"><strong>{payloadText(native, 'native_class')?.replaceAll('_', ' ')}</strong><Confidence value={native.confidence} /></div>
          {payloadText(native, 'native_candidate_archetype') && <p className="muted-label">Likely native candidate: {payloadText(native, 'native_candidate_archetype')}</p>}
          {payloadText(native, 'win_thesis') && <p><strong>{payloadText(native, 'win_thesis')}</strong></p>}
          {payloadText(native, 'commentary') && <p>{payloadText(native, 'commentary')}</p>}
          <InlineLists leftTitle="Candidate advantages" left={payloadList(native, 'candidate_advantages')} rightTitle="Skepticism to overcome" right={payloadList(native, 'skepticism_to_overcome')} />
        </DetailBlock>}

        {pressure && <DetailBlock title="Hiring-manager commercial pressure">
          <div className="intel-head"><strong>{payloadText(pressure, 'statement')}</strong><Confidence value={pressure.confidence} /></div>
          <DetailList title="Pressure chain" items={payloadList(pressure, 'pressure_tree')} />
          <div className="trace-grid">
            <Trace label="6 months" value={payloadText(pressure, 'success_6_months') ?? 'UNKNOWN'} />
            <Trace label="12 months" value={payloadText(pressure, 'success_12_months') ?? 'UNKNOWN'} />
            <Trace label="18 months" value={payloadText(pressure, 'success_18_months') ?? 'UNKNOWN'} />
            <Trace label="HM must believe" value={payloadList(pressure, 'what_hm_needs_to_believe').join(' · ') || 'UNKNOWN'} />
          </div>
        </DetailBlock>}

        {twoNotch && <DetailBlock title="Two-Notch-Up / Aditya Lens">
          <IntelSequence label="Stated job" value={payloadText(twoNotch, 'level_0_stated_job')} />
          <IntelSequence label="Underlying outcome" value={payloadText(twoNotch, 'level_1_underlying_outcome')} />
          <IntelSequence label="Game changer" value={payloadText(twoNotch, 'level_2_game_changer')} />
          <IntelSequence label="Future business / operating model" value={payloadText(twoNotch, 'future_business_or_operating_model')} />
          <IntelSequence label="Economic consequence" value={payloadText(twoNotch, 'economic_consequence')} />
          <IntelSequence label="What the hire should build toward" value={payloadText(twoNotch, 'role_reinterpretation')} />
          <IntelSequence label="Overreach boundary" value={payloadText(twoNotch, 'overreach_boundary')} />
          <Confidence value={twoNotch.confidence} />
        </DetailBlock>}

        {stakeholders && <StakeholderBlock record={stakeholders} />}

        {trajectory && <DetailBlock title="Company trajectory">
          <div className="intel-head"><strong>{payloadText(trajectory, 'current_health')}</strong><Confidence value={trajectory.confidence} /></div>
          <div className="trace-grid">
            <Trace label="Growth" value={payloadText(trajectory, 'growth_trajectory') ?? 'UNKNOWN'} />
            <Trace label="Margin" value={payloadText(trajectory, 'margin_trajectory') ?? 'UNKNOWN'} />
          </div>
          <InlineLists leftTitle="Strategic priorities" left={payloadList(trajectory, 'strategic_priorities')} rightTitle="Biggest pressures" right={payloadList(trajectory, 'biggest_pain_points')} />
          <IntelligenceSources sources={trajectory.evidence ?? []} />
        </DetailBlock>}

        <DetailBlock title="Evidence trail">
          {sources.length === 0 ? <p className="muted">No screening-source evidence attached.</p> : sources.map((source, i) => (
            <div className="evidence-row" key={`${source.source_family}-${source.external_id}-${i}`}>
              <div><strong>{source.source_name ?? source.source_family ?? 'Source'}</strong><small>{source.source_family} · {source.state ?? 'state unknown'}{source.external_id ? ` · ${source.external_id}` : ''}</small></div>
              {source.canonical_url && <a href={source.canonical_url} target="_blank" rel="noreferrer">Open source ↗</a>}
            </div>
          ))}
        </DetailBlock>

        {decision && <DetailBlock title="Decision trace">
          <div className="trace-grid">
            <Trace label="Candidate path" value={evidence.candidate_path ?? 'Unknown'} />
            <Trace label="Evaluator" value={decision.evaluator_type} />
            <Trace label="Model" value={modelRun?.model_id ?? decision.model_id ?? 'Deterministic'} />
            <Trace label="Reasoning" value={modelRun?.reasoning_effort ?? 'n/a'} />
            <Trace label="Policy" value={decision.policy_version ?? 'Unknown'} />
            <Trace label="Trace" value={decision.trace_id ? decision.trace_id.slice(0, 12) : 'n/a'} />
          </div>
        </DetailBlock>}

        {intelligence.length > 0 && <DetailBlock title="Intelligence traces">
          <div className="intelligence-traces">{intelligence.map((record) => (
            <div key={record.id}><strong>{record.capability.replaceAll('_', ' ')}</strong><small>{record.model_id ?? 'Deterministic'} · {record.reasoning_effort ?? 'n/a'} · {record.capability_version} · trace {record.trace_id?.slice(0, 10) ?? 'n/a'}</small></div>
          ))}</div>
        </DetailBlock>}
      </section>
    </div>
  )
}

function StakeholderBlock({ record }: { record: IntelligenceRecord }) {
  const stakeholders = payloadStakeholders(record)
  const hm = payloadText(record, 'exact_hiring_manager') ?? 'UNKNOWN'
  const hmStatus = payloadText(record, 'hiring_manager_verification') ?? 'UNKNOWN'
  return <DetailBlock title="Stakeholder decision system">
    <div className="hm-line"><div><span>Exact hiring manager</span><strong>{hm}</strong></div><Verification value={hmStatus} /></div>
    {stakeholders.length === 0 ? <p className="muted">No defensible stakeholder identities established yet.</p> : stakeholders.map((person, i) => (
      <div className="stakeholder-row" key={`${person.identity}-${i}`}>
        <div><strong>{person.identity ?? 'Unknown person'}</strong><small>{person.title ?? 'Title unknown'} · {person.role_in_decision ?? 'role unknown'}</small>{person.relationship_to_role && <p>{person.relationship_to_role}</p>}</div>
        <Verification value={person.verification_status ?? 'UNKNOWN'} />
      </div>
    ))}
    <DetailList title="Alternate hypotheses" items={payloadList(record, 'alternate_hypotheses')} empty="None retained." />
    <IntelligenceSources sources={record.evidence ?? []} />
  </DetailBlock>
}

function IntelligenceSources({ sources }: { sources: IntelligenceEvidence[] }) {
  if (!sources.length) return <p className="muted">No external research sources persisted for this capability.</p>
  return <div className="research-sources">{sources.slice(0, 12).map((source, i) => source.url ? (
    <a key={`${source.url}-${i}`} href={source.url} target="_blank" rel="noreferrer">{source.title ?? source.url} ↗</a>
  ) : null)}</div>
}

function InlineLists({ leftTitle, left, rightTitle, right }: { leftTitle: string; left: string[]; rightTitle: string; right: string[] }) {
  return <div className="detail-grid"><DetailList title={leftTitle} items={left} /><DetailList title={rightTitle} items={right} /></div>
}

function IntelSequence({ label, value }: { label: string; value?: string }) {
  if (!value) return null
  return <div className="intel-sequence"><span>{label}</span><p>{value}</p></div>
}

function Confidence({ value }: { value: number | null }) {
  if (value === null || value === undefined) return null
  const label = value >= .85 ? 'High confidence' : value >= .65 ? 'Moderate confidence' : 'Low confidence'
  return <span className="confidence">{label}</span>
}

function Verification({ value }: { value: string }) {
  return <span className={`verification ${value.toLowerCase()}`}>{value.replaceAll('_', ' ')}</span>
}

function latestByCapability(records: IntelligenceRecord[]): IntelligenceRecord[] {
  const seen = new Set<string>()
  return records
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .filter((record) => {
      if (seen.has(record.capability)) return false
      seen.add(record.capability)
      return true
    })
}

function payloadText(record: IntelligenceRecord, key: string): string | undefined {
  const value = record.payload?.[key]
  return typeof value === 'string' && value.trim() ? value : undefined
}

function payloadList(record: IntelligenceRecord, key: string): string[] {
  const value = record.payload?.[key]
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string' && item.trim().length > 0) : []
}

function payloadStakeholders(record: IntelligenceRecord): Stakeholder[] {
  const value = record.payload?.stakeholders
  return Array.isArray(value) ? value.filter((item): item is Stakeholder => Boolean(item) && typeof item === 'object') : []
}

function DetailBlock({ title, children }: { title: string; children: React.ReactNode }) { return <section className="detail-block"><h3>{title}</h3>{children}</section> }
function DetailList({ title, items, empty = 'None recorded.' }: { title: string; items: string[]; empty?: string }) { return <DetailBlock title={title}>{items.length ? <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="muted">{empty}</p>}</DetailBlock> }
function Trace({ label, value }: { label: string; value: string }) { return <div><span>{label}</span><strong>{value}</strong></div> }

function ActivityRail({ activity }: { activity: Activity[] }) {
  const needsMe = activity.filter((event) => event.severity === 'ACTION_REQUIRED')
  const operational = activity.filter((event) => event.severity !== 'ACTION_REQUIRED')
  return <aside aria-label="Activity and Needs Me">
    <div className="panel-title"><h3>Activity / Needs Me</h3><span>{needsMe.length ? `${needsMe.length} action required` : 'system healthy'}</span></div>
    {needsMe.length > 0 && <section className="needs-me-list"><div className="eyebrow">NEEDS ME</div>{needsMe.map((event) => <ActivityItem event={event} key={event.id} />)}</section>}
    {operational.length === 0 && needsMe.length === 0 ? <p className="muted">Waiting for first autonomous run.</p> : operational.map((event) => <ActivityItem event={event} key={event.id} />)}
  </aside>
}

function ActivityItem({ event }: { event: Activity }) {
  const prominent = ['ATTENTION', 'ACTION_REQUIRED', 'ERROR'].includes(event.severity)
  return <div className={`activity-item ${prominent ? 'prominent' : ''}`}><span className={`activity-mark ${event.severity.toLowerCase()}`} /><div><strong>{event.message}</strong><small>{relativeTime(event.created_at)} · {event.severity.replace('_', ' ')}</small></div></div>
}

function relativeTime(value: string) {
  const diff = Date.now() - new Date(value).getTime()
  const mins = Math.max(0, Math.floor(diff / 60000))
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

function Metric({ label, value }: { label: string; value: number }) { return <div className="metric"><span>{label}</span><strong>{value}</strong></div> }
function StatRow({ label, value }: { label: string; value: number }) { return <div className="stat-row"><span>{label}</span><strong>{value}</strong></div> }

export default App
