export type CompanyOpportunity = {
  company_id: string | null
  company: { display_name: string } | null
}

export type CompanyIntelligence = {
  company_id: string | null
  capability: string
}

export type CompanyGroup<T extends CompanyOpportunity, R extends CompanyIntelligence> = {
  id: string
  name: string
  opportunities: T[]
  trajectory: R | null
}

export function groupCompanies<T extends CompanyOpportunity, R extends CompanyIntelligence>(
  opportunities: T[],
  intelligence: R[],
): CompanyGroup<T, R>[] {
  const groups = new Map<string, CompanyGroup<T, R>>()
  const trajectoryByCompany = new Map<string, R>()

  for (const record of intelligence) {
    if (record.company_id && record.capability === 'COMPANY_TRAJECTORY' && !trajectoryByCompany.has(record.company_id)) {
      trajectoryByCompany.set(record.company_id, record)
    }
  }

  for (const opportunity of opportunities) {
    if (!opportunity.company_id) continue
    const current = groups.get(opportunity.company_id) ?? {
      id: opportunity.company_id,
      name: opportunity.company?.display_name ?? 'Unknown company',
      opportunities: [],
      trajectory: trajectoryByCompany.get(opportunity.company_id) ?? null,
    }
    current.opportunities.push(opportunity)
    groups.set(opportunity.company_id, current)
  }

  return [...groups.values()].sort(
    (a, b) => b.opportunities.length - a.opportunities.length || a.name.localeCompare(b.name),
  )
}
