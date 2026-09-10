import { FormEvent, useEffect, useId, useMemo, useRef, useState } from 'react'
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
type Coverage = {
  direct_sources: number
  direct_companies: number
  market_channels: number
  market_signals: number
  market_companies: number
  linked_opportunities: number
  probe_total: number
  unresolved_probes: number
  last_market_success: string | null
}
type RecallProbe = {
  id?: string
  company_name: string
  title: string
  discovery_url: string
  official_url: string | null
  classification: string
  classification_reason: string
  checked_at: string
}
type PipelineHealth = {
  awaiting_triage: number
  oldest_awaiting_triage: string | null
  awaiting_qualification: number
  oldest_awaiting_qualification: string | null
  stale_running: number
  recent_throttles: number
  last_discovery_success: string | null
  last_triage_success: string | null
  last_qualification_success: string | null
  degraded: boolean
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
  opportunity_sources?: Array<{
    is_primary: boolean
    source_record: { canonical_url: string } | null
  }>
}
type Source = {
  id: string
  display_name: string
  source_family: string
  base_url: string
  health: string
  last_sync_at: string | null
  last_success_at: string | null
  last_error: string | null
  metadata?: { company_name?: string } | null
}
type Activity = {
  id: string
  severity: string
  message: string
  created_at: string
  entity_type: string | null
  entity_id: string | null
  details: Record<string, unknown> | null
}
type IngestionRun = {
  id: string
  started_at: string
  finished_at: string | null
  status: string
  discovered_count: number
  new_count: number
  changed_count: number
  duplicate_count: number
  closed_count: number
  error_count: number
  error_text: string | null
}
type SourceRecord = {
  id: string
  external_id: string
  canonical_url: string | null
  state: string
  first_seen_at: string
  last_seen_at: string
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
  supersedes_id: string | null
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
  status: string
  payload: Record<string, unknown>
  evidence: IntelligenceEvidence[] | null
  confidence: number | null
  policy_version: string
  model_id: string | null
  reasoning_effort: string | null
  trace_id: string | null
  supersedes_id: string | null
  created_at: string
  updated_at: string
}
type OpportunityDetail = {
  opportunity: Opportunity
  decision: Decision | null
  decisionHistory: Decision[]
  modelRun: ModelRun | null
  intelligence: IntelligenceRecord[]
}

type CompanyView = {
  id: string
  name: string
  opportunities: Opportunity[]
  trajectory: IntelligenceRecord | null
}

type OpportunitySetDetail = {
  title: string
  description: string
  opportunities: Opportunity[]
}

type SourceDetail = {
  source: Source
  runs: IngestionRun[]
  records: SourceRecord[]
  recordCount: number
  opportunities: Opportunity[]
}

type CompanyDetail = {
  company: CompanyView
  intelligence: IntelligenceRecord[]
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
const emptyCoverage: Coverage = { direct_sources: 0, direct_companies: 0, market_channels: 0, market_signals: 0, market_companies: 0, linked_opportunities: 0, probe_total: 0, unresolved_probes: 0, last_market_success: null }
const emptyPipeline: PipelineHealth = { awaiting_triage: 0, oldest_awaiting_triage: null, awaiting_qualification: 0, oldest_awaiting_qualification: null, stale_running: 0, recent_throttles: 0, last_discovery_success: null, last_triage_success: null, last_qualification_success: null, degraded: false }

const intelligenceSelect = 'id,company_id,opportunity_id,capability,capability_version,status,payload,evidence,confidence,policy_version,model_id,reasoning_effort,trace_id,supersedes_id,created_at,updated_at'
const opportunitySelect = 'id,company_id,title,location,priority_class,screening_stage,current_reason_code,current_reason_text,current_confidence,first_seen_at,company:companies(display_name),opportunity_sources(is_primary,source_record:source_records(canonical_url))'
const lastDay = () => new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()

function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [email, setEmail] = useState('')
  const [authMessage, setAuthMessage] = useState('')
  const [page, setPage] = useState<Page>('Home')
  const [summary, setSummary] = useState<Summary>(emptySummary)
  const [coverage, setCoverage] = useState<Coverage>(emptyCoverage)
  const [recallProbes, setRecallProbes] = useState<RecallProbe[]>([])
  const [pipeline, setPipeline] = useState<PipelineHealth>(emptyPipeline)
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
  const [opportunitySet, setOpportunitySet] = useState<OpportunitySetDetail | null>(null)
  const [sourceDetail, setSourceDetail] = useState<SourceDetail | null>(null)
  const [companyDetail, setCompanyDetail] = useState<CompanyDetail | null>(null)
  const [activityDetail, setActivityDetail] = useState<Activity | null>(null)
  const [activitySet, setActivitySet] = useState<Activity[] | null>(null)
  const [drilldownLoading, setDrilldownLoading] = useState('')
  const [drilldownError, setDrilldownError] = useState('')

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
    const staleBefore = new Date(Date.now() - 35 * 60 * 1000).toISOString()
    const dayBefore = lastDay()
    const [summaryResult, oppResult, sourceResult, activityResult, grayResult, companyIntelResult, recallResult, triageCountResult, triageOldestResult, qualificationCountResult, qualificationOldestResult, staleResult, throttleResult, capacityResult, triageSuccessResult, qualificationSuccessResult] = await Promise.all([
      supabase.rpc('intake_summary', { hours_back: 24 }),
      supabase.from('opportunities')
        .select(opportunitySelect)
        .eq('visibility', 'SURFACED')
        .order('first_seen_at', { ascending: false })
        .limit(50),
      supabase.from('source_registry')
        .select('id,display_name,source_family,base_url,health,last_sync_at,last_success_at,last_error,metadata')
        .eq('enabled', true)
        .order('display_name'),
      supabase.from('activity_events')
        .select('id,severity,message,created_at,entity_type,entity_id,details')
        .order('created_at', { ascending: false })
        .limit(24),
      supabase.from('opportunities').select('id', { count: 'exact', head: true }).eq('visibility', 'GRAY_ZONE'),
      supabase.from('intelligence_records')
        .select(intelligenceSelect)
        .is('opportunity_id', null)
        .eq('status', 'COMPLETED')
        .order('created_at', { ascending: false })
        .limit(100),
      supabase.from('activity_events')
        .select('id,severity,message,created_at,entity_type,entity_id,details')
        .eq('event_type', 'MARKET_DISCOVERY_COMPLETED')
        .order('created_at', { ascending: false })
        .limit(1)
        .maybeSingle(),
      supabase.from('opportunities').select('id', { count: 'exact', head: true }).eq('lifecycle_state', 'ACTIVE').eq('screening_stage', 'ELIGIBLE'),
      supabase.from('opportunities').select('first_seen_at').eq('lifecycle_state', 'ACTIVE').eq('screening_stage', 'ELIGIBLE').order('first_seen_at', { ascending: true }).limit(1).maybeSingle(),
      supabase.from('opportunities').select('id', { count: 'exact', head: true }).eq('lifecycle_state', 'ACTIVE').eq('screening_stage', 'TRIAGE_RELEVANT'),
      supabase.from('opportunities').select('first_seen_at').eq('lifecycle_state', 'ACTIVE').eq('screening_stage', 'TRIAGE_RELEVANT').order('first_seen_at', { ascending: true }).limit(1).maybeSingle(),
      supabase.from('model_runs').select('id', { count: 'exact', head: true }).eq('status', 'RUNNING').lt('started_at', staleBefore),
      supabase.from('model_runs').select('id', { count: 'exact', head: true }).gte('started_at', dayBefore).ilike('error_text', '%429%'),
      supabase.from('model_capacity').select('model_id,recent_throttles,last_throttle_at,blocked_until,last_success_at'),
      supabase.from('model_runs').select('finished_at').eq('capability', 'RELEVANCE_TRIAGE').eq('status', 'PASSED').order('finished_at', { ascending: false }).limit(1).maybeSingle(),
      supabase.from('model_runs').select('finished_at').eq('capability', 'DEEP_QUALIFICATION').eq('status', 'PASSED').order('finished_at', { ascending: false }).limit(1).maybeSingle(),
    ])

    const firstError = [summaryResult.error, oppResult.error, sourceResult.error, activityResult.error, grayResult.error, companyIntelResult.error, recallResult.error, triageCountResult.error, triageOldestResult.error, qualificationCountResult.error, qualificationOldestResult.error, staleResult.error, throttleResult.error, capacityResult.error, triageSuccessResult.error, qualificationSuccessResult.error].find(Boolean)
    if (firstError) setLoadError(firstError.message)
    if (summaryResult.data?.[0]) setSummary(summaryResult.data[0] as Summary)
    setOpportunities((oppResult.data ?? []) as unknown as Opportunity[])
    setSources((sourceResult.data ?? []) as Source[])
    setActivity((activityResult.data ?? []) as Activity[])
    setCompanyIntelligence((companyIntelResult.data ?? []) as unknown as IntelligenceRecord[])
    const sourceRows = (sourceResult.data ?? []) as Source[]
    const direct = sourceRows.filter((source) => source.source_family !== 'DISCOVERY_SIGNAL')
    const market = sourceRows.filter((source) => source.source_family === 'DISCOVERY_SIGNAL')
    const detail = (recallResult.data?.details ?? {}) as Record<string, unknown>
    const probes = Array.isArray(detail.recall_probes) ? detail.recall_probes as RecallProbe[] : []
    const marketSourceIds = market.map((source) => source.id)
    let marketSignals = 0
    let linkedOpportunities = 0
    let marketCompanies = 0
    if (marketSourceIds.length) {
      const recordsResult = await supabase.from('source_records').select('id', { count: 'exact' }).in('source_id', marketSourceIds)
      if (recordsResult.error) setLoadError(recordsResult.error.message)
      const recordIds = (recordsResult.data ?? []).map((record) => record.id)
      marketSignals = recordsResult.count ?? recordIds.length
      if (recordIds.length) {
        const linksResult = await supabase.from('opportunity_sources').select('opportunity_id').in('source_record_id', recordIds)
        if (linksResult.error) setLoadError(linksResult.error.message)
        const opportunityIds = [...new Set((linksResult.data ?? []).map((link) => link.opportunity_id))]
        linkedOpportunities = opportunityIds.length
        if (opportunityIds.length) {
          const companiesResult = await supabase.from('opportunities').select('company_id').in('id', opportunityIds)
          if (companiesResult.error) setLoadError(companiesResult.error.message)
          marketCompanies = new Set((companiesResult.data ?? []).map((role) => role.company_id).filter(Boolean)).size
        }
      }
    }
    setCoverage({ direct_sources: direct.length, direct_companies: new Set(direct.map((source) => source.metadata?.company_name).filter(Boolean)).size, market_channels: market.length, market_signals: marketSignals, market_companies: marketCompanies, linked_opportunities: linkedOpportunities, probe_total: probes.length, unresolved_probes: probes.filter((probe) => probe.classification.startsWith('MISSED_') || probe.classification.includes('FAILURE') || probe.classification.startsWith('UNKNOWN')).length, last_market_success: market[0]?.last_success_at ?? null })
    setRecallProbes(probes)
    const awaitingTriage = triageCountResult.count ?? 0
    const awaitingQualification = qualificationCountResult.count ?? 0
    const staleRunning = staleResult.count ?? 0
    const capacityRows = capacityResult.data ?? []
    const recentCapacityRows = capacityRows.filter((row) => row.last_throttle_at && new Date(row.last_throttle_at).getTime() >= new Date(dayBefore).getTime())
    const durableThrottles = recentCapacityRows.reduce((sum, row) => sum + (row.recent_throttles ?? 0), 0)
    const recentThrottles = capacityRows.length ? durableThrottles : (throttleResult.count ?? 0)
    const unresolvedThrottle = capacityRows.length ? recentCapacityRows.some((row) => !row.last_success_at || new Date(row.last_throttle_at).getTime() > new Date(row.last_success_at).getTime() || (row.blocked_until && new Date(row.blocked_until).getTime() > Date.now())) : recentThrottles > 0
    const oldestTriage = triageOldestResult.data?.first_seen_at ?? null
    const oldestQualification = qualificationOldestResult.data?.first_seen_at ?? null
    const triageTooOld = Boolean(oldestTriage && Date.now() - new Date(oldestTriage).getTime() > 6 * 60 * 60 * 1000)
    const qualificationTooOld = Boolean(oldestQualification && Date.now() - new Date(oldestQualification).getTime() > 4 * 60 * 60 * 1000)
    setPipeline({ awaiting_triage: awaitingTriage, oldest_awaiting_triage: oldestTriage, awaiting_qualification: awaitingQualification, oldest_awaiting_qualification: oldestQualification, stale_running: staleRunning, recent_throttles: recentThrottles, last_discovery_success: market[0]?.last_success_at ?? null, last_triage_success: triageSuccessResult.data?.finished_at ?? null, last_qualification_success: qualificationSuccessResult.data?.finished_at ?? null, degraded: staleRunning > 0 || unresolvedThrottle || triageTooOld || qualificationTooOld })
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
      .order('created_at', { ascending: false })
      .limit(40)
    const companyIntelQuery = role.company_id
      ? supabase.from('intelligence_records')
          .select(intelligenceSelect)
          .eq('company_id', role.company_id)
          .is('opportunity_id', null)
          .order('created_at', { ascending: false })
          .limit(20)
      : Promise.resolve({ data: [], error: null })

    const [decisionResult, roleIntelResult, companyIntelResult] = await Promise.all([
      supabase.from('screening_decisions')
        .select('id,stage,outcome,reason_code,reason_text,confidence,evidence,policy_version,evaluator_type,model_class,model_id,trace_id,supersedes_id,created_at')
        .eq('opportunity_id', role.id)
        .order('created_at', { ascending: false })
        .limit(20),
      roleIntelQuery,
      companyIntelQuery,
    ])

    const detailQueryError = [decisionResult.error, roleIntelResult.error, companyIntelResult.error].find(Boolean)
    if (detailQueryError) {
      setDetailError(detailQueryError.message)
      setDetailLoading(false)
      return
    }

    const decisionHistory = (decisionResult.data ?? []) as Decision[]
    const decision = decisionHistory[0] ?? null
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
    setDetail({ opportunity: role, decision, decisionHistory, modelRun, intelligence: allIntel })
    setDetailLoading(false)
  }

  async function openOpportunitySet(kind: string, title: string, description: string) {
    setDrilldownLoading(title)
    setDrilldownError('')
    setOpportunitySet(null)
    try {
      let rows: Opportunity[] = []
      if (kind === 'discovered') {
        const recordsResult = await supabase.from('source_records').select('id').gte('first_seen_at', lastDay()).order('first_seen_at', { ascending: false }).limit(500)
        if (recordsResult.error) throw recordsResult.error
        const recordIds = (recordsResult.data ?? []).map((record) => record.id)
        if (recordIds.length) {
          const linksResult = await supabase.from('opportunity_sources').select('opportunity_id').in('source_record_id', recordIds)
          if (linksResult.error) throw linksResult.error
          const opportunityIds = [...new Set((linksResult.data ?? []).map((link) => link.opportunity_id))]
          if (opportunityIds.length) {
            const result = await supabase.from('opportunities').select(opportunitySelect).in('id', opportunityIds).order('first_seen_at', { ascending: false }).limit(100)
            if (result.error) throw result.error
            rows = (result.data ?? []) as unknown as Opportunity[]
          }
        }
      } else {
        let query = supabase.from('opportunities').select(opportunitySelect).order('first_seen_at', { ascending: false }).limit(100)
        if (!['gray', 'awaiting_triage', 'awaiting_qualification'].includes(kind)) query = query.gte('first_seen_at', lastDay())
        if (kind === 'canonical') query = query
        if (kind === 'eligible') query = query.in('screening_stage', ['ELIGIBLE', 'TRIAGE_CLEAR_NO', 'TRIAGE_POSSIBLE', 'TRIAGE_RELEVANT', 'DEEP_QUALIFY', 'PRIORITIZED'])
        if (kind === 'relevant') query = query.eq('visibility', 'SURFACED')
        if (kind === 'priority') query = query.in('priority_class', ['TIER_1', 'TIER_2'])
        if (kind === 'tier_1') query = query.eq('priority_class', 'TIER_1')
        if (kind === 'tier_2') query = query.eq('priority_class', 'TIER_2')
        if (kind === 'monitor') query = query.eq('priority_class', 'MONITOR')
        if (kind === 'gray') query = query.eq('visibility', 'GRAY_ZONE')
        if (kind === 'clear_no') query = query.eq('screening_stage', 'TRIAGE_CLEAR_NO')
        if (kind === 'possible') query = query.eq('screening_stage', 'TRIAGE_POSSIBLE')
        if (kind === 'needs_data') query = query.eq('priority_class', 'NEEDS_DATA')
        if (kind === 'awaiting_triage') query = query.eq('screening_stage', 'ELIGIBLE')
        if (kind === 'awaiting_qualification') query = query.eq('screening_stage', 'TRIAGE_RELEVANT')
        const result = await query
        if (result.error) throw result.error
        rows = (result.data ?? []) as unknown as Opportunity[]
      }
      setOpportunitySet({ title, description, opportunities: rows })
    } catch (error) {
      setDrilldownError(error instanceof Error ? error.message : 'The underlying role set could not be loaded.')
    } finally {
      setDrilldownLoading('')
    }
  }

  async function openSource(source: Source) {
    setDrilldownLoading(source.display_name)
    setDrilldownError('')
    setSourceDetail(null)
    try {
      const [runsResult, recordsResult] = await Promise.all([
        supabase.from('ingestion_runs').select('id,started_at,finished_at,status,discovered_count,new_count,changed_count,duplicate_count,closed_count,error_count,error_text').eq('source_id', source.id).order('started_at', { ascending: false }).limit(8),
        supabase.from('source_records').select('id,external_id,canonical_url,state,first_seen_at,last_seen_at', { count: 'exact' }).eq('source_id', source.id).order('last_seen_at', { ascending: false }).limit(30),
      ])
      const firstError = runsResult.error ?? recordsResult.error
      if (firstError) throw firstError
      const records = (recordsResult.data ?? []) as SourceRecord[]
      let sourceOpportunities: Opportunity[] = []
      if (records.length) {
        const linksResult = await supabase.from('opportunity_sources').select('opportunity_id').in('source_record_id', records.map((record) => record.id))
        if (linksResult.error) throw linksResult.error
        const ids = [...new Set((linksResult.data ?? []).map((link) => link.opportunity_id))]
        if (ids.length) {
          const opportunitiesResult = await supabase.from('opportunities').select(opportunitySelect).in('id', ids).order('last_seen_at', { ascending: false }).limit(30)
          if (opportunitiesResult.error) throw opportunitiesResult.error
          sourceOpportunities = (opportunitiesResult.data ?? []) as unknown as Opportunity[]
        }
      }
      setSourceDetail({ source, runs: (runsResult.data ?? []) as IngestionRun[], records, recordCount: recordsResult.count ?? records.length, opportunities: sourceOpportunities })
    } catch (error) {
      setDrilldownError(error instanceof Error ? error.message : 'Source detail could not be loaded.')
    } finally {
      setDrilldownLoading('')
    }
  }

  async function openCompany(company: CompanyView) {
    setDrilldownLoading(company.name)
    setDrilldownError('')
    setCompanyDetail(null)
    const result = await supabase.from('intelligence_records').select(intelligenceSelect).eq('company_id', company.id).eq('status', 'COMPLETED').order('created_at', { ascending: false }).limit(100)
    if (result.error) setDrilldownError(result.error.message)
    else setCompanyDetail({ company, intelligence: (result.data ?? []) as unknown as IntelligenceRecord[] })
    setDrilldownLoading('')
  }

  async function openActivity(event: Activity) {
    if (event.entity_type === 'opportunity' && event.entity_id) {
      const loaded = opportunities.find((role) => role.id === event.entity_id)
      if (loaded) return void openOpportunity(loaded)
      setDrilldownLoading('Linked opportunity')
      const result = await supabase.from('opportunities').select(opportunitySelect).eq('id', event.entity_id).maybeSingle()
      setDrilldownLoading('')
      if (result.error) return setDrilldownError(result.error.message)
      if (result.data) return void openOpportunity(result.data as unknown as Opportunity)
    }
    if (event.entity_type === 'source' && event.entity_id) {
      let source = sources.find((item) => item.id === event.entity_id)
      if (!source) {
        setDrilldownLoading('Linked source')
        const result = await supabase.from('source_registry').select('id,display_name,source_family,base_url,health,last_sync_at,last_success_at,last_error').eq('id', event.entity_id).maybeSingle()
        setDrilldownLoading('')
        if (result.error) return setDrilldownError(result.error.message)
        source = (result.data ?? undefined) as Source | undefined
      }
      if (source) return void openSource(source)
    }
    setActivityDetail(event)
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
  const runtimeHealthy = !loadError && !pipeline.degraded && sources.length > 0 && sources.every((source) => source.health === 'HEALTHY')
  const overlayBusy = detailLoading || Boolean(drilldownLoading) || Boolean(drilldownError) || Boolean(detailError)

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
          {!loading && page === 'Home' && <Home summary={summary} pipeline={pipeline} opportunities={opportunities} grayZoneCount={grayZoneCount} actionRequired={actionRequired} onOpen={openOpportunity} onDrill={openOpportunitySet} onNeedsMe={() => setActivitySet(activity.filter((event) => event.severity === 'ACTION_REQUIRED'))} />}
          {!loading && page === 'Intake' && <Intake summary={summary} pipeline={pipeline} coverage={coverage} recallProbes={recallProbes} sources={sources} opportunities={opportunities} grayZoneCount={grayZoneCount} onOpen={openOpportunity} onDrill={openOpportunitySet} onSource={openSource} />}
          {!loading && page === 'Opportunities' && <OpportunityList opportunities={opportunities} onOpen={openOpportunity} />}
          {!loading && page === 'Companies' && <CompanyList companies={companies} onOpen={openOpportunity} onCompany={openCompany} />}
        </main>
        <ActivityRail activity={activity} onOpen={openActivity} />
      </div>
      {opportunitySet && !detail && !overlayBusy && <OpportunitySetDrawer detail={opportunitySet} onOpen={openOpportunity} onClose={() => setOpportunitySet(null)} />}
      {companyDetail && !detail && !overlayBusy && <CompanyDrawer detail={companyDetail} onOpen={openOpportunity} onClose={() => setCompanyDetail(null)} />}
      {activitySet && !sourceDetail && !activityDetail && !detail && !overlayBusy && <ActivitySetDrawer events={activitySet} onOpen={openActivity} onClose={() => setActivitySet(null)} />}
      {sourceDetail && !detail && !overlayBusy && <SourceDrawer detail={sourceDetail} onOpen={openOpportunity} onClose={() => setSourceDetail(null)} />}
      {activityDetail && !detail && !overlayBusy && <ActivityDrawer event={activityDetail} onClose={() => setActivityDetail(null)} />}
      {detailLoading && <div className="drawer-backdrop"><section className="decision-drawer" aria-live="polite"><p className="muted">Loading decision trace...</p></section></div>}
      {drilldownLoading && <div className="drawer-backdrop"><section className="decision-drawer" aria-live="polite"><p className="muted">Loading {drilldownLoading}...</p></section></div>}
      {drilldownError && <ErrorDrawer message={drilldownError} onClose={() => setDrilldownError('')} />}
      {detailError && <div className="drawer-backdrop" onMouseDown={() => setDetailError('')}><section className="decision-drawer" role="dialog" aria-modal="true" aria-label="Decision detail error" onMouseDown={(e) => e.stopPropagation()}><div className="drawer-head"><h2>Decision detail unavailable</h2><button className="close" aria-label="Close error" onClick={() => setDetailError('')}>×</button></div><div className="error-banner" role="alert">{detailError}</div></section></div>}
      {detail && <DecisionDrawer detail={detail} onClose={() => setDetail(null)} />}
    </div>
  )
}

function Home({ summary, pipeline, opportunities, grayZoneCount, actionRequired, onOpen, onDrill, onNeedsMe }: { summary: Summary; pipeline: PipelineHealth; opportunities: Opportunity[]; grayZoneCount: number; actionRequired: number; onOpen: (role: Opportunity) => void; onDrill: (kind: string, title: string, description: string) => void; onNeedsMe: () => void }) {
  return (
    <>
      <section className="hero-row">
        <div>
          <div className="eyebrow">WHAT MATTERS NOW</div>
          <button className="conclusion-link" onClick={() => void onDrill('relevant', 'Surfaced opportunities', 'Roles first seen in the last 24 hours whose persisted visibility is SURFACED.')}><span>{summary.relevant} surfaced from roles first seen in the last 24 hours</span><small>Inspect underlying roles →</small></button>
          <p className="muted">Broad discovery stays below the glass. Only roles that clear mandate-aware relevance screening enter this view.</p>
        </div>
        <button className="needs-me interactive-card" onClick={onNeedsMe}><strong>{actionRequired}</strong><span>Needs me · inspect →</span></button>
      </section>
      <PipelineStatus pipeline={pipeline} onDrill={onDrill} />
      <div className="metric-grid">
        <Metric label="Tier 1" value={summary.tier_1} onClick={() => void onDrill('tier_1', 'Tier 1 opportunities', 'Highest-priority surfaced roles first seen in the last 24 hours.')} />
        <Metric label="Tier 2" value={summary.tier_2} onClick={() => void onDrill('tier_2', 'Tier 2 opportunities', 'Worth-pursuing surfaced roles first seen in the last 24 hours.')} />
        <Metric label="Monitor" value={summary.monitor} onClick={() => void onDrill('monitor', 'Monitor opportunities', 'Surfaced roles currently held for monitoring and first seen in the last 24 hours.')} />
        <Metric label="Gray zone · system-held" value={grayZoneCount} onClick={() => void onDrill('gray', 'Gray-zone audit set', 'Ambiguous roles retained for system follow-up rather than hidden as clear-no decisions.')} />
      </div>
      <section className="panel">
        <div className="panel-title"><h3>Surfaced opportunities</h3><span>{opportunities.length} visible</span></div>
        <OpportunityRows opportunities={opportunities.slice(0, 8)} onOpen={onOpen} />
      </section>
    </>
  )
}

function Intake({ summary, pipeline, coverage, recallProbes, sources, opportunities, grayZoneCount, onOpen, onDrill, onSource }: { summary: Summary; pipeline: PipelineHealth; coverage: Coverage; recallProbes: RecallProbe[]; sources: Source[]; opportunities: Opportunity[]; grayZoneCount: number; onOpen: (role: Opportunity) => void; onDrill: (kind: string, title: string, description: string) => void; onSource: (source: Source) => void }) {
  const funnel = [
    ['discovered', 'Signals discovered', summary.discovered],
    ['canonical', 'Canonicalized roles', summary.canonical],
    ['awaiting_triage', 'Awaiting mandate triage', pipeline.awaiting_triage],
    ['relevant', 'Surfaced · new ≤24h', summary.relevant],
    ['priority', 'Tier 1/2 · new ≤24h', summary.tier_1 + summary.tier_2],
  ] as const
  return (
    <>
      <div className="eyebrow">SCREENING CONTROL</div>
      <h2>Broad discovery. Narrow human attention.</h2>
      <p className="muted">The raw universe remains auditable but hidden by default. Hard rejects require high confidence. Ambiguous roles stay in the gray zone for system follow-up instead of disappearing.</p>
      <section className="panel funnel">
        {funnel.map(([kind, label, value], index) => <div className="funnel-step" key={label}><button onClick={() => void onDrill(kind, label, `Exact persisted-state records backing ${label.toLowerCase()}; labels marked ≤24h filter on first-seen time.`)}><span>{label}</span><strong>{value}</strong><small>Inspect →</small></button>{index < funnel.length - 1 && <i>→</i>}</div>)}
      </section>
      <PipelineStatus pipeline={pipeline} onDrill={onDrill} />
      <section className="panel coverage-panel">
        <div className="panel-title"><h3>Market coverage</h3><span>{coverage.last_market_success ? `last scan ${relativeTime(coverage.last_market_success)}` : 'awaiting first market scan'}</span></div>
        <p className="muted">Coverage measures where we look; health measures whether a configured connector ran. These are intentionally separate.</p>
        <div className="coverage-grid" aria-label="Discovery coverage measures">
          <div><span>Direct sources</span><strong>{coverage.direct_sources}</strong><small>{coverage.direct_companies} named employers</small></div>
          <div><span>Market channels</span><strong>{coverage.market_channels}</strong><small>{coverage.market_companies} companies beyond the registry</small></div>
          <div><span>Market signals</span><strong>{coverage.market_signals}</strong><small>{coverage.linked_opportunities} canonical links</small></div>
          <div><span>Recall probes</span><strong>{coverage.probe_total}</strong><small>{coverage.unresolved_probes} unresolved misses</small></div>
        </div>
        <div className="probe-list">
          <div className="panel-title"><h4>Independent recall probes</h4><span>private runtime evidence</span></div>
          {recallProbes.length === 0 ? <p className="muted">No independent live-scan probes have been reconciled yet.</p> : recallProbes.map((probe) => (
            <div className="probe-row" key={probe.id ?? probe.discovery_url}>
              <div><strong>{probe.title}</strong><small>{probe.company_name} · {probe.classification.replaceAll('_', ' ')}</small><p>{probe.classification_reason}</p></div>
              <a className="posting-link" href={probe.official_url ?? probe.discovery_url} target="_blank" rel="noreferrer">Open probe source ↗</a>
            </div>
          ))}
        </div>
      </section>
      <div className="split-grid">
        <section className="panel">
          <div className="panel-title"><h3>Source health</h3><span>{sources.length} enabled</span></div>
          {sources.length === 0 ? <p className="muted">No source state available.</p> : sources.map((source) => (
            <button className="source-row interactive-row" key={source.id} onClick={() => void onSource(source)}>
              <div><strong>{source.display_name}</strong><small>{source.source_family} · {source.health === 'HEALTHY' && source.last_success_at ? `healthy ${relativeTime(source.last_success_at)}` : source.last_success_at ? `last success ${relativeTime(source.last_success_at)}` : 'awaiting first success'}</small>{source.last_error && <small className="source-error">{source.last_error}</small>}</div>
              <div className="role-actions"><span className={`health ${source.health.toLowerCase()}`}>{source.health}</span><span className="inspect">Inspect source →</span></div>
            </button>
          ))}
        </section>
        <section className="panel">
          <div className="panel-title"><h3>Screening outcomes</h3><span>last 24h</span></div>
          <StatRow label="Clear no, retained but hidden" value={summary.clear_no} onClick={() => void onDrill('clear_no', 'Clear-no audit set', 'High-confidence exclusions from the last 24 hours, retained with reason and evidence.')} />
          <StatRow label="Possible / gray zone" value={Math.max(summary.possible_fit, grayZoneCount)} onClick={() => void onDrill('gray', 'Possible / gray-zone roles', 'Ambiguous roles retained for follow-up rather than silently discarded.')} />
          <StatRow label="Relevant and surfaced" value={summary.relevant} onClick={() => void onDrill('relevant', 'Relevant surfaced roles', 'Roles surfaced by relevance screening in the last 24 hours.')} />
          <StatRow label="Needs data" value={summary.needs_data} onClick={() => void onDrill('needs_data', 'Needs-data roles', 'Roles whose current priority is blocked on material missing evidence.')} />
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

function CompanyList({ companies, onOpen, onCompany }: { companies: CompanyView[]; onOpen: (role: Opportunity) => void; onCompany: (company: CompanyView) => void }) {
  return <><div className="eyebrow">AGGREGATION LENS</div><h2>Companies</h2><p className="muted">Reusable company intelligence and surfaced mandates stay together without turning the product into a CRM.</p><div className="company-grid">{companies.length === 0 ? <section className="panel"><p className="muted">No surfaced company opportunities yet.</p></section> : companies.map((company) => {
    const trajectory = company.trajectory
    return <section className="panel company-card" key={company.id}>
      <div className="panel-title"><h3>{company.name}</h3><button className="inspect-link" onClick={() => void onCompany(company)}>{company.opportunities.length} relevant role{company.opportunities.length === 1 ? '' : 's'} · Inspect company →</button></div>
      {trajectory ? <div className="company-intelligence">
        <div className="intel-head"><strong>{payloadText(trajectory, 'current_health') ?? 'Current health not established.'}</strong><Confidence value={trajectory.confidence} /></div>
        <p>{payloadText(trajectory, 'why_now_for_role') ?? payloadList(trajectory, 'biggest_pain_points')[0] ?? 'No company-level why-now conclusion yet.'}</p>
        <IntelligenceSources sources={trajectory.evidence ?? []} />
      </div> : <p className="muted">Company-level trajectory is not established yet.</p>}
      <div className="company-opportunities"><span>Surfaced mandates</span><OpportunityRows opportunities={company.opportunities} onOpen={onOpen} /></div>
    </section>
  })}</div></>
}

function PipelineStatus({ pipeline, onDrill }: { pipeline: PipelineHealth; onDrill: (kind: string, title: string, description: string) => void }) {
  const status = pipeline.degraded ? 'DEGRADED · PROCESSING INCOMPLETE' : 'PROCESSING CURRENT'
  return <section className={`panel pipeline-status ${pipeline.degraded ? 'degraded' : ''}`}>
    <div className="panel-title"><h3>Pipeline assurance</h3><span>{status}</span></div>
    <p className="muted">Recommendation totals cover processed records only. Backlog is shown separately and never interpreted as a negative recommendation.</p>
    <div className="pipeline-grid">
      <button className="interactive-card" onClick={() => void onDrill('awaiting_triage', 'Awaiting mandate triage', 'Active canonical roles whose persisted screening_stage is ELIGIBLE; no relevance outcome exists yet.')}><strong>{pipeline.awaiting_triage}</strong><span>Awaiting triage</span><small>{pipeline.oldest_awaiting_triage ? `oldest ${relativeTime(pipeline.oldest_awaiting_triage)}` : 'none pending'} · Inspect →</small></button>
      <button className="interactive-card" onClick={() => void onDrill('awaiting_qualification', 'Awaiting deep qualification', 'Active roles whose persisted screening_stage is TRIAGE_RELEVANT; no priority outcome exists yet.')}><strong>{pipeline.awaiting_qualification}</strong><span>Awaiting qualification</span><small>{pipeline.oldest_awaiting_qualification ? `oldest ${relativeTime(pipeline.oldest_awaiting_qualification)}` : 'none pending'} · Inspect →</small></button>
      <div><strong>{pipeline.stale_running}</strong><span>Stale running work</span><small>worker timeout + 5m</small></div>
      <div><strong>{pipeline.recent_throttles}</strong><span>Provider throttles</span><small>last 24h</small></div>
    </div>
    <div className="freshness-line"><span>Discovery {timeOrNever(pipeline.last_discovery_success)}</span><span>Triage {timeOrNever(pipeline.last_triage_success)}</span><span>Qualification {timeOrNever(pipeline.last_qualification_success)}</span></div>
  </section>
}

function opportunityState(role: Opportunity): { label: string; className: string } {
  if (role.priority_class) return { label: role.priority_class.replaceAll('_', ' '), className: role.priority_class.toLowerCase() }
  if (role.screening_stage === 'ELIGIBLE') return { label: 'AWAITING TRIAGE', className: 'pending' }
  if (role.screening_stage === 'TRIAGE_RELEVANT') return { label: 'AWAITING QUALIFICATION', className: 'pending' }
  if (role.screening_stage === 'TRIAGE_POSSIBLE') return { label: 'AMBIGUOUS · HELD', className: 'pending' }
  if (role.screening_stage === 'TRIAGE_CLEAR_NO') return { label: 'CLEAR NO', className: 'reject' }
  return { label: 'UNPROCESSED', className: 'pending' }
}

function timeOrNever(value: string | null) { return value ? relativeTime(value) : 'no recorded success' }

function OpportunityRows({ opportunities, onOpen }: { opportunities: Opportunity[]; onOpen: (role: Opportunity) => void }) {
  if (opportunities.length === 0) return <p className="muted">No roles match this exact persisted-state query.</p>
  return <div>{opportunities.map((role) => (
    <div className="opportunity-row" key={role.id}>
      <button className="opportunity-main" onClick={() => onOpen(role)}>
        <div className="role-title">{role.title}</div>
        <div className="role-meta">{role.company?.display_name ?? 'Company pending'}{role.location ? ` · ${role.location}` : ''}</div>
        {role.current_reason_text && <div className="reason">{role.current_reason_text}</div>}
      </button>
      <div className="role-actions"><span className={`priority ${opportunityState(role).className}`}>{opportunityState(role).label}</span>{postingUrl(role) ? <a className="posting-link" href={postingUrl(role)} target="_blank" rel="noreferrer">Open posting ↗</a> : <span className="source-unavailable">Source URL unavailable</span>}<button className="inspect-link" onClick={() => onOpen(role)}>Decision glass →</button></div>
    </div>
  ))}</div>
}

function DrawerShell({ title, eyebrow, onClose, children }: { title: string; eyebrow: string; onClose: () => void; children: React.ReactNode }) {
  const titleId = useId()
  const closeRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    const previousFocus = document.activeElement as HTMLElement | null
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose() }
    window.addEventListener('keydown', closeOnEscape)
    closeRef.current?.focus()
    return () => {
      window.removeEventListener('keydown', closeOnEscape)
      previousFocus?.focus()
    }
  }, [onClose])
  return <div className="drawer-backdrop" onMouseDown={onClose}><section className="decision-drawer" role="dialog" aria-modal="true" aria-labelledby={titleId} onMouseDown={(event) => event.stopPropagation()}><div className="drawer-head"><div><div className="eyebrow">{eyebrow}</div><h2 id={titleId}>{title}</h2></div><button ref={closeRef} className="close" aria-label={`Close ${title}`} onClick={onClose}>×</button></div>{children}</section></div>
}

function ErrorDrawer({ message, onClose }: { message: string; onClose: () => void }) {
  return <DrawerShell title="Drill-down unavailable" eyebrow="QUERY FAILURE" onClose={onClose}><div className="error-banner" role="alert">{message}</div></DrawerShell>
}

function OpportunitySetDrawer({ detail, onOpen, onClose }: { detail: OpportunitySetDetail; onOpen: (role: Opportunity) => void; onClose: () => void }) {
  return <DrawerShell title={detail.title} eyebrow="UNDERLYING ROLE SET" onClose={onClose}><p className="muted">{detail.description}</p><div className="result-count">{detail.opportunities.length} role{detail.opportunities.length === 1 ? '' : 's'} loaded</div><section className="detail-block"><OpportunityRows opportunities={detail.opportunities} onOpen={onOpen} /></section></DrawerShell>
}

function SourceDrawer({ detail, onOpen, onClose }: { detail: SourceDetail; onOpen: (role: Opportunity) => void; onClose: () => void }) {
  const { source, runs, records, recordCount, opportunities } = detail
  return <DrawerShell title={source.display_name} eyebrow="SOURCE OPERATIONS" onClose={onClose}>
    <div className="decision-verdict"><span>{source.health}</span><strong>{source.source_family} source</strong></div>
    <div className="trace-grid">
      <Trace label="Last sync" value={source.last_sync_at ? `${relativeTime(source.last_sync_at)} · ${formatDate(source.last_sync_at)}` : 'Never'} />
      <Trace label="Last success" value={source.last_success_at ? `${relativeTime(source.last_success_at)} · ${formatDate(source.last_success_at)}` : 'Never'} />
      <Trace label="Canonical source records" value={String(recordCount)} />
      <Trace label="Recent linked roles" value={String(opportunities.length)} />
    </div>
    {source.last_error && <div className="error-banner" role="alert">Latest source error: {source.last_error}</div>}
    <DetailBlock title="Recent ingestion runs">{runs.length ? <div className="run-list">{runs.map((run) => <div className="run-row" key={run.id}><div><strong>{run.status}</strong><small>{formatDate(run.started_at)}{run.finished_at ? ` → ${formatDate(run.finished_at)}` : ' · still running'}</small></div><div className="run-counts"><span>{run.discovered_count} discovered</span><span>{run.new_count} new</span><span>{run.changed_count} changed</span><span>{run.duplicate_count} duplicate</span><span>{run.closed_count} closed</span><span>{run.error_count} errors</span></div>{run.error_text && <p className="source-error">{run.error_text}</p>}</div>)}</div> : <p className="muted">No ingestion runs recorded.</p>}</DetailBlock>
    <DetailBlock title="Recent source records">{records.length ? <div>{records.map((record) => <div className="evidence-row" key={record.id}><div><strong>{record.external_id}</strong><small>{record.state} · seen {relativeTime(record.last_seen_at)}</small></div>{record.canonical_url ? <a href={record.canonical_url} target="_blank" rel="noreferrer">Open source ↗</a> : <span className="source-unavailable">Source URL unavailable</span>}</div>)}</div> : <p className="muted">No source records available.</p>}</DetailBlock>
    <DetailBlock title="Linked canonical roles"><OpportunityRows opportunities={opportunities} onOpen={onOpen} /></DetailBlock>
  </DrawerShell>
}

function CompanyDrawer({ detail, onOpen, onClose }: { detail: CompanyDetail; onOpen: (role: Opportunity) => void; onClose: () => void }) {
  const { company, intelligence } = detail
  const trajectory = intelligence.find((record) => record.capability === 'COMPANY_TRAJECTORY') ?? company.trajectory
  const stakeholders = intelligence.flatMap(payloadStakeholders)
  return <DrawerShell title={company.name} eyebrow="COMPANY AGGREGATION" onClose={onClose}>
    <p className="muted">Reusable intelligence, stakeholders, surfaced mandates, and opportunity history for this company.</p>
    {trajectory ? <DetailBlock title="Trajectory"><div className="intel-head"><strong>{payloadText(trajectory, 'current_health') ?? 'Current health not established.'}</strong><Confidence value={trajectory.confidence} /></div><p>{payloadText(trajectory, 'why_now_for_role') ?? 'Why-now conclusion not established.'}</p><InlineLists leftTitle="Strategic priorities" left={payloadList(trajectory, 'strategic_priorities')} rightTitle="Operating pressures" right={payloadList(trajectory, 'biggest_pain_points')} /><IntelligenceSources sources={trajectory.evidence ?? []} /><TraceLine record={trajectory} /></DetailBlock> : <p className="muted">Company trajectory has not been established.</p>}
    <DetailBlock title="Stakeholders">{stakeholders.length ? stakeholders.map((person, index) => <div className="stakeholder-row" key={`${person.identity}-${index}`}><div><strong>{person.identity ?? 'Unknown person'}</strong><small>{person.title ?? 'Title unknown'} · {person.role_in_decision ?? 'role unknown'}</small></div><Verification value={person.verification_status ?? 'UNKNOWN'} /></div>) : <p className="muted">No defensible stakeholder identities established yet.</p>}</DetailBlock>
    <DetailBlock title="Surfaced opportunities"><OpportunityRows opportunities={company.opportunities} onOpen={onOpen} /></DetailBlock>
    <DetailBlock title="Opportunity history">{company.opportunities.map((role) => <button className="history-row interactive-row" key={role.id} onClick={() => onOpen(role)}><span><strong>{role.title}</strong><small>First seen {formatDate(role.first_seen_at)} · {role.screening_stage.replaceAll('_', ' ')}</small></span><small>Decision glass →</small></button>)}</DetailBlock>
    {intelligence.length > 0 && <DetailBlock title="Reusable intelligence traces"><div className="intelligence-traces">{intelligence.map((record) => <div key={record.id}><strong>{record.capability.replaceAll('_', ' ')}</strong><small>{record.model_id ?? 'Deterministic'} · {record.reasoning_effort ?? 'n/a'} · {record.policy_version} · {record.capability_version}</small></div>)}</div></DetailBlock>}
  </DrawerShell>
}

function ActivitySetDrawer({ events, onOpen, onClose }: { events: Activity[]; onOpen: (event: Activity) => void; onClose: () => void }) {
  return <DrawerShell title="Needs Me" eyebrow="ACTION-REQUIRED ACTIVITY" onClose={onClose}>{events.length ? events.map((event) => <ActivityItem event={event} onOpen={onOpen} key={event.id} />) : <p className="muted">No action-required events are currently in the activity window.</p>}</DrawerShell>
}

function ActivityDrawer({ event, onClose }: { event: Activity; onClose: () => void }) {
  const details = Object.entries(event.details ?? {})
  return <DrawerShell title={event.message} eyebrow="ACTION CONTEXT" onClose={onClose}><div className="decision-verdict"><span>{event.severity.replaceAll('_', ' ')}</span><strong>{event.entity_type ? `${event.entity_type} · ${event.entity_id ?? 'reference unavailable'}` : 'No linked entity'}</strong></div><DetailBlock title="Blocking reason and recorded context">{details.length ? <div className="trace-grid">{details.map(([key, value]) => <Trace key={key} label={key.replaceAll('_', ' ')} value={formatValue(value)} />)}</div> : <p className="muted">No additional action context was persisted for this event.</p>}</DetailBlock><small className="muted">Recorded {formatDate(event.created_at)}</small></DrawerShell>
}

function TraceLine({ record }: { record: IntelligenceRecord }) { return <div className="trace-line">{record.model_id ?? 'Deterministic'} · {record.reasoning_effort ?? 'n/a'} · policy {record.policy_version} · capability {record.capability_version} · trace {record.trace_id?.slice(0, 12) ?? 'n/a'}</div> }

function DecisionDrawer({ detail, onClose }: { detail: OpportunityDetail; onClose: () => void }) {
  const closeRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    const previousFocus = document.activeElement as HTMLElement | null
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', closeOnEscape)
    closeRef.current?.focus()
    return () => {
      window.removeEventListener('keydown', closeOnEscape)
      previousFocus?.focus()
    }
  }, [onClose])

  const { opportunity, decision, decisionHistory, modelRun, intelligence } = detail
  const evidence = decision?.evidence ?? {}
  const sources = evidence.sources ?? []
  const intel = new Map(latestByCapability(intelligence.filter((record) => record.status === 'COMPLETED')).map((record) => [record.capability, record]))
  const core = intel.get('CORE_X')
  const native = intel.get('NATIVE_CANDIDATE')
  const pressure = intel.get('COMMERCIAL_PRESSURE')
  const twoNotch = intel.get('TWO_NOTCH_UP')
  const stakeholders = intel.get('STAKEHOLDER_CONTEXT')
  const trajectory = intel.get('COMPANY_TRAJECTORY')

  return (
    <div className="drawer-backdrop" onMouseDown={onClose}>
      <section className="decision-drawer" role="dialog" aria-modal="true" aria-labelledby="decision-title" onMouseDown={(e) => e.stopPropagation()}>
        <div className="drawer-head"><div><div className="eyebrow">DECISION GLASS</div><h2 id="decision-title">{opportunity.title}</h2><p className="muted">{opportunity.company?.display_name}{opportunity.location ? ` · ${opportunity.location}` : ''}</p>{postingUrl(opportunity) ? <a className="posting-link primary-posting" href={postingUrl(opportunity)} target="_blank" rel="noreferrer">Open canonical posting ↗</a> : <span className="source-unavailable">Source URL unavailable</span>}</div><button ref={closeRef} className="close" aria-label="Close decision details" onClick={onClose}>×</button></div>

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

        <DetailBlock title="Changed / stale state">
          <div className="trace-grid">
            <Trace label="Current role state" value={opportunity.screening_stage.replaceAll('_', ' ')} />
            <Trace label="First seen" value={formatDate(opportunity.first_seen_at)} />
            <Trace label="Decision versions" value={String(decisionHistory.length)} />
            <Trace label="Supersedes" value={decision?.supersedes_id?.slice(0, 12) ?? 'No prior decision linked'} />
          </div>
          {decisionHistory.length > 1 && <div className="history-list">{decisionHistory.map((version) => <div className="trace-line" key={version.id}>{formatDate(version.created_at)} · {version.stage.replaceAll('_', ' ')} · {version.outcome.replaceAll('_', ' ')} · {version.policy_version ?? 'policy unknown'}</div>)}</div>}
        </DetailBlock>

        {intelligence.length > 0 && <DetailBlock title="Intelligence traces">
          <div className="intelligence-traces">{intelligence.map((record) => (
            <div key={record.id}><strong>{record.capability.replaceAll('_', ' ')} · {record.status.replaceAll('_', ' ')}</strong><small>{formatDate(record.updated_at)} · {record.model_id ?? 'Deterministic'} · {record.reasoning_effort ?? 'n/a'} · {record.capability_version} · policy {record.policy_version} · trace {record.trace_id?.slice(0, 10) ?? 'n/a'}{record.supersedes_id ? ` · supersedes ${record.supersedes_id.slice(0, 10)}` : ''}</small></div>
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
  return [...records]
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

function ActivityRail({ activity, onOpen }: { activity: Activity[]; onOpen: (event: Activity) => void }) {
  const needsMe = activity.filter((event) => event.severity === 'ACTION_REQUIRED')
  const operational = activity.filter((event) => event.severity !== 'ACTION_REQUIRED')
  return <aside aria-label="Activity and Needs Me">
    <div className="panel-title"><h3>Activity / Needs Me</h3><span>{needsMe.length ? `${needsMe.length} action required` : 'system healthy'}</span></div>
    {needsMe.length > 0 && <section className="needs-me-list"><div className="eyebrow">NEEDS ME</div>{needsMe.map((event) => <ActivityItem event={event} onOpen={onOpen} key={event.id} />)}</section>}
    {operational.length === 0 && needsMe.length === 0 ? <p className="muted">Waiting for first autonomous run.</p> : operational.map((event) => <ActivityItem event={event} onOpen={onOpen} key={event.id} />)}
  </aside>
}

function ActivityItem({ event, onOpen }: { event: Activity; onOpen: (event: Activity) => void }) {
  const prominent = ['ATTENTION', 'ACTION_REQUIRED', 'ERROR'].includes(event.severity)
  const interactive = Boolean(event.entity_type && event.entity_id) || event.severity === 'ACTION_REQUIRED'
  const content = <><span className={`activity-mark ${event.severity.toLowerCase()}`} /><div><strong>{event.message}</strong><small>{relativeTime(event.created_at)} · {event.severity.replace('_', ' ')}{interactive ? ' · Inspect →' : ''}</small></div></>
  return interactive ? <button className={`activity-item activity-button ${prominent ? 'prominent' : ''}`} onClick={() => void onOpen(event)}>{content}</button> : <div className={`activity-item ${prominent ? 'prominent' : ''}`}>{content}</div>
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

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function formatValue(value: unknown): string {
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (value === null || value === undefined) return 'Not recorded'
  return JSON.stringify(value)
}

function postingUrl(opportunity: Opportunity): string | undefined {
  const sources = opportunity.opportunity_sources ?? []
  return sources.find((link) => link.is_primary && link.source_record?.canonical_url)?.source_record?.canonical_url
    ?? sources.find((link) => link.source_record?.canonical_url)?.source_record?.canonical_url
}

function Metric({ label, value, onClick }: { label: string; value: number; onClick: () => void }) { return <button className="metric interactive-card" onClick={onClick}><span>{label} · Inspect →</span><strong>{value}</strong></button> }
function StatRow({ label, value, onClick }: { label: string; value: number; onClick: () => void }) { return <button className="stat-row interactive-row" onClick={onClick}><span>{label}</span><span className="stat-action"><strong>{value}</strong><small>Inspect →</small></span></button> }

export default App
