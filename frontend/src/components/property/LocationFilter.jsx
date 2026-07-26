import { useEffect, useMemo } from 'react'
import { getLocations } from '../../api/catalog'

/**
 * Dependent Ciudad → Localidad → Barrio selector. The whole hierarchy (a few
 * hundred nodes) is fetched once and walked in memory, so the component is fully
 * controlled by a single `value` (the slug of the deepest chosen node) and is
 * round-trippable from the URL. The backend `location` filter matches that slug
 * AND its entire subtree, so picking a city surfaces listings tagged to its
 * localities/barrios too.
 */
export default function LocationFilter({ value = '', onChange, all, setAll }) {
  useEffect(() => {
    if (all.length) return
    getLocations().then((d) => setAll(d || [])).catch(() => setAll([]))
  }, [all.length, setAll])

  const active = useMemo(() => all.filter((l) => l.is_active !== false), [all])
  const bySlug = useMemo(() => Object.fromEntries(active.map((l) => [l.slug, l])), [active])
  const byId = useMemo(() => Object.fromEntries(active.map((l) => [l.id, l])), [active])
  const childrenOf = useMemo(() => {
    const m = {}
    for (const l of active) (m[l.parent_id] ||= []).push(l)
    for (const k in m) m[k].sort((a, b) => a.name.localeCompare(b.name, 'es'))
    return m
  }, [active])
  const cities = useMemo(
    () => active.filter((l) => l.level === 'city').sort((a, b) => a.name.localeCompare(b.name, 'es')),
    [active],
  )

  // Resolve the selected slug back into its city / locality / barrio ancestors.
  const chain = []
  let node = value ? bySlug[value] : null
  while (node) {
    chain.unshift(node)
    node = node.parent_id ? byId[node.parent_id] : null
  }
  const cityId = chain.find((n) => n.level === 'city')?.id || ''
  const localityId = chain.find((n) => n.level === 'locality')?.id || ''
  const neighborhoodId = chain.find((n) => n.level === 'neighborhood')?.id || ''

  const emit = (id) => onChange(id && byId[id] ? byId[id].slug : '')

  const localities = cityId ? childrenOf[cityId] || [] : []
  const barrios = localityId ? childrenOf[localityId] || [] : []

  return (
    <>
      <div className="fld">
        <label>Ciudad</label>
        <select value={cityId} onChange={(e) => emit(e.target.value)}>
          <option value="">Todas las ciudades</option>
          {cities.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>
      {cityId && localities.length > 0 && (
        <div className="fld">
          <label>Localidad / zona</label>
          <select value={localityId} onChange={(e) => emit(e.target.value || cityId)}>
            <option value="">Toda la ciudad</option>
            {localities.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
          </select>
        </div>
      )}
      {localityId && barrios.length > 0 && (
        <div className="fld">
          <label>Barrio</label>
          <select value={neighborhoodId} onChange={(e) => emit(e.target.value || localityId)}>
            <option value="">Toda la localidad</option>
            {barrios.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
        </div>
      )}
    </>
  )
}
