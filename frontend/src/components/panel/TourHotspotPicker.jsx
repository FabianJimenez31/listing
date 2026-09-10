import { useState } from 'react'
import '../../styles/tour.css'

const DEG = Math.PI / 180
// Banda de piso estilo Matterport: las flechas de navegacion viven cerca del
// horizonte inferior de la esfera, no a media pared (FR-304).
const FLOOR_PITCH_LOW = -85 * DEG
const FLOOR_PITCH_HIGH = -60 * DEG
const clampFloorPitch = (pitch) => Math.min(FLOOR_PITCH_HIGH, Math.max(FLOOR_PITCH_LOW, pitch))

export default function TourHotspotPicker({ scene, targetScene, onSave, onClose }) {
  const existing = (scene.hotspots || []).find((spot) => spot.to_scene_id === targetScene.id)
  const [hotspot, setHotspot] = useState(existing || null)

  const addAt = (event) => {
    const rect = event.currentTarget.getBoundingClientRect()
    const x = (event.clientX - rect.left) / rect.width
    const y = (event.clientY - rect.top) / rect.height
    const hfov = (scene.hfov_deg || 360) * DEG
    const vfov = (scene.vfov_deg || 180) * DEG
    const yaw = (x - 0.5) * hfov
    const pitch = clampFloorPitch((0.5 - y) * vfov)
    setHotspot({
      to_scene_id: targetScene.id,
      yaw,
      pitch,
      label: targetScene.title,
    })
  }

  return (
    <div className="hotspot-editor">
      <div className="hotspot-editor-head">
        <div>
          <span className="tour-kicker">Ajuste opcional</span>
          <h4>Flecha de {scene.title} a {targetScene.title}</h4>
        </div>
        <button type="button" className="hotspot-close" onClick={onClose} aria-label="Cerrar">✕</button>
      </div>
      <div className="hotspot-toolbar">
        <span>La navegación ya está conectada. Haz clic sobre el piso para decidir dónde aparece la flecha.</span>
      </div>
      <div
        className="hotspot-canvas"
        style={{ aspectRatio: `${scene.width || 2} / ${scene.height || 1}` }}
        onClick={addAt}
        role="presentation"
      >
        <img src={scene.pano_url} alt={scene.title} />
        {hotspot && (() => {
          const hfov = (scene.hfov_deg || 360) * Math.PI / 180
          const vfov = (scene.vfov_deg || 180) * Math.PI / 180
          const yaw = Math.atan2(Math.sin(hotspot.yaw), Math.cos(hotspot.yaw))
          const pitch = clampFloorPitch(hotspot.pitch)
          return (
            <button
              type="button"
              className="hotspot-dot"
              style={{ left: `${(yaw / hfov + 0.5) * 100}%`, top: `${(0.5 - pitch / vfov) * 100}%` }}
              title={`Ir a ${targetScene.title}`}
              onClick={(event) => event.stopPropagation()}
            >→</button>
          )
        })()}
      </div>
      <p className="hotspot-tip">Puedes hacer clic nuevamente para moverla. Si usas la posición automática, aparecerá centrada.</p>
      <div className="hotspot-actions">
        <button type="button" className="btn btn-outline btn-sm" onClick={onClose}>Cancelar</button>
        <button type="button" className="btn btn-outline btn-sm" onClick={() => onSave([])}>Usar posición automática</button>
        <button type="button" className="btn btn-blue btn-sm" onClick={() => onSave(hotspot ? [hotspot] : [])}>Guardar dirección</button>
      </div>
    </div>
  )
}
