import { useEffect, useMemo, useState } from 'react'
import { createLocation, getLocations } from '../../api/catalog'
import { useAuth } from '../../contexts/AuthContext'
import PromptModal from '../ui/PromptModal'

// A nivel de módulo (no dentro del componente) para que su identidad sea estable
// entre renders y el select no se remonte al elegir una opción.
function LevelSelect({
  label, value, options, onPick, disabled = false,
  emptyLabel = '— Selecciona —', addLabel = null, onAdd,
  fieldClass, inputClass,
}) {
  return (
    <div className={fieldClass}>
      <label>{label}</label>
      <select className={inputClass} value={value} onChange={(e) => onPick(e.target.value)} disabled={disabled}>
        <option value="">{emptyLabel}</option>
        {options.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
      </select>
      {addLabel && (
        <button type="button" style={addBtnStyle} onClick={onAdd}>{addLabel}</button>
      )}
    </div>
  )
}

/**
 * Selector en cascada de la jerarquía de ubicaciones:
 * País → Departamento/Estado → Ciudad → Localidad/zona → Barrio.
 *
 * `value` es el id del nodo más profundo elegido (lo único que se persiste en
 * `location_id`). Quien tenga permiso `location:create` puede agregar cualquier
 * nivel que falte sin salir del formulario: el nodo nuevo se agrega a la lista
 * local y queda seleccionado, así que no se pierde nada de lo ya escrito.
 */
export default function LocationPicker({
  value = '',
  onChange,
  fieldClass = 'pf-field',
  inputClass = 'pf-input',
}) {
  const { hasPermission } = useAuth()
  const [locs, setLocs] = useState([])
  const [modal, setModal] = useState(null)

  useEffect(() => { getLocations().then((r) => setLocs(r || [])).catch(() => setLocs([])) }, [])

  const byId = useMemo(() => Object.fromEntries(locs.map((l) => [l.id, l])), [locs])

  // Sube por la cadena de padres hasta el nivel pedido (las ciudades cuelgan de
  // un departamento, así que no se puede comparar parent_id directamente).
  const ancestorOfLevel = (id, level) => {
    let node = byId[id]
    while (node) {
      if (node.level === level) return node.id
      node = node.parent_id ? byId[node.parent_id] : null
    }
    return ''
  }

  const sel = useMemo(() => ({
    country: ancestorOfLevel(value, 'country'),
    state: ancestorOfLevel(value, 'state'),
    city: ancestorOfLevel(value, 'city'),
    locality: ancestorOfLevel(value, 'locality'),
    neighborhood: ancestorOfLevel(value, 'neighborhood'),
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }), [value, byId])

  const sorted = (list) => [...list].sort((a, b) => a.name.localeCompare(b.name, 'es'))
  const atLevel = (level) => locs.filter((l) => l.level === level)

  const countryOpts = useMemo(() => sorted(atLevel('country')), [locs])
  const stateOpts = useMemo(
    () => (sel.country ? sorted(atLevel('state').filter((l) => ancestorOfLevel(l.id, 'country') === sel.country)) : []),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [locs, sel.country, byId],
  )
  const cityOpts = useMemo(() => {
    if (!sel.country) return []
    return sorted(atLevel('city').filter((l) => (
      ancestorOfLevel(l.id, 'country') === sel.country
      && (!sel.state || ancestorOfLevel(l.id, 'state') === sel.state)
    )))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locs, sel.country, sel.state, byId])
  const localityOpts = useMemo(
    () => (sel.city ? sorted(atLevel('locality').filter((l) => ancestorOfLevel(l.id, 'city') === sel.city)) : []),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [locs, sel.city, byId],
  )
  const barrioOpts = useMemo(
    () => (sel.locality ? sorted(atLevel('neighborhood').filter((l) => ancestorOfLevel(l.id, 'locality') === sel.locality)) : []),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [locs, sel.locality, byId],
  )

  const canAdd = hasPermission('location:create')

  const createChild = async (name, { level, parent }) => {
    const created = await createLocation({ name, level, parent_id: parent ? parent.id : null })
    setLocs((prev) => [...prev.filter((l) => l.id !== created.id), created])
    onChange(created.id)
  }

  const askFor = ({ level, parent, title, label, placeholder }) =>
    setModal({
      title,
      label,
      placeholder,
      onSubmit: (name) => createChild(name, { level, parent }),
    })

  const addCountry = () => askFor({
    level: 'country', parent: null,
    title: 'Agregar país', label: 'Nuevo país', placeholder: 'Ej: Panamá',
  })

  const addState = () => askFor({
    level: 'state', parent: byId[sel.country],
    title: 'Agregar departamento / estado',
    label: `Nuevo departamento o estado en ${byId[sel.country]?.name || ''}`,
    placeholder: 'Ej: Provincia de Panamá',
  })

  // La ciudad cuelga del departamento si hay uno elegido; si no, del país.
  const addCity = () => {
    const parent = byId[sel.state] || byId[sel.country]
    if (!parent) return
    askFor({
      level: 'city', parent,
      title: 'Agregar ciudad',
      label: `Nueva ciudad en ${parent.name}`,
      placeholder: 'Ej: Ciudad de Panamá',
    })
  }

  const addLocality = () => askFor({
    level: 'locality', parent: byId[sel.city],
    title: 'Agregar localidad / zona',
    label: `Nueva localidad en ${byId[sel.city]?.name || ''}`,
    placeholder: 'Nombre de la localidad o zona',
  })

  const addBarrio = () => askFor({
    level: 'neighborhood', parent: byId[sel.locality],
    title: 'Agregar barrio',
    label: `Nuevo barrio en ${byId[sel.locality]?.name || ''}`,
    placeholder: 'Nombre del barrio',
  })

  const shared = { fieldClass, inputClass }

  return (
    <>
      <LevelSelect
        {...shared}
        label="País"
        value={sel.country}
        options={countryOpts}
        onPick={(id) => onChange(id)}
        addLabel={canAdd ? '+ Agregar país que falta' : null}
        onAdd={addCountry}
      />
      <LevelSelect
        {...shared}
        label="Departamento / Estado"
        value={sel.state}
        options={stateOpts}
        disabled={!sel.country}
        emptyLabel={sel.country ? '— Todo el país —' : '— Selecciona —'}
        onPick={(id) => onChange(id || sel.country)}
        addLabel={canAdd && sel.country ? '+ Agregar departamento que falta' : null}
        onAdd={addState}
      />
      <LevelSelect
        {...shared}
        label="Ciudad"
        value={sel.city}
        options={cityOpts}
        disabled={!sel.country}
        onPick={(id) => onChange(id || sel.state || sel.country)}
        addLabel={canAdd && sel.country ? '+ Agregar ciudad que falta' : null}
        onAdd={addCity}
      />
      <LevelSelect
        {...shared}
        label="Localidad / zona"
        value={sel.locality}
        options={localityOpts}
        disabled={!sel.city}
        onPick={(id) => onChange(id || sel.city)}
        addLabel={canAdd && sel.city ? '+ Agregar localidad que falta' : null}
        onAdd={addLocality}
      />
      <LevelSelect
        {...shared}
        label="Barrio"
        value={sel.neighborhood}
        options={barrioOpts}
        disabled={!sel.locality}
        onPick={(id) => onChange(id || sel.locality)}
        addLabel={canAdd && sel.locality ? '+ Agregar barrio que falta' : null}
        onAdd={addBarrio}
      />
      {modal && <PromptModal {...modal} onClose={() => setModal(null)} />}
    </>
  )
}

const addBtnStyle = {
  marginTop: 6,
  alignSelf: 'flex-start',
  background: 'none',
  border: 'none',
  color: '#0251FD',
  fontSize: 13,
  fontWeight: 700,
  cursor: 'pointer',
  padding: '2px 0',
  textAlign: 'left',
}
