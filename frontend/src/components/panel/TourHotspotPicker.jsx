import { useState } from 'react'
import '../../styles/tour.css'

export default function TourHotspotPicker({ scene, scenes, onSave, onClose }) {
  const [hotspots, setHotspots] = useState(scene.hotspots || [])
  const targets = scenes.filter((item) => item.id !== scene.id && item.state === 'ready')
  const [targetId, setTargetId] = useState(targets[0]?.id || '')

  const addAt = (event) => {
    if (!targetId) return
    const rect = event.currentTarget.getBoundingClientRect()
    const x = (event.clientX - rect.left) / rect.width
    const y = (event.clientY - rect.top) / rect.height
    const hfov = (scene.hfov_deg || 360) * Math.PI / 180
    const vfov = (scene.vfov_deg || 180) * Math.PI / 180
    const target = targets.find((item) => item.id === targetId)
    setHotspots((items) => [...items, {
      to_scene_id: targetId,
      yaw: (x - 0.5) * hfov,
      pitch: (0.5 - y) * vfov,
      label: target?.title || 'Ir al ambiente',
    }])
  }

  return (
    <div className="hotspot-editor">
      <div className="hotspot-toolbar">
        <label>Destino
          <select value={targetId} onChange={(e) => setTargetId(e.target.value)}>
            {targets.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
          </select>
        </label>
        <span>Selecciona un destino y haz clic en la panorámica.</span>
      </div>
      <div className="hotspot-canvas" onClick={addAt} role="presentation">
        <img src={scene.pano_url} alt={scene.title} />
        {hotspots.map((spot, index) => {
          const hfov = (scene.hfov_deg || 360) * Math.PI / 180
          const vfov = (scene.vfov_deg || 180) * Math.PI / 180
          return (
            <button
              type="button"
              key={`${spot.to_scene_id}-${index}`}
              className="hotspot-dot"
              style={{ left: `${(spot.yaw / hfov + 0.5) * 100}%`, top: `${(0.5 - spot.pitch / vfov) * 100}%` }}
              title="Quitar hotspot"
              onClick={(event) => { event.stopPropagation(); setHotspots((items) => items.filter((_, i) => i !== index)) }}
            >{index + 1}</button>
          )
        })}
      </div>
      <div className="hotspot-actions">
        <button type="button" className="btn btn-outline btn-sm" onClick={onClose}>Cancelar</button>
        <button type="button" className="btn btn-blue btn-sm" onClick={() => onSave(hotspots)}>Guardar hotspots</button>
      </div>
    </div>
  )
}
