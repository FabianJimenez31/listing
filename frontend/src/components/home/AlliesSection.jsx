import { useEffect, useState } from 'react'
import { getPartners } from '../../api/partners'

export default function AlliesSection() {
  const [partners, setPartners] = useState([])

  useEffect(() => {
    getPartners().then((data) => setPartners(data || [])).catch(() => setPartners([]))
  }, [])

  if (partners.length === 0) return null

  return (
    <div className="allies">
      <div className="wrap">
        <div className="lbl">Inmobiliarias y constructoras aliadas</div>
        <div className="ally-row">
          {partners.map((p) => (
            <span className="ally" key={p.id}>{p.name}</span>
          ))}
        </div>
      </div>
    </div>
  )
}
