import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { searchProjects } from '../../api/projects'
import { searchProperties } from '../../api/properties'
import { formatPrice } from '../../lib/priceDisplay'
import { IconPin, IconSearch } from '../ui/icons'

const MIN_QUERY_LENGTH = 2

export default function SearchAutocomplete({ value, onChange, tab, kind, onSearch }) {
  const navigate = useNavigate()
  const focused = useRef(false)
  const resultsRef = useRef(null)
  const requestSequence = useRef(0)
  const [suggestions, setSuggestions] = useState([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)

  useEffect(() => {
    if (active < 0) return
    resultsRef.current
      ?.querySelector(`#hero-suggestion-${active}`)
      ?.scrollIntoView({ block: 'nearest' })
  }, [active])

  const query = value.trim()
  useEffect(() => {
    if (query.length < MIN_QUERY_LENGTH) return undefined
    const sequence = ++requestSequence.current
    const timer = setTimeout(() => {
      setLoading(true)
      const request = tab === 'projects'
        ? searchProjects({ q: query, page_size: 5 })
        : searchProperties({
            q: query,
            page_size: 5,
            ...(tab === 'sale' || tab === 'rent' ? { operation_type: tab } : {}),
            ...(tab === 'usa' ? { country: 'us' } : {}),
            ...(kind ? { property_kind: kind } : {}),
          })
      request
        .then((result) => {
          if (sequence !== requestSequence.current) return
          setSuggestions(result.data || [])
          setActive(-1)
          setOpen(focused.current)
        })
        .catch(() => {
          if (sequence === requestSequence.current) setSuggestions([])
        })
        .finally(() => {
          if (sequence === requestSequence.current) setLoading(false)
        })
    }, 220)
    return () => clearTimeout(timer)
  }, [query, tab, kind])

  const handleChange = (event) => {
    const next = event.target.value
    onChange(next)
    setActive(-1)
    setSuggestions([])
    setLoading(next.trim().length >= MIN_QUERY_LENGTH)
    setOpen(next.trim().length >= MIN_QUERY_LENGTH)
  }

  const hrefFor = (item) => tab === 'projects'
    ? `/proyectos/${item.slug}`
    : `/propiedades/${item.nid}`

  const choose = (item) => {
    setOpen(false)
    navigate(hrefFor(item))
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Escape') {
      setOpen(false)
      setActive(-1)
      return
    }
    if (!open || suggestions.length === 0) return
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActive((current) => (current + 1) % suggestions.length)
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActive((current) => (current <= 0 ? suggestions.length - 1 : current - 1))
    } else if (event.key === 'Enter' && active >= 0) {
      event.preventDefault()
      choose(suggestions[active])
    }
  }

  const runFullSearch = () => {
    setOpen(false)
    onSearch()
  }

  const isProject = tab === 'projects'
  const listId = 'hero-search-suggestions'

  return (
    <div
      className="search-suggest-wrap"
      onFocus={() => {
        focused.current = true
        if (query.length >= MIN_QUERY_LENGTH) setOpen(true)
      }}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) {
          focused.current = false
          setOpen(false)
        }
      }}
    >
      <div className="inputwrap">
        <IconSearch />
        <input
          type="search"
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Busca por ciudad, barrio, NID o palabra clave"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls={listId}
          aria-activedescendant={active >= 0 ? `hero-suggestion-${active}` : undefined}
          autoComplete="off"
        />
      </div>

      {open && (
        <div className="search-suggestions" id={listId} role="listbox">
          <div className="suggestion-results" ref={resultsRef}>
            {loading && <div className="suggestion-message">Buscando sugerencias…</div>}
            {!loading && suggestions.length === 0 && (
              <div className="suggestion-message">No encontramos coincidencias todavía.</div>
            )}
            {!loading && suggestions.map((item, index) => {
              const price = formatPrice(
                isProject ? item.price_from : item.price_amount,
                item.currency,
              )
              return (
                <button
                  type="button"
                  key={item.id}
                  id={`hero-suggestion-${index}`}
                  role="option"
                  aria-selected={active === index}
                  className={`search-suggestion ${active === index ? 'active' : ''}`}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => choose(item)}
                >
                  <span className="suggestion-main">
                    <strong>{item.title}</strong>
                    {item.location?.name && <small><IconPin /> {item.location.name}</small>}
                  </span>
                  <span className="suggestion-price">{isProject && price ? 'Desde ' : ''}{price || 'Consultar'}</span>
                </button>
              )
            })}
          </div>
          <button
            type="button"
            className="suggestion-all"
            onMouseDown={(event) => event.preventDefault()}
            onClick={runFullSearch}
          >
            <IconSearch /> Ver todos los resultados para “{query}”
          </button>
        </div>
      )}
    </div>
  )
}
