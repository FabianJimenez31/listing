import { useState } from 'react'
import '../../styles/tour.css'

const DEG = Math.PI / 180
// Banda de piso estilo Matterport: las flechas de navegacion viven cerca del
// horizonte inferior de la esfera, no a media pared (FR-304).
const FLOOR_PITCH_LOW = -85 * DEG
const FLOOR_PITCH_HIGH = -60 * DEG
// Separacion minima entre hotspots: debe superar el umbral de desvanecido
// del visor (linkOverlapAngle = 22.5) para que nunca se tapen entre si.
const MIN_YAW_SEPARATION = 25 * DEG
const MIN_PITCH_SEPARATION = 15 * DEG

function yawDelta(a, b) {
  return Math.abs(Math.atan2(Math.sin(a - b), Math.cos(a - b)))
}

const clampFloorPitch = (pitch) => Math.min(FLOOR_PITCH_HIGH, Math.max(FLOOR_PITCH_LOW, pitch))

export default function TourHotspotPicker({ scene, scenes, onSave, onClose }) {
  const [hotspots, setHotspots] = useState(scene.hotspots || [])
  const [warning, setWarning] = useState('')
  const targets = scenes.filter((item) => item.id !== scene.id && item.state === 'ready')
  const [targetId, setTargetId] = useState(targets[0]?.id || '')

  const addAt = (event) => {
    if (!targetId) return
    const rect = event.currentTarget.getBoundingClientRect()
    const x = (event.clientX - rect.left) / rect.width
    const y = (event.clientY - rect.top) / rect.height
    const hfov = (scene.hfov_deg || 360) * DEG
    const vfov = (scene.vfov_deg || 180) * DEG
    const target = targets.find((item) => item.id === targetId)
    // El yaw respeta el clic; el pitch se ajusta a la banda de piso (FR-304).
    const yaw = (x - 0.5) * hfov
    const pitch = clampFloorPitch((0.5 - y) * vfov)
    // Rechaza puntos demasiado cerca de un hotspot existente (FR-305).
    const crowded = hotspots.find((spot) =>
      yawDelta(spot.yaw, yaw) < MIN_YAW_SEPARATION && Math.abs(spot.pitch - pitch) < MIN_PITCH_SEPARATION)
    if (crowded) {
      setWarning('Demasiado cerca de otro hotspot: sepáralo al menos 25° a la izquierda o derecha.')
      return
    }
    setWarning('')
    setHotspots((items) => [...items, {
      to_scene_id: targetId,
      yaw,
      pitch,
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
        <span>Selecciona un destino y haz clic sobre el piso de la panorámica.</span>
      </div>
      <div
        className="hotspot-canvas"
        style={{ aspectRatio: `${scene.width || 2} / ${scene.height || 1}` }}
        onClick={addAt}
        role="presentation"
      >
        <img src={scene.pano_url} alt={scene.title} />
        {hotspots.map((spot, index) => {
          const hfov = (scene.hfov_deg || 360) * Math.PI / 180
          const vfov = (scene.vfov_deg || 180) * Math.PI / 180
          // WYSIWYG: mismo yaw envuelto y misma banda de piso que el visor.
          const yaw = Math.atan2(Math.sin(spot.yaw), Math.cos(spot.yaw))
          const pitch = clampFloorPitch(spot.pitch)
          return (
            <button
              type="button"
              key={`${spot.to_scene_id}-${index}`}
              className="hotspot-dot"
              style={{ left: `${(yaw / hfov + 0.5) * 100}%`, top: `${(0.5 - pitch / vfov) * 100}%` }}
              title={`Ir a ${spot.label || 'el ambiente'} — clic para quitar`}
              onClick={(event) => { event.stopPropagation(); setHotspots((items) => items.filter((_, i) => i !== index)) }}
            >{index + 1}</button>
          )
        })}
      </div>
      {warning && <p className="hotspot-warning" role="alert">{warning}</p>}
      <div className="hotspot-actions">
        <button type="button" className="btn btn-outline btn-sm" onClick={onClose}>Cancelar</button>
        <button type="button" className="btn btn-blue btn-sm" onClick={() => onSave(hotspots)}>Guardar hotspots</button>
      </div>
    </div>
  )
}
